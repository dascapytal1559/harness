# Upstream Integrity

This document is the synchronization waypoint for the Flywheel Conductor. It records what upstream material the skills are based on, where this implementation intentionally differs, and how an agent must evaluate future upstream changes.

## Integrity contract

- Do not describe the Conductor as a verbatim ACFS implementation.
- Do not silently absorb an upstream change or silently erase a local deviation.
- Preserve human product intent and accepted local decisions when updating methodology.
- Update a baseline revision only after the corresponding changes are reviewed, applied where appropriate, and validated.
- Append sync outcomes; do not rewrite history to make old decisions appear inevitable.

## Current upstream baseline

Baseline captured: 2026-08-12

| Upstream | Role in this project | Pinned baseline | Observation |
|---|---|---|---|
| [Agentic Coding Flywheel Setup](https://github.com/Dicklesworthstone/agentic_coding_flywheel_setup) | Host-tooling and compatibility reference | Stable tag `v0.7.0`, peeled commit `edaee4f6ceff772d4f56d42eda65b1d659fead73` | Upstream `main` was `7f998de52a563b9aff84a6ee5bed57240b0f6c46` when captured. The Conductor does not vendor ACFS. |
| [Agent Flywheel planning skill](https://github.com/Dicklesworthstone/agent_flywheel_clawdbot_skills_and_integrations/blob/main/skills/planning-workflow/SKILL.md) | Primary prompt/workflow lineage for plan refinement and multi-model blending | Repository commit `6bdac0a0c18c86b8d2545d5bf50baf4d44027467` | Track the `planning-workflow`, `beads-workflow`, and related methodology skills when syncing. |
| [Complete Flywheel Guide](https://agent-flywheel.com/complete-guide) | Published end-to-end methodology | Page stated “Last reviewed July 17, 2026”; retrieved 2026-08-12 | The website has no immutable release identifier. Archive material changes or record a content hash during a future sync if reproducibility requires it. |
| [CASS competing proposal plans](https://github.com/Dicklesworthstone/cass_memory_system/tree/main/competing_proposal_plans) | Public evidence for independent multi-model proposals | Observed 2026-08-12 | Used as behavioral evidence, not vendored source. |

The ACFS tag is a compatibility baseline, not a claim that it versions the website or planning-skill repository. These upstreams evolve independently.

## Intentional deviations

### DEV-001 — Desktop session as control surface

- **Upstream behavior:** The reference environment is terminal- and VPS-oriented, with operators directly invoking the Flywheel toolchain.
- **Conductor behavior:** The active desktop session derives the next gate from repository evidence, serves as primary planner and synthesis owner, and drives routine steps for the user.
- **Reason:** The product goal is a non-terminal workflow without discarding durable Flywheel state.
- **Sync rule:** Retain unless upstream introduces a stronger host-neutral conductor abstraction that satisfies the same desktop requirement.

### DEV-002 — Session-primary planning with automated cross-model challenge

- **Upstream behavior:** The documented workflow uses a designated frontier model, currently GPT-5.6 Sol Pro in ChatGPT Pro, for the initial plan and synthesis, and commonly involves manually moving plans between model web apps and coding agents.
- **Conductor behavior:** The active session becomes the primary planner and synthesis owner. It automatically dispatches the same immutable planning packet to installed provider families other than its own; guided copy-and-import is fallback behavior.
- **Reason:** Session ownership preserves the user's product dialogue and removes the fixed-planner integration burden. Cross-model alternatives retain the method's independent challenge without requiring another coordination channel.
- **Sync rule:** Adapt new upstream planning roles and prompts to the provider adapter; do not regress to manual-first operation without an explicit decision.

### DEV-003 — Transparent exhaustive audits

- **Upstream behavior:** The “overshoot mismatch hunt” may tell a model that it missed a large invented number of issues to prolong its search.
- **Conductor behavior:** Use a visible coverage matrix, proposal traceability, fresh contexts, and convergence status without making a false factual assertion.
- **Reason:** Repeated deception can erode operator trust and makes the audit criterion less reproducible.
- **Sync rule:** Adopt stronger exhaustive-review mechanisms from upstream, but retain the prohibition on fabricated claims unless explicitly reconsidered by the user.

### DEV-004 — Depth follows risk, not line count

- **Upstream behavior:** Examples and guidance often celebrate plans several thousand lines long.
- **Conductor behavior:** Require complete decisions and traceability while scaling detail to project size, novelty, and risk. Length is an outcome rather than a gate.
- **Reason:** A line-count target can reward repetition and obscure whether the plan is actually executable.
- **Sync rule:** Adopt useful coverage requirements and examples; do not introduce a minimum plan length.

### DEV-005 — Host dependencies are adapters, not skill payload

- **Upstream behavior:** ACFS installs and configures the broader toolchain as an environment.
- **Conductor behavior:** Detect `br`, `bv`, and provider CLIs; guide the user to install missing tools instead of bundling or silently installing executables with the skill.
- **Reason:** A skill ships instructions and helper scripts, not host toolchain installation.
- **Sync rule:** Re-evaluate if a host gains a supported, consentful dependency mechanism. Until then, retain external installation.

### DEV-006 — Shared user-level skill source, repository-local project state

- **Upstream behavior:** Workflow skills and ACFS configuration may be installed through their own environment-specific mechanisms.
- **Conductor behavior:** Keep canonical skill sources in this repository (`skills/flywheel-conductor` and `skills/multi-model-convergence-planning`). Expose the same directories through `~/.claude/skills`, `~/.codex/skills`, and `~/.grok/skills`; keep briefs, plans, decisions, Beads data, code, and verification evidence inside each work repository.
- **Reason:** Workflow knowledge should be reusable across projects and hosts without divergent copies, while product state remains portable and versioned with its project.
- **Sync rule:** Do not reintroduce a plugin or marketplace wrapper unless a host cannot discover plain user skills.

### DEV-007 — Explicit human decision docket and bounded rebuttal

- **Upstream behavior:** Human judgment is central during initial planning and is implicitly invited when the integration critic reports wholehearted, partial, and disputed agreement. The documented models exchange artifacts through the human operator rather than holding a direct debate.
- **Conductor behavior:** Material synthesis disagreements are made explicit in `DECISION_DOCKET.md` before the canonical plan is finalized. Technical disputes may receive one focused rebuttal round; product taste, value, and consequential architecture choices return to the user.
- **Reason:** Desktop automation must not erase the human intervention that the manual upstream workflow naturally creates while moving artifacts between applications.
- **Sync rule:** Adopt stronger upstream decision protocols when available, but retain an explicit human checkpoint and never substitute model consensus for product authority.

## Upstream synchronization procedure

When asked to “sync the Conductor with upstream ACFS”:

1. Read `AGENTS.md`, this document, and the current `flywheel-conductor` and `multi-model-convergence-planning` skills before inspecting upstream.
2. Resolve the latest stable ACFS release and current revisions of every upstream listed above. Use exact commit SHAs or content hashes where possible; do not rely only on mutable branch names.
3. Compare only relevant surfaces: installation/capability expectations, planning workflow and prompts, plan-to-Beads translation, graph review, execution coordination, and ship/learning gates.
4. Produce a proposed change set in four classes:
   - **Adopt** — compatible upstream improvement with no local conflict.
   - **Adapt** — useful upstream improvement requiring desktop-session translation.
   - **Retain deviation** — upstream differs, but the documented local choice still applies.
   - **Not applicable** — upstream change lies outside the Conductor's scope.
5. Surface any change that would alter product behavior, safety, provider cost, compatibility, or an accepted deviation before implementing it.
6. Update the skills, validate them, and exercise affected deterministic scripts. Do not update the baseline table yet if validation fails.
7. Update this document's baseline and deviation statuses, append a sync-history entry, and record a new decision when policy changed.
8. Confirm the user-level skill symlinks still point at this repository, then test from a new desktop session.

## Sync history

### 2026-08-12 — Baseline established

- Pinned ACFS stable `v0.7.0` and recorded the then-current `main` revision.
- Pinned the upstream skills repository revision used to assess the planning workflow.
- Recorded the website review date and CASS proposal corpus as unversioned behavioral evidence.
- Established six intentional deviations for desktop control, automated planning, audit integrity, plan sizing, host dependencies, and installation scope.
- Added an explicit decision-docket adaptation after confirming that upstream synthesis relies on human-mediated integration rather than direct model debate.

### 2026-08-12 — Session-primary planning locked in

- Replaced the fixed GPT/Codex primary-planner substitution with the active session agent.
- Kept competing plans independent by excluding the session's provider family from the automated alternative panel.
- Preserved human authority through the existing decision docket and kept Agent Mail outside the planning handoff.

### 2026-08-12 — Claude skill exposure added

- Linked Claude's user-level `flywheel-conductor` skill entry to the canonical plugin skill directory.
- Avoided a second physical copy so Codex and Claude use the same workflow instructions.

### 2026-08-13 — Multi-model planning extracted

- Moved packet construction, isolated alternative dispatch, synthesis, the decision docket, rebuttal, and the convergence audit into the sibling skill `multi-model-convergence-planning`.
- Left the Conductor as control surface and primary planner; it now loads the sibling skill instead of owning the planning procedure inline.
- Linked Claude's user-level `multi-model-convergence-planning` skill entry to the new canonical skill directory.

### 2026-08-13 — Plugin layer removed

- Extracted `flywheel-conductor` and `multi-model-convergence-planning` from the Codex plugin wrapper into the user skills repository.
- Replaced marketplace/plugin installation with the existing per-host skill symlink convention.
- Moved this ledger with the Conductor skill so methodology history stays next to the workflow it describes.

### 2026-08-13 — Skills returned to harness

- Moved `flywheel-conductor` and `multi-model-convergence-planning` back into this repository at `skills/`.
- Relocated the unrelated user-skills repository to `~/Projects/basedcapital/skills`.
