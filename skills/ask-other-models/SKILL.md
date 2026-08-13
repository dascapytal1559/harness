---
name: ask-other-models
description: >
  Ask every other model family configured on this host for an independent opinion on one
  question, then present the attributed answers side by side with an honest synthesis. Use when
  the user says to ask other models what they think about X, get other models' opinions on X,
  get a second opinion from Codex or Grok, or runs /ask-other-models. Do not use for full
  project planning — that is multi-model-convergence-planning — or for same-family subagent
  brainstorming presented as a cross-model panel.
---

# Ask other models

Collect independent opinions on one question from every other model family installed on this host, and present them with clear attribution. The active session is itself one voice on the panel: its own family is excluded from dispatch, and it contributes its opinion directly in the conversation.

This skill gathers and compares opinions. It does not produce planning artifacts, decision dockets, or code changes.

## Compose the question packet

Write the question to a temporary file (for example under `mktemp -d`). The alternatives run in isolated working directories with tools disabled, so the packet must be self-contained:

- the question itself, stated once and precisely;
- any code excerpts, error output, data, or constraints needed to answer it;
- what kind of answer is wanted (recommendation, critique, prediction, tradeoff call);
- nothing about your own opinion, the user's leaning, or other models' views.

If the honest packet would need more context than fits comfortably (a whole subsystem, a long history), say so and either trim the question or suggest the planning panel instead.

## Record your own opinion first

Before dispatching, write down your own complete answer to the packet — in the conversation or a scratch note. You are about to read persuasive alternatives; preserving your prior keeps the synthesis honest and lets the user see where you changed your mind.

## Discover and announce

Inspect `command -v claude`, `command -v codex`, and `command -v grok`, then capture each `--version`. Do not install, authenticate, update, or switch provider accounts implicitly.

Identify the active session's provider family explicitly. A missing CLI is skipped and reported, not treated as an error. Before dispatch, tell the user which providers will run, the host-model policy or any pinned models, where outputs land, and possible quota or metered-cost implications.

## Dispatch

Run the bundled adapter from this skill directory. For a Claude session:

```sh
python3 scripts/dispatch_opinions.py \
  --session-provider claude \
  --question <dir>/question.md \
  --out-dir <dir>/opinions
```

By default the adapter targets every supported provider except the session provider; it rejects an attempt to present the session's own family as an independent voice. Use `--provider` only to narrow the set, `--session-provider other` for a host family outside the supported list, and `--model provider=model-id` only when a model is pinned — otherwise the explicit policy is `host-configured`: keep the authenticated CLI's configured model and record that policy in `opinion-run.json`.

Each provider gets the identical neutral prompt. Unlike the planning panel, no complementary roles are assigned — the point is each model's natural, unbiased read of the same question.

The adapter uses isolated temporary working directories, disables tools where supported, gives Codex a read-only sandbox, disables session memory, and writes only the captured opinion artifacts. If a provider fails, its failure metadata is preserved alongside the successful outputs; the run is useful with as few as one successful alternative, but tell the user which perspective is missing.

## Present the results

Do not vote, average, or blend the answers into one anonymous consensus. Present:

1. **Per-model opinions** — a faithful summary of each provider's position with its name and recorded model policy, including the active session's own pre-dispatch opinion as an equal entry.
2. **Agreements and disagreements** — where the panel converges, where it splits, and what each split actually hinges on (fact, taste, or risk appetite).
3. **Your synthesis** — clearly labelled as the session's view after reading the others: your recommendation, what changed your mind if anything, and which disagreements only the user can settle.

Keep the raw per-provider markdown files in the output directory so the user can read any answer in full.
