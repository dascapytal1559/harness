---
name: multi-model-convergence-planning
description: >
  Run an independent multi-model planning panel: write a session-primary plan, dispatch isolated
  alternative providers, synthesize, resolve a human decision docket, and refine until material
  changes converge. Use when the user asks to plan a project or feature with Claude, Codex, and
  Grok, run a planning panel, converge competing plans, create a planning packet or decision
  docket, or runs /multi-model-convergence-planning. Do not use for isolated coding or for
  same-family subagent brainstorming presented as triangulation.
---

# Multi-model convergence planning

Produce one implementable canonical plan by challenging a session-primary draft with independent proposals from other model families. This skill owns packet construction, primary-plan preservation, isolated alternative dispatch, synthesis, the decision docket, rebuttal, and the convergence audit.

Do not write product source code.

## Durable layout

Use existing repository conventions when present. Otherwise use:

```text
docs/planning/
  PROJECT_BRIEF.md
  PLANNING_PACKET.md
  PRIMARY_PLAN.md
  panel-runs/<UTC timestamp>/
    <alternative-provider>.md
    panel-run.json
    rebuttals/
  SYNTHESIS.md
  DECISION_DOCKET.md
  REFINEMENT.md
docs/PLAN.md
```

`PROJECT_BRIEF.md` preserves human intent. `PLANNING_PACKET.md` is an immutable snapshot for one panel run. A later material brief change requires a new packet and panel run; never silently alter the evidence underneath existing proposals.

`PRIMARY_PLAN.md` is the active session's complete proposal created before it can see alternative plans. It preserves what the session initially believed and makes later synthesis changes auditable.

## Build the planning packet

Include:

- product goal, intended users, and why the project matters;
- primary end-to-end user workflows and acceptance outcomes;
- scope, non-goals, constraints, compatibility promises, and risk posture;
- relevant repository architecture and current behavior for an existing project;
- accepted decisions, unresolved questions, research, and required standards;
- operational, security, privacy, migration, and verification expectations where relevant.

Exclude previous proposals and synthesis commentary. Compute and preserve a SHA-256 hash so every proposal can be tied to the exact same evidence.

## Keep the active session primary

The session that invoked this skill is both facilitator and primary planner. It owns:

- clarification of the project brief;
- the initial complete plan;
- synthesis and recommendation after alternatives return;
- the human decision docket;
- the canonical plan.

This role follows the session rather than a hard-coded model family. Record the host/provider and exact model when discoverable; otherwise record `host-configured`. The session's continuity with the user is a feature: it carries product intent and can conduct the decision dialogue. Its initial proposal is not independent review, so preserve it before exposing the session to alternatives.

Native subagents from the same model family may assist with bounded research, but do not count them as cross-model alternatives. The independent challenge comes from other installed provider families.

## Dispatch alternative planners automatically

First inspect `command -v claude`, `command -v codex`, and `command -v grok`, then capture each `--version`. Do not install, authenticate, update, or switch provider accounts implicitly.

Identify the active session provider explicitly, then run the bundled adapter from this skill directory. For a Codex session:

```sh
python3 scripts/dispatch_planning_panel.py \
  --session-provider codex \
  --packet docs/planning/PLANNING_PACKET.md \
  --out-dir docs/planning/panel-runs/<UTC timestamp>
```

By default the adapter targets every supported provider except the session provider. Thus Codex launches Claude and Grok, Claude launches Codex and Grok, and Grok launches Codex and Claude. Use `--provider` only to select a narrower explicit alternative set. Use `--session-provider other` for a host family outside the supported provider list. The adapter rejects an attempt to present the active provider family as an independent alternative.

Use `--model provider=model-id` when the repository pins a model. Otherwise the explicit policy is `host-configured`: retain the authenticated CLI's configured model and record that policy in `panel-run.json`. Never guess a model identifier that the installed CLI may not support.

Announce the providers, requested models or host-model policy, output location, and possible quota or metered-cost implications before dispatch. An action-mode request authorizes normal use of already-authenticated subscription CLIs; obtain separate authority for known metered API spending or an unusual budget.

The adapter uses isolated temporary working directories, disables tools where supported, gives Codex a read-only sandbox, disables session memory, and writes only the captured proposal artifacts. Inspect `--help` again before use if an installed CLI's major behavior has changed from the validated contracts recorded in the adapter.

If one alternative fails, preserve its failure metadata and the successful outputs. For non-trivial planning, aim for two successful alternative model families and tell the user which perspective is missing. Use guided collection when the missing perspective materially affects confidence. For small or low-risk work, the active session plus one different model family may be proportionate when the limitation and rationale are recorded.

## Keep roles complementary

- **Codex — global architect:** system coherence, boundaries, data flow, tradeoffs, and verification strategy.
- **Claude — implementation realist:** executable structure, maintainability, failure handling, migration, and operational detail.
- **Grok — assumption challenger:** hidden assumptions, counterexamples, simpler alternatives, abuse cases, and product risks.

Every role must still return a complete standalone plan. Roles bias attention; they do not divide the plan into fragments.

## Adapt the upstream primary-planner role

The upstream guide currently uses GPT-5.6 Sol Pro in the ChatGPT Pro web app for the initial plan and final synthesis. This skill preserves the single-primary-planner structure but assigns it to the active session for a lower-friction desktop workflow; do not repeat an availability disclaimer in every synthesis.

## Synthesize selectively

Do not vote, concatenate, or accept every suggestion. The active session compares its preserved primary plan and the alternatives against the brief, then creates `docs/planning/SYNTHESIS.md`, classifying material ideas as accept, adapt, reject, or unresolved, with rationale and conflicts.

Then create `docs/planning/DECISION_DOCKET.md`. Classify every material difference as:

- **Consensus improvement** — integrate automatically when it preserves accepted intent.
- **Engineering tradeoff** — give a recommendation, alternatives, evidence, reversibility, and consequences; escalate when material.
- **Product decision** — require the user to choose; do not delegate taste, user value, or scope to a model.
- **Architecture commitment** — require the user when costly to reverse or consequential for security, compatibility, operations, or data.
- **Needs evidence** — run a focused research or rebuttal round before recommending.
- **Rejected suggestion** — preserve the rejection and rationale.

Ask about unresolved items one focused question at a time, ordered by how many downstream choices they constrain. Keep the canonical plan provisional until every blocking docket entry is resolved. The user need not review routine wording or every consensus improvement.

## Use rebuttal rounds narrowly

When a disagreement depends on factual or technical reasoning, give the affected providers the relevant competing claims, the immutable planning packet hash, and a request to defend, revise, or concede. Store outputs under the panel run's `rebuttals/` directory with provider/model provenance.

Do not run open-ended model debate. Limit rebuttal to one round by default, ask for evidence and falsifiable tradeoffs, and return any remaining value judgment to the user. Rebuttal occurs after independent proposals, so never describe rebuttal outputs as independent plans.

After the docket is resolved:

1. Update `DECISION_DOCKET.md` with the decision, owner, date, rationale, and affected plan sections.
2. Create or revise one canonical `docs/PLAN.md` incorporating only the selected design.
3. Record accepted material decisions in the repository decision log.

An integration agent may make reversible editorial and structural choices, but must record them. Never allow synthesis to silently settle a blocking docket entry.

## Audit and converge

Use a transparent matrix instead of telling reviewers that a fabricated number of defects exists. Audit every plan against:

- brief goals, users, workflows, acceptance outcomes, scope, and non-goals;
- architecture, state and data flows, boundaries, dependencies, and explicit configuration;
- failure, retry, rollback, recovery, migration, and compatibility behavior;
- security, privacy, abuse cases, observability, and operations where relevant;
- test strategy, sequencing, taskability, and unresolved decisions;
- proposal-to-plan traceability and contradictions between accepted ideas.

Run fresh-context reviews until major architecture and workflow changes stop. Record each round and whether it remains in `major-change` or `near-convergence` mode. Move to Beads only when fresh findings are mainly corrections, tests, sequencing, or execution context rather than product redesign.
