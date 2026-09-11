#!/usr/bin/env python3
"""Dispatch one council round to every model family installed on this host.

Round 1 is independent: each voice sees only the immutable packet. Later rounds
are rebuttal rounds: each voice also sees the judge's brief (draft canonical
answer plus enumerated disagreements) and must defend, revise, or concede.
The active session is the judge, not a voice, so no provider is excluded.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


PROVIDERS = ("codex", "claude", "grok")
CANONICAL_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")
PROVIDER_EFFORTS = {
    "claude": ("low", "medium", "high", "xhigh", "max"),
    "codex": ("minimal", "low", "medium", "high", "xhigh"),
    "grok": CANONICAL_EFFORTS,
}
MIN_QUORUM = 2


@dataclass(frozen=True)
class EffortMapping:
    requested: str
    applied: str

    @property
    def clamped(self) -> bool:
        return self.applied != self.requested


@dataclass(frozen=True)
class Result:
    provider: str
    status: str
    model_policy: str
    effort: EffortMapping
    cli_version: str | None
    output: str | None
    error: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--packet", type=Path, required=True, help="Immutable self-contained council packet.")
    parser.add_argument("--round", type=int, required=True, dest="round_number", help="1 for the independent round, 2+ for rebuttal rounds.")
    parser.add_argument(
        "--brief",
        type=Path,
        help="Judge's rebuttal brief (draft canonical answer plus disagreements). Required for round 2 and up; forbidden for round 1.",
    )
    parser.add_argument("--out-dir", type=Path, required=True, help="Council directory; the round is written to <out-dir>/round-N/.")
    parser.add_argument(
        "--effort",
        required=True,
        choices=CANONICAL_EFFORTS,
        help=(
            "Reasoning effort of the judging session on the canonical scale "
            f"{', '.join(CANONICAL_EFFORTS)}. Mapped to each provider's nearest supported tier."
        ),
    )
    parser.add_argument(
        "--judge",
        choices=(*PROVIDERS, "other"),
        default="other",
        help="Provider family of the judging session. Recorded for provenance only; it does not exclude anyone.",
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=PROVIDERS,
        help="Provider to convene; repeat as needed. Defaults to every supported provider.",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        metavar="PROVIDER=MODEL",
        help="Pin a provider model; otherwise record and use the host-configured model.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    return parser.parse_args()


def parse_models(values: list[str], selected: tuple[str, ...]) -> dict[str, str]:
    models: dict[str, str] = {}
    for value in values:
        provider, separator, model = value.partition("=")
        if not separator or provider not in PROVIDERS or not model.strip():
            raise ValueError(f"invalid --model {value!r}; expected provider=model")
        if provider not in selected:
            raise ValueError(f"model supplied for unselected provider {provider!r}")
        if provider in models:
            raise ValueError(f"model supplied more than once for {provider!r}")
        models[provider] = model.strip()
    return models


def map_effort(provider: str, requested: str) -> EffortMapping:
    if requested not in CANONICAL_EFFORTS:
        raise ValueError(f"invalid effort {requested!r}")
    if provider not in PROVIDER_EFFORTS:
        raise ValueError(f"unknown provider {provider!r}")
    supported = PROVIDER_EFFORTS[provider]
    if requested in supported:
        return EffortMapping(requested, requested)
    requested_index = CANONICAL_EFFORTS.index(requested)

    def closeness(level: str) -> tuple[int, int]:
        level_index = CANONICAL_EFFORTS.index(level)
        return (abs(level_index - requested_index), -level_index)

    return EffortMapping(requested, min(supported, key=closeness))


def prompt_for(packet: str, packet_hash: str, round_number: int, brief: str | None) -> str:
    if round_number < 1:
        raise ValueError("round must be 1 or greater")
    if round_number == 1 and brief is not None:
        raise ValueError("round 1 is independent; no brief may be supplied")
    if round_number > 1 and brief is None:
        raise ValueError(f"round {round_number} is a rebuttal round; a brief is required")

    if round_number == 1:
        task = """Give your own complete, considered answer to the packet below. State your position first, then the reasoning behind it, the assumptions it rests on, and what evidence would change your mind. If the subject has no single right answer, name the genuine tradeoffs, but still commit to a recommendation rather than surveying every viewpoint. Do not write code or edit files. Do not search for or consider other council outputs."""
        sections = ""
    else:
        task = f"""This is rebuttal round {round_number}. The judge has synthesized the council's previous answers into a draft canonical answer and enumerated the disagreements that remain. Both are in the brief below, with positions attributed by provider.

For every enumerated disagreement, respond with exactly one of DEFEND, REVISE, or CONCEDE, followed by your evidence or reasoning. Defend only with a falsifiable argument or evidence; do not restate a position. Revise when another voice's argument is stronger and say what you now hold. Concede when you cannot defend. Then critique the draft canonical answer: what is wrong, missing, or overreaching, and what should change. Do not re-answer the whole packet. Do not write code or edit files."""
        sections = f"""
--- BEGIN JUDGE BRIEF ---
{brief}
--- END JUDGE BRIEF ---
"""

    return f"""You are one voice in an independent multi-model council. A separate judging session coordinates the council and writes the final answer; you are asked only for your own honest position.

{task}

The packet is self-contained; do not assume access to any repository, tool, or prior conversation.

Council packet SHA-256: {packet_hash}

--- BEGIN IMMUTABLE COUNCIL PACKET ---
{packet}
--- END IMMUTABLE COUNCIL PACKET ---
{sections}"""


def cli_version(executable: str) -> str | None:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = (completed.stdout or completed.stderr).strip()
    return text.splitlines()[0] if text else None


def command_for(
    provider: str,
    model: str | None,
    effort: str,
    prompt_file: Path,
    result_file: Path,
) -> list[str]:
    if provider == "claude":
        command = [
            "claude", "--print", "--no-session-persistence", "--permission-mode", "plan",
            "--tools", "", "--output-format", "text",
            "--effort", effort,
        ]
        if model:
            command.extend(["--model", model])
        return command
    if provider == "codex":
        command = [
            "codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only",
            "--ephemeral", "--color", "never", "--output-last-message", str(result_file),
            "-c", f"model_reasoning_effort={effort}",
        ]
        if model:
            command.extend(["--model", model])
        command.append("-")
        return command
    command = [
        "grok", "--prompt-file", str(prompt_file), "--permission-mode", "plan",
        "--tools", "", "--no-memory", "--no-subagents", "--output-format", "plain",
        "--reasoning-effort", effort,
    ]
    if model:
        command.extend(["--model", model])
    return command


def run_provider(
    provider: str,
    prompt: str,
    model: str | None,
    effort_level: str,
    timeout_seconds: int,
) -> Result:
    executable = shutil.which(provider)
    model_policy = model or "host-configured"
    effort = map_effort(provider, effort_level)
    if executable is None:
        return Result(provider, "unavailable", model_policy, effort, None, None, "CLI not found")

    version = cli_version(executable)
    with tempfile.TemporaryDirectory(prefix=f"ai-council-{provider}-") as temp_name:
        temp_dir = Path(temp_name)
        prompt_file = temp_dir / "prompt.md"
        result_file = temp_dir / "result.md"
        prompt_file.write_text(prompt, encoding="utf-8")
        command = command_for(provider, model, effort.applied, prompt_file, result_file)
        try:
            completed = subprocess.run(
                command,
                cwd=temp_dir,
                input=prompt if provider in {"claude", "codex"} else None,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return Result(provider, "failed", model_policy, effort, version, None, "timed out")
        except OSError as error:
            return Result(provider, "failed", model_policy, effort, version, None, str(error))

        output = result_file.read_text(encoding="utf-8") if result_file.exists() else completed.stdout
        output = output.strip()
        if completed.returncode != 0 or not output:
            detail = completed.stderr.strip() or f"exited {completed.returncode} without output"
            return Result(provider, "failed", model_policy, effort, version, None, detail[-2000:])
        return Result(provider, "succeeded", model_policy, effort, version, output, None)


def effort_label(mapping: EffortMapping) -> str:
    if mapping.clamped:
        return f"{mapping.applied} (clamped from {mapping.requested})"
    return mapping.applied


def main() -> int:
    args = parse_args()
    selected = tuple(dict.fromkeys(args.provider or PROVIDERS))
    if args.timeout_seconds <= 0:
        print("--timeout-seconds must be positive", file=sys.stderr)
        return 2

    available = tuple(provider for provider in selected if shutil.which(provider) is not None)
    if len(available) < MIN_QUORUM:
        print(
            f"council needs at least {MIN_QUORUM} installed voices; found {len(available)} of {', '.join(selected)}",
            file=sys.stderr,
        )
        return 2

    round_dir = args.out_dir / f"round-{args.round_number}"
    try:
        models = parse_models(args.model, selected)
        packet = args.packet.read_text(encoding="utf-8")
        brief = args.brief.read_text(encoding="utf-8") if args.brief else None
        packet_hash = hashlib.sha256(packet.encode("utf-8")).hexdigest()
        prompt = prompt_for(packet, packet_hash, args.round_number, brief)
        round_dir.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2

    brief_hash = hashlib.sha256(brief.encode("utf-8")).hexdigest() if brief is not None else None
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = {
            provider: executor.submit(
                run_provider,
                provider,
                prompt,
                models.get(provider),
                args.effort,
                args.timeout_seconds,
            )
            for provider in selected
        }
        results = [futures[provider].result() for provider in selected]

    kind = "independent answer" if args.round_number == 1 else f"rebuttal (round {args.round_number})"
    for result in results:
        if result.output is None:
            continue
        header = (
            f"# {result.provider.title()} {kind}\n\n"
            f"- CLI version: {result.cli_version or 'unknown'}\n"
            f"- Model policy: {result.model_policy}\n"
            f"- Session effort: {result.effort.requested}\n"
            f"- Applied effort: {effort_label(result.effort)}\n"
            f"- Packet SHA-256: `{packet_hash}`\n"
            + (f"- Brief SHA-256: `{brief_hash}`\n" if brief_hash else "")
            + f"- Generated: {generated_at}\n\n"
        )
        (round_dir / f"{result.provider}.md").write_text(header + result.output + "\n", encoding="utf-8")

    manifest = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "round": args.round_number,
        "packet": str(args.packet.resolve()),
        "packetSha256": packet_hash,
        "brief": str(args.brief.resolve()) if args.brief else None,
        "briefSha256": brief_hash,
        "judge": args.judge,
        "effort": args.effort,
        "voices": list(selected),
        "results": [
            {
                "provider": result.provider,
                "status": result.status,
                "modelPolicy": result.model_policy,
                "effortRequested": result.effort.requested,
                "effortApplied": result.effort.applied,
                "effortClamped": result.effort.clamped,
                "cliVersion": result.cli_version,
                "error": result.error,
            }
            for result in results
        ],
    }
    (round_dir / "council-run.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    succeeded = [result.provider for result in results if result.status == "succeeded"]
    failed = [result.provider for result in results if result.status == "failed"]
    unavailable = [result.provider for result in results if result.status == "unavailable"]
    if unavailable:
        print(f"not installed on this host, skipped: {', '.join(unavailable)}", file=sys.stderr)
    if len(succeeded) < MIN_QUORUM:
        print(
            f"quorum not met: {len(succeeded)} of {MIN_QUORUM} voices answered; inspect council-run.json",
            file=sys.stderr,
        )
        return 1
    if failed:
        print(f"round incomplete; inspect council-run.json (failed: {', '.join(failed)})", file=sys.stderr)
        return 1
    print(str(round_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
