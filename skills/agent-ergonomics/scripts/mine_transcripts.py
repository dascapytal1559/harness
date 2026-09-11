#!/usr/bin/env python3
"""History instrument for agent-ergonomics.

Reads past Claude Code and Codex session transcripts for one target directory
and reports where agents already struggled: files re-read, searches repeated,
commands that failed, reads of files that no longer exist, hook errors.

Read-only. Never spends tokens. Counts are evidence, not verdicts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import sys
from collections import Counter, defaultdict
from pathlib import Path

HOME = Path.home()
CLAUDE_PROJECTS = HOME / ".claude" / "projects"
CODEX_SESSIONS = HOME / ".codex" / "sessions"
GROK_HOME = HOME / ".grok"

READ_CMDS = {"cat", "head", "tail", "sed", "less", "bat"}
SEARCH_CMDS = {"grep", "rg", "find", "fd", "ag"}


class Session:
    def __init__(self, store: str, sid: str):
        self.store = store
        self.sid = sid
        self.reads: Counter[str] = Counter()
        self.searches: Counter[str] = Counter()
        self.failures: Counter[str] = Counter()
        self.hook_errors = 0
        self.calls = 0


def parse_ts(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def norm_path(p: str, target: Path, cwd: str | None) -> str:
    """Return a path relative to target when it is inside it, else as given."""
    if not p:
        return p
    path = Path(p)
    if not path.is_absolute() and cwd:
        path = Path(cwd) / path
    try:
        return str(path.resolve().relative_to(target))
    except (ValueError, OSError):
        return str(path)


PATHISH = re.compile(r"^[~./A-Za-z0-9_@-][A-Za-z0-9_./@~+-]*$")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")


def command_lines(cmd: str):
    """Yield the command's lines with heredoc bodies removed."""
    terminator: str | None = None
    for line in cmd.splitlines():
        if terminator is not None:
            if line.strip() == terminator:
                terminator = None
            continue
        m = HEREDOC.search(line)
        if m:
            terminator = m.group(1)
        yield line


def classify_shell(cmd: str, target: Path, cwd: str | None, s: Session) -> None:
    """Record reads and searches implied by a shell command."""
    for line in command_lines(cmd):
        for segment in re.split(r"\s*(?:&&|\|\||;|\|)\s*", line):
            if ">" in segment or "<<" in segment:
                continue  # a write or a heredoc, not a read
            try:
                toks = shlex.split(segment)
            except ValueError:
                toks = segment.split()
            if not toks:
                continue
            head = os.path.basename(toks[0])
            if head in READ_CMDS:
                for t in toks[1:]:
                    if t.startswith("-") or not PATHISH.match(t):
                        continue
                    if "/" not in t and "." not in t:
                        continue
                    s.reads[norm_path(os.path.expanduser(t), target, cwd)] += 1
            elif head in SEARCH_CMDS:
                s.searches[" ".join(toks[:4])] += 1


def in_target(cwd: str | None, target: Path) -> bool:
    if not cwd:
        return False
    try:
        Path(cwd).resolve().relative_to(target)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- Claude ----

def claude_dirs(target: Path) -> list[Path]:
    if not CLAUDE_PROJECTS.is_dir():
        return []
    slug = str(target).replace("/", "-")
    return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir() and d.name.startswith(slug)]


def mine_claude(target: Path, since: dt.datetime | None) -> list[Session]:
    sessions: list[Session] = []
    for d in claude_dirs(target):
        for f in sorted(d.glob("*.jsonl")):
            s = Session("claude", f.stem)
            pending: dict[str, str] = {}
            keep = False
            with f.open(errors="ignore") as fh:
                for line in fh:
                    try:
                        o = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    cwd = o.get("cwd")
                    if cwd and not in_target(cwd, target):
                        continue
                    if cwd:
                        keep = True
                    ts = parse_ts(o.get("timestamp"))
                    if since and ts and ts < since:
                        continue
                    if o.get("type") == "attachment":
                        att = o.get("attachment") or {}
                        if "hook" in str(att.get("type", "")) and "error" in str(att.get("type", "")):
                            s.hook_errors += 1
                        continue
                    msg = o.get("message") or {}
                    content = msg.get("content")
                    if not isinstance(content, list):
                        continue
                    for c in content:
                        if not isinstance(c, dict):
                            continue
                        if c.get("type") == "tool_use":
                            s.calls += 1
                            name = c.get("name", "")
                            inp = c.get("input") or {}
                            label = name
                            if name == "Read":
                                p = norm_path(inp.get("file_path", ""), target, cwd)
                                s.reads[p] += 1
                                label = f"Read {p}"
                            elif name in ("Grep", "Glob"):
                                s.searches[f"{name} {inp.get('pattern', '')}"] += 1
                                label = f"{name} {inp.get('pattern', '')}"
                            elif name == "Bash":
                                cmd = inp.get("command", "") or ""
                                classify_shell(cmd, target, cwd, s)
                                label = "Bash " + cmd.strip().splitlines()[0][:70] if cmd.strip() else "Bash"
                            pending[c.get("id", "")] = label
                        elif c.get("type") == "tool_result":
                            label = pending.pop(c.get("tool_use_id", ""), "?")
                            body = c.get("content")
                            text = body if isinstance(body, str) else json.dumps(body)
                            failed = bool(c.get("is_error")) or bool(
                                re.match(r"Exit code [1-9]", text or "")
                            )
                            if failed:
                                s.failures[label] += 1
            if keep and s.calls:
                sessions.append(s)
    return sessions


# ----------------------------------------------------------------- Codex ----

def mine_codex(target: Path, since: dt.datetime | None) -> list[Session]:
    sessions: list[Session] = []
    if not CODEX_SESSIONS.is_dir():
        return sessions
    for f in sorted(CODEX_SESSIONS.rglob("rollout-*.jsonl")):
        s = Session("codex", f.stem)
        cwd: str | None = None
        pending: dict[str, str] = {}
        with f.open(errors="ignore") as fh:
            first = fh.readline()
            try:
                meta = json.loads(first)
            except json.JSONDecodeError:
                continue
            if meta.get("type") != "session_meta":
                continue
            cwd = (meta.get("payload") or {}).get("cwd")
            if not in_target(cwd, target):
                continue
            for line in fh:
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = parse_ts(o.get("timestamp"))
                if since and ts and ts < since:
                    continue
                p = o.get("payload") or {}
                kind = p.get("type")
                if kind == "function_call":
                    s.calls += 1
                    try:
                        args = json.loads(p.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    cmd = args.get("command")
                    if isinstance(cmd, list):
                        cmd = " ".join(cmd[2:]) if len(cmd) > 2 and cmd[1] == "-lc" else " ".join(cmd)
                    label = f"{p.get('name', '')} {str(cmd or '')[:70]}"
                    if cmd:
                        classify_shell(str(cmd), target, args.get("workdir") or cwd, s)
                    pending[p.get("call_id", "")] = label
                elif kind == "function_call_output":
                    label = pending.pop(p.get("call_id", ""), "?")
                    out = p.get("output") or ""
                    try:
                        parsed = json.loads(out)
                        code = (parsed.get("metadata") or {}).get("exit_code", parsed.get("exit_code"))
                    except (json.JSONDecodeError, AttributeError):
                        code = None
                    if isinstance(code, int) and code != 0:
                        s.failures[label] += 1
        if s.calls:
            sessions.append(s)
    return sessions


# ---------------------------------------------------------------- Report ----

def aggregate(sessions: list[Session], target: Path) -> dict:
    reads_total: Counter[str] = Counter()
    reads_sessions: Counter[str] = Counter()
    rereads_within: Counter[str] = Counter()
    search_sessions: Counter[str] = Counter()
    failures: Counter[str] = Counter()
    calls = 0
    hook_errors = 0
    for s in sessions:
        calls += s.calls
        hook_errors += s.hook_errors
        for p, n in s.reads.items():
            reads_total[p] += n
            reads_sessions[p] += 1
            if n >= 2:
                rereads_within[p] += 1
        for q in s.searches:
            search_sessions[q] += 1
        failures.update(s.failures)
    missing = {
        p: n for p, n in reads_total.items()
        if p and not p.startswith("/") and not (target / p).exists()
    }
    return {
        "sessions": Counter(s.store for s in sessions),
        "calls": calls,
        "failures_total": sum(failures.values()),
        "hook_errors": hook_errors,
        "reread_files": [
            {"path": p, "reads": reads_total[p], "sessions": reads_sessions[p],
             "sessions_rereading": rereads_within[p]}
            for p, _ in reads_total.most_common()
            if reads_sessions[p] >= 2 or rereads_within[p] >= 1
        ][:15],
        "repeated_searches": [
            {"search": q, "sessions": n} for q, n in search_sessions.most_common() if n >= 2
        ][:15],
        "failed_commands": [
            {"command": c, "count": n} for c, n in failures.most_common(15)
        ],
        "missing_files_read": [
            {"path": p, "reads": n} for p, n in sorted(missing.items(), key=lambda x: -x[1])
        ][:15],
    }


def render(target: Path, since: dt.datetime | None, stores: dict, agg: dict) -> str:
    out = [f"agent-ergonomics history for {target}"]
    out.append("stores: " + ", ".join(f"{k}: {v}" for k, v in stores.items()))
    out.append("window: " + (f"since {since.date()}" if since else "all time"))
    out.append(
        f"tool calls: {agg['calls']}   failures: {agg['failures_total']}   hook errors: {agg['hook_errors']}"
    )

    def section(title: str, rows: list[str]) -> None:
        out.append("")
        out.append(title)
        if rows:
            out.extend(f"  {r}" for r in rows)
        else:
            out.append("  none")

    section("re-read files (reads / sessions / sessions re-reading within one session):", [
        f"{r['path']}  {r['reads']} / {r['sessions']} / {r['sessions_rereading']}"
        for r in agg["reread_files"]
    ])
    section("searches repeated across sessions:", [
        f"{r['search']}  {r['sessions']} sessions" for r in agg["repeated_searches"]
    ])
    section("failed commands:", [
        f"{r['command']}  x{r['count']}" for r in agg["failed_commands"]
    ])
    section("reads of files that no longer exist:", [
        f"{r['path']}  {r['reads']} reads" for r in agg["missing_files_read"]
    ])
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default=os.getcwd(), help="directory under review (default: cwd)")
    ap.add_argument("--since", help="ISO date; only count events on or after it")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    target = Path(a.target).resolve()
    if not target.is_dir():
        print(f"target is not a directory: {target}", file=sys.stderr)
        return 2
    since = parse_ts(a.since) if a.since else None
    if a.since and since is None:
        print(f"could not parse --since {a.since!r}; use ISO 8601", file=sys.stderr)
        return 2
    if since and since.tzinfo is None:
        since = since.replace(tzinfo=dt.timezone.utc)

    claude = mine_claude(target, since)
    codex = mine_codex(target, since)
    stores = {
        "claude": f"{len(claude)} sessions" if CLAUDE_PROJECTS.is_dir() else "store not found",
        "codex": f"{len(codex)} sessions" if CODEX_SESSIONS.is_dir() else "store not found",
        "grok": "present, format unsupported" if GROK_HOME.is_dir() else "store not found",
    }
    agg = aggregate(claude + codex, target)

    if a.json:
        print(json.dumps({"target": str(target), "since": a.since, "stores": stores, **agg}, indent=2))
    else:
        print(render(target, since, stores, agg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
