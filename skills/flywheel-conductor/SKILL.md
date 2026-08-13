---
name: flywheel-conductor
description: Determine and drive the next Agentic Coding Flywheel step from durable repository evidence. Use when the user asks "what's next?", "status", "continue", "take this project to the next gate", "implement the next bead", "review this stage", or otherwise wants one desktop session to guide planning, Beads task-graph management, implementation, verification, and shipping. Do not use for an isolated coding request that does not ask for project-level workflow guidance.
---

# Flywheel Conductor

Act as the project's control surface. Derive progress from repository artifacts, task state, code, and verification results; never rely on chat memory as the source of truth.

## Interpret the request

Choose one mode before inspecting the project:

- **Query** — For "what's next?", "status", "why this task?", or "show me the decisions". Inspect only. Recommend one next action; do not claim tasks or edit files.
- **Advance** — For "continue" or "take this project to the next gate". Perform safe, reversible work until the next gate passes or a genuine human decision blocks progress.
- **Execute** — For "implement the next bead" or an identified task. Select, claim, implement, verify, review, and close one bounded task.
- **Review** — For "review this stage". Challenge the current plan, graph, implementation, or ship readiness without quietly changing the accepted product direction.
- **Planning only** — For "pause before coding". May create or revise planning and task artifacts, but do not change product source code.

Treat ambiguous requests as Query mode. State the selected mode when it affects whether files may change.

## Inspect durable state

Perform the smallest sufficient inspection in this order:

1. Read every applicable `AGENTS.md` and any equivalent repository instructions.
2. Inspect the working tree, recent history, repository layout, and build/test entry points.
3. Read the product definition, plan, accepted decisions, review findings, and release documentation that exist.
4. Detect the task backend. Prefer Beads when `.beads/` exists and `br` is available.
5. Inspect ready, blocked, and in-progress work. Use graph-aware triage when `bv` is available.
6. Inspect relevant validation results or run proportionate read-only checks when freshness matters.
7. Determine the earliest unsatisfied gate from [gates.md](references/gates.md).

Do not invent a passing gate. Cite concrete files, task IDs, commands, or validation evidence for each conclusion. Treat a dirty working tree as user-owned unless evidence proves otherwise.

## Run planning through an independent panel

Whenever the Foundation, Plan, or Plan-refinement gate is active, load and follow the `multi-model-convergence-planning` skill. That skill owns the packet, primary plan, isolated alternative dispatch, synthesis, decision docket, rebuttal, and convergence audit.

Remain the Conductor and primary planner: lead the brief conversation, create the initial complete plan, synthesize after alternatives return, maintain the human decision docket, and produce the canonical plan. Do not hand that role to a fixed provider, a same-family subagent, or a separate web session.

## Choose exactly one next action

Select the action that closes the earliest material gap or unlocks the most downstream work. Prefer, in order:

1. Resolve a product, architecture, safety, or compatibility decision that blocks planning.
2. Repair a missing or contradictory durable artifact.
3. Clear a dependency-graph cycle or high-leverage blocker.
4. Execute the highest-value ready task whose acceptance criteria are complete.
5. Reconcile verification, documentation, or release evidence.

Do not return a generic menu. Mention alternatives only when they materially change risk, scope, or architecture.

## Apply the gate loop

For Advance, Execute, or Planning-only mode:

1. Announce the current gate, evidence, intended action, and any material implementation decision.
2. Perform routine in-scope work autonomously.
3. Record durable decisions as described below.
4. Validate the changed artifact or implementation in proportion to risk.
5. Re-inspect the gate from repository state rather than assuming success.
6. Stop when the requested gate passes, a human decision is required, or a material risk needs authority.
7. Report changed files, validation evidence, decisions, and the new next action.

Never broaden "advance" into deployment, publication, destructive migration, credential changes, spending, or other consequential external actions without explicit authority.

## Surface decisions

Distinguish decisions from routine implementation details.

- Ask the user before settling product behavior, architecture boundaries, data-loss risk, security posture, major compatibility breaks, irreversible actions, or meaningful scope expansion.
- Make local and reversible engineering decisions when needed to progress, but announce them and explain the tradeoff.
- Tell the user about every material decision in session — what was decided, why, the alternatives considered, and the consequences. Do not write decisions to a decision log or create one.
- Do not reopen an accepted decision without new contradictory evidence.

## Use task and coordination tools safely

Read [tooling.md](references/tooling.md) whenever Beads, BV, task translation, task claiming, or multiple writers are involved.

- Use `br` as the task system of record when configured.
- Use only `bv --robot-*` modes; never run bare `bv`.
- Verify a BV recommendation against current Beads state before claiming it.
- Do not manually edit Beads SQLite or JSONL state.
- Keep one writer by default. Use parallel workers only when the user asks for delegation or repository instructions explicitly require it.
- When multiple writers are active, use the configured coordination system and file reservations before edits. If none exists, avoid overlapping writes.
- Do not install `br`, `bv`, Agent Mail, or any other system dependency without explicit user approval.

## Review independently

Treat review as evidence, not ceremony.

- Review plans for omissions, contradictions, unjustified complexity, failure behavior, security, operations, and testability.
- Review task graphs for missing traceability, vague acceptance criteria, incorrect dependencies, cycles, and oversized work.
- Review code against the task, accepted plan, tests, failure paths, and diff quality.
- Use a fresh-context reviewer when the user requests delegation and the host supports it. Otherwise perform an explicit adversarial pass and disclose that it was not independent.
- During planning, prefer the independent provider panel in the `multi-model-convergence-planning` skill; it is a normal workflow step rather than implementation delegation.
- Turn unresolved material findings into durable tasks; do not bury them in chat.

## Respond in a stable format

For Query mode, use:

```text
Current phase: <phase>
Gate: <passed | not passed | blocked>

Evidence:
- <specific repository evidence>

Next action: <one concrete action>
Why: <dependency or leverage explanation>

Decision needed: <none | one precise question with recommendation>
After that: <immediate subsequent step>
```

For action modes, lead with the outcome, then report:

- gate reached or blocker;
- files and task state changed;
- validation evidence;
- decisions made or requested;
- the single next action.

Keep the user-facing explanation non-technical unless technical detail changes a decision.
