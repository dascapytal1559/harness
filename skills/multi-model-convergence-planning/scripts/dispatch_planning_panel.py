#!/usr/bin/env python3
"""Dispatch one immutable planning packet to model families other than the active session."""

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


PROVIDERS = {
    "codex": {
        "role": "global architect",
        "focus": "system coherence, boundaries, data flow, tradeoffs, and verification strategy",
    },
    "claude": {
        "role": "implementation realist",
        "focus": "executable structure, maintainability, failure handling, migration, and operations",
    },
    "grok": {
        "role": "assumption challenger",
        "focus": "hidden assumptions, counterexamples, simpler alternatives, abuse cases, and product risks",
    },
}
DEFAULT_PROVIDERS = ("codex", "claude", "grok")


@dataclass(frozen=True)
class Result:
    provider: str
    role: str
    status: str
    model_policy: str
    cli_version: str | None
    output: str | None
    error: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--session-provider",
        required=True,
        choices=(*PROVIDERS, "other"),
        help=(
            "Provider family of the active Conductor session. By default that family is excluded "
            "from the independent alternatives; use 'other' for a different host family."
        ),
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=tuple(PROVIDERS),
        help=(
            "Alternative provider to run; repeat as needed. Defaults to every supported provider "
            "except --session-provider."
        ),
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        metavar="PROVIDER=MODEL",
        help="Pin a provider model; otherwise record and use the host-configured model.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=1800)
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


def prompt_for(provider: str, packet: str, packet_hash: str) -> str:
    spec = PROVIDERS[provider]
    return f"""You are the {spec['role']} in an independent software-planning panel.

Create a complete, standalone implementation plan from the planning packet below. Concentrate especially on {spec['focus']}, but cover the whole product. Do not assume another proposal will fill gaps. Do not write code or edit files. Do not search for or consider other panel outputs.

Make user workflows, scope, architecture, state and data flow, explicit dependencies and configuration, failure and recovery behavior, security and privacy concerns, migration and compatibility, operations, testing, sequencing, risks, and unresolved human decisions concrete. Explain material tradeoffs. Avoid verbosity that adds no decision or execution value.

Planning packet SHA-256: {packet_hash}

--- BEGIN IMMUTABLE PLANNING PACKET ---
{packet}
--- END IMMUTABLE PLANNING PACKET ---
"""


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


def command_for(provider: str, model: str | None, prompt_file: Path, result_file: Path) -> list[str]:
    if provider == "claude":
        command = [
            "claude", "--print", "--no-session-persistence", "--permission-mode", "plan",
            "--tools", "", "--output-format", "text",
        ]
        if model:
            command.extend(["--model", model])
        return command
    if provider == "codex":
        command = [
            "codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only",
            "--ephemeral", "--color", "never", "--output-last-message", str(result_file),
        ]
        if model:
            command.extend(["--model", model])
        command.append("-")
        return command
    command = [
        "grok", "--prompt-file", str(prompt_file), "--permission-mode", "plan",
        "--tools", "", "--no-memory", "--no-subagents", "--output-format", "plain",
    ]
    if model:
        command.extend(["--model", model])
    return command


def run_provider(
    provider: str,
    packet: str,
    packet_hash: str,
    model: str | None,
    timeout_seconds: int,
) -> Result:
    spec = PROVIDERS[provider]
    executable = shutil.which(provider)
    model_policy = model or "host-configured"
    if executable is None:
        return Result(provider, spec["role"], "unavailable", model_policy, None, None, "CLI not found")

    version = cli_version(executable)
    prompt = prompt_for(provider, packet, packet_hash)
    with tempfile.TemporaryDirectory(prefix=f"flywheel-{provider}-") as temp_name:
        temp_dir = Path(temp_name)
        prompt_file = temp_dir / "prompt.md"
        result_file = temp_dir / "result.md"
        prompt_file.write_text(prompt, encoding="utf-8")
        command = command_for(provider, model, prompt_file, result_file)
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
            return Result(provider, spec["role"], "failed", model_policy, version, None, "timed out")
        except OSError as error:
            return Result(provider, spec["role"], "failed", model_policy, version, None, str(error))

        output = result_file.read_text(encoding="utf-8") if result_file.exists() else completed.stdout
        output = output.strip()
        if completed.returncode != 0 or not output:
            detail = completed.stderr.strip() or f"exited {completed.returncode} without output"
            return Result(provider, spec["role"], "failed", model_policy, version, None, detail[-2000:])
        return Result(provider, spec["role"], "succeeded", model_policy, version, output, None)


def main() -> int:
    args = parse_args()
    selected = tuple(
        dict.fromkeys(
            args.provider
            or tuple(provider for provider in DEFAULT_PROVIDERS if provider != args.session_provider)
        )
    )
    if args.session_provider in PROVIDERS and args.session_provider in selected:
        print(
            f"active session provider {args.session_provider!r} cannot also be an independent alternative",
            file=sys.stderr,
        )
        return 2
    if not selected:
        print("select at least one alternative provider", file=sys.stderr)
        return 2
    if args.timeout_seconds <= 0:
        print("--timeout-seconds must be positive", file=sys.stderr)
        return 2
    try:
        models = parse_models(args.model, selected)
        packet = args.packet.read_text(encoding="utf-8")
        args.out_dir.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2

    packet_hash = hashlib.sha256(packet.encode("utf-8")).hexdigest()
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = {
            provider: executor.submit(
                run_provider, provider, packet, packet_hash, models.get(provider), args.timeout_seconds
            )
            for provider in selected
        }
        results = [futures[provider].result() for provider in selected]

    for result in results:
        if result.output is None:
            continue
        header = (
            f"# {result.provider.title()} independent proposal\n\n"
            f"- Role: {result.role}\n"
            f"- CLI version: {result.cli_version or 'unknown'}\n"
            f"- Model policy: {result.model_policy}\n"
            f"- Planning packet SHA-256: `{packet_hash}`\n"
            f"- Generated: {generated_at}\n\n"
        )
        (args.out_dir / f"{result.provider}.md").write_text(header + result.output + "\n", encoding="utf-8")

    manifest = {
        "schemaVersion": 2,
        "generatedAt": generated_at,
        "packet": str(args.packet.resolve()),
        "packetSha256": packet_hash,
        "primaryPlanner": {
            "kind": "active-session",
            "provider": args.session_provider,
        },
        "alternativeProviders": list(selected),
        "results": [
            {
                "provider": result.provider,
                "role": result.role,
                "status": result.status,
                "modelPolicy": result.model_policy,
                "cliVersion": result.cli_version,
                "error": result.error,
            }
            for result in results
        ],
    }
    (args.out_dir / "panel-run.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    failed = [result.provider for result in results if result.status != "succeeded"]
    if failed:
        print(f"planning panel incomplete; inspect panel-run.json (failed: {', '.join(failed)})", file=sys.stderr)
        return 1
    print(str(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
