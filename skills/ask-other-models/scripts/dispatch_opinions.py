#!/usr/bin/env python3
"""Ask every other model family configured on this host for an independent opinion on one question."""

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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", type=Path, required=True, help="Self-contained question packet.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--session-provider",
        required=True,
        choices=(*PROVIDERS, "other"),
        help=(
            "Provider family of the active session. That family is excluded from the panel; "
            "use 'other' for a host family outside the supported provider list."
        ),
    )
    parser.add_argument(
        "--session-effort",
        required=True,
        choices=CANONICAL_EFFORTS,
        help=(
            "Reasoning effort of the active session on the canonical scale "
            f"{', '.join(CANONICAL_EFFORTS)}. Mapped to each provider's nearest supported tier."
        ),
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=PROVIDERS,
        help=(
            "Provider to ask; repeat as needed. Defaults to every supported provider except "
            "--session-provider."
        ),
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        metavar="PROVIDER=MODEL",
        help="Pin a provider model; otherwise record and use the host-configured model.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600)
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
        raise ValueError(f"invalid session effort {requested!r}")
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


def prompt_for(question: str) -> str:
    return f"""You are one voice in an independent multi-model opinion panel.

Give your own considered opinion on the question below. State your position first, then the reasoning behind it, the assumptions it rests on, and what evidence would change your mind. If the question has no single right answer, name the genuine tradeoffs — but still commit to a recommendation rather than surveying every viewpoint. Do not write code or edit files. Do not search for or consider other panel outputs.

The question packet is self-contained; do not assume access to any repository, tool, or prior conversation.

--- BEGIN QUESTION PACKET ---
{question}
--- END QUESTION PACKET ---
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
    question: str,
    model: str | None,
    session_effort: str,
    timeout_seconds: int,
) -> Result:
    executable = shutil.which(provider)
    model_policy = model or "host-configured"
    effort = map_effort(provider, session_effort)
    if executable is None:
        return Result(provider, "unavailable", model_policy, effort, None, None, "CLI not found")

    version = cli_version(executable)
    prompt = prompt_for(question)
    with tempfile.TemporaryDirectory(prefix=f"ask-other-models-{provider}-") as temp_name:
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
    selected = tuple(
        dict.fromkeys(
            args.provider
            or tuple(provider for provider in PROVIDERS if provider != args.session_provider)
        )
    )
    if args.session_provider in PROVIDERS and args.session_provider in selected:
        print(
            f"active session provider {args.session_provider!r} cannot also be an independent panel voice",
            file=sys.stderr,
        )
        return 2
    if not selected:
        print("select at least one provider", file=sys.stderr)
        return 2
    if args.timeout_seconds <= 0:
        print("--timeout-seconds must be positive", file=sys.stderr)
        return 2
    try:
        models = parse_models(args.model, selected)
        question = args.question.read_text(encoding="utf-8")
        args.out_dir.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2

    question_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = {
            provider: executor.submit(
                run_provider,
                provider,
                question,
                models.get(provider),
                args.session_effort,
                args.timeout_seconds,
            )
            for provider in selected
        }
        results = [futures[provider].result() for provider in selected]

    for result in results:
        if result.output is None:
            continue
        header = (
            f"# {result.provider.title()} independent opinion\n\n"
            f"- CLI version: {result.cli_version or 'unknown'}\n"
            f"- Model policy: {result.model_policy}\n"
            f"- Session effort: {result.effort.requested}\n"
            f"- Applied effort: {effort_label(result.effort)}\n"
            f"- Question SHA-256: `{question_hash}`\n"
            f"- Generated: {generated_at}\n\n"
        )
        (args.out_dir / f"{result.provider}.md").write_text(header + result.output + "\n", encoding="utf-8")

    manifest = {
        "schemaVersion": 2,
        "generatedAt": generated_at,
        "question": str(args.question.resolve()),
        "questionSha256": question_hash,
        "sessionProvider": args.session_provider,
        "sessionEffort": args.session_effort,
        "panelProviders": list(selected),
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
    (args.out_dir / "opinion-run.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    succeeded = [result.provider for result in results if result.status == "succeeded"]
    failed = [result.provider for result in results if result.status == "failed"]
    unavailable = [result.provider for result in results if result.status == "unavailable"]
    if unavailable:
        print(f"not installed on this host, skipped: {', '.join(unavailable)}", file=sys.stderr)
    if not succeeded:
        print("no provider returned an opinion; inspect opinion-run.json", file=sys.stderr)
        return 1
    if failed:
        print(f"panel incomplete; inspect opinion-run.json (failed: {', '.join(failed)})", file=sys.stderr)
        return 1
    print(str(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
