---
name: ai-council
description: >
  Convene every model family installed on this host (Claude, Codex, Grok) on one subject and
  converge them into a single canonical answer, with the active session acting as coordinator
  and final judge rather than as a voice. Runs an independent round, then judged rebuttal rounds
  until material changes stop, escalating disagreements that will not budge to the user. Use
  when the user says to do X via ai-council, convene a council on X, or runs /ai-council, for
  any subject: a methodology, an analysis, a design, an interpretation, a position. Do not use
  for a one-shot second opinion (that is ask-other-models) or for a software implementation plan
  with repository planning artifacts (that is multi-model-convergence-planning).
---

# AI council

Converge independent answers from every installed model family into one canonical answer. The active session is the **judge**: it writes the packet, dispatches rounds, synthesizes, rules on disagreements that reasoning or evidence can settle, and escalates the ones that cannot. The judge is not a voice. It does not write its own answer to the subject first, and its own model family is convened as a fresh isolated peer like every other.

## Council record

Every council lives under `docs/council/<slug>/` relative to the repository root. Derive a kebab-case slug from the subject. If the directory already exists, use `<slug>-<UTC timestamp>` rather than writing into an old record. Outside a repository, ask the user for a directory before doing anything else.

```text
docs/council/<slug>/
  packet.md            immutable subject packet, hashed
  round-1/             independent answers: <provider>.md, council-run.json
  synthesis-1.md       judge's classification after round 1
  brief-2.md           judge's rebuttal brief for round 2
  round-2/             rebuttals
  synthesis-2.md
  ...
  decision-docket.md   items escalated to the user
  CANONICAL.md         the converged answer
```

## Compose the packet

Write `packet.md` once. The voices run in isolated directories with tools disabled, so it must be self-contained:

- the subject, stated once and precisely, and what kind of deliverable is wanted (a methodology, a ranking, a critique, an interpretation);
- every excerpt, datum, constraint, or context needed to answer it. For a data set, include a described excerpt or sample and record how it was sampled;
- acceptance criteria if the user has any;
- nothing about the user's leaning, the judge's view, or any model's prior output.

If an honest packet would need more than fits comfortably, say so and ask the user to trim the subject or accept the sampling. Compute the SHA-256 and treat the packet as immutable: a material change to the subject is a new council, not an edited packet.

## Discover and announce

Inspect `command -v claude`, `command -v codex`, and `command -v grok` and capture each `--version`. Do not install, authenticate, update, or switch accounts. A missing CLI is skipped and reported. A council needs at least two installed voices; with fewer, stop and tell the user.

Resolve the session's reasoning effort from its own recorded level (Grok `summary.json` `reasoning_effort`, Claude `--effort` / `/effort` / `effortLevel`, Codex a mid-session override or else `model_reasoning_effort` in `~/.codex/config.toml`). Map aliases such as `auto` to the concrete tier. If you cannot see the level, ask; do not invent a higher tier.

Before round 1, tell the user once: the voices, the effort and any provider clamps, the model policy, the output directory, the rebuttal cap, and the quota or metered-cost implications of up to cap plus one dispatches. Later rounds get a one-line note, not a fresh consent prompt.

## Round 1: independent answers

Run the bundled adapter from this skill directory. For a Claude session at high effort:

```sh
python3 scripts/dispatch_council.py \
  --packet docs/council/<slug>/packet.md \
  --round 1 \
  --effort high \
  --judge claude \
  --out-dir docs/council/<slug>
```

`--effort` is required and is mapped to each provider's nearest supported tier, ties going higher; requested and applied effort are recorded in `council-run.json`. `--judge` is provenance only and excludes nobody. Use `--provider` only to narrow the set. The Claude voice is pinned to the Opus family by skill default (`--model claude=opus`, resolved by the CLI to the latest Opus) so it does not follow whatever model the host session runs; Codex and Grok use the host-configured model. Use `--model provider=model-id` to override either. The model policy and its source (`pinned`, `skill-default`, `host-configured`) are recorded in `council-run.json`. Do not pass provider-native effort flags yourself.

Every voice gets the identical neutral prompt. No roles or lenses are assigned; diversity comes from the model families.

## Synthesize

After each round write `synthesis-N.md`. Read every answer in full, then:

1. Extract each voice's material claims. Material means a recommendation, a method step, a conclusion, or a stated constraint. Wording, ordering, and emphasis are not material.
2. Classify every material claim as **accept**, **adapt**, **reject**, or **unresolved**, with a one-line rationale and the provider attribution.
3. Enumerate the disagreements: for each, the competing positions by provider and what the split actually hinges on (a fact, a value judgment, or risk appetite).
4. Draft or revise the canonical answer from the accepted and adapted claims. Any content the judge adds that no voice proposed is labelled **judge-originated** so the user can see it.
5. Where a factual claim can be checked, check it with tools and record what was verified. The voices stay blind; the judge does not.
6. Record the round's status: `major-change`, `near-convergence`, or `converged`.

Do not vote, average, or blend positions into an anonymous consensus.

## Rebuttal rounds

If unresolved disagreements remain and the cap is not reached, write `brief-N.md` for the next round: the packet hash, the current draft canonical answer, and the enumerated disagreements with positions attributed by provider. One brief, shared by all voices. Then dispatch:

```sh
python3 scripts/dispatch_council.py \
  --packet docs/council/<slug>/packet.md \
  --round 2 \
  --brief docs/council/<slug>/brief-2.md \
  --effort high \
  --judge claude \
  --out-dir docs/council/<slug>
```

Each voice must answer every disagreement with DEFEND, REVISE, or CONCEDE plus evidence, and critique the draft. Synthesize again.

**Stopping.** The judge decides when the council has converged: stop when a round produces no material change. The hard cap is 5 rebuttal rounds after round 1, so at most 6 dispatches; the user may lower or raise it for one council by saying so.

**Ruling.** Where a disagreement moved (someone revised or conceded, or one side produced evidence the other could not answer), the judge rules and records the ruling and its basis in the synthesis.

**Stuck.** A disagreement is stuck when a rebuttal round ends with no side conceding or materially revising it. Do not re-run it. Stuck items are batched into `decision-docket.md` at the end, each with the competing positions, what it hinges on, the judge's recommendation, and the consequences of each choice. Exception: if a stuck item constrains the other open items, pause the loop and ask the user immediately.

## Finalize

Write `CANONICAL.md` from the last synthesis. It stays **provisional** until every docket entry is settled by the user; mark it so. Once settled, update the docket with the decision and date, and fold the outcome into `CANONICAL.md`.

Deliver in chat:

1. the canonical answer, or its provisional form with the docket questions asked one at a time, ordered by how many other items each constrains;
2. a short convergence trace: rounds run, each round's status, which voices took part, any clamps or failures;
3. what changed between round 1 and the final answer, and what the judge originated.

Keep every per-round provider file so the user can read any voice in full.

## Feedback

Every council ends by posting feedback about this skill, not about the subject, as one new file in `feedbacks/` inside this skill's directory. Post it even when the council aborted, ran short of quorum, or hit the cap without converging; an aborted council is the most useful feedback. Name it `<YYYY-MM-DD>-<host>-<slug>.md`, host being claude, codex, or grok, slug being the council's record directory name. Never edit SKILL.md, the scripts, or another run's feedback; refinement happens later, by a human reading these.

```
# <date> <host>, <slug>: <one-line title>

Subject: <one line>. Record: docs/council/<slug>/.
Voices: <providers that answered, with any clamps or failures>. Judge: <host and model>.
Rounds: <N run>, status per round: <e.g. major-change, near-convergence, converged>.
Docket: <number of stuck items escalated>. Outcome: <one line>.

## What worked
- <what the procedure got right>

## 1. <the issue, one line>
<what happened and what it cost. Quote the SKILL.md line if it caused it.>
Suggest: <the smallest change to SKILL.md or the scripts that removes it>

## 2. ...
```

As many numbered issues as the run produced, each with its own suggestion. Paths from the record are fine; the packet's contents and the voices' answers are not.
