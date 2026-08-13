# Flywheel Gates

Use these gates as a state machine, not as a heavyweight checklist. Apply only criteria material to the project's size and risk. A prototype may satisfy a criterion in a few lines; a production system may require a dedicated artifact and evidence.

## 1. Foundation

Pass when durable repository state identifies:

- the product goal, intended user, and primary workflows;
- explicit scope boundaries and constraints;
- the chosen stack and important architecture boundaries;
- build, test, lint, and run instructions that match the repository;
- engineering, safety, compatibility, and Git rules;
- where accepted decisions are recorded.

For a new project or material feature, preserve the product intent in `docs/planning/PROJECT_BRIEF.md` and assemble the immutable evidence sent to planning providers in `docs/planning/PLANNING_PACKET.md`. Equivalent repository conventions are acceptable when they are explicit. The planning procedure lives in the `multi-model-convergence-planning` skill.

Do not pass based only on package metadata or inferred intent.

## 2. Plan

Pass when an implementable plan explains:

- user-visible behavior and acceptance outcomes;
- important state, data flows, and component responsibilities;
- external dependencies and explicit configuration;
- error, retry, rollback, and recovery behavior where relevant;
- security, privacy, migration, and operational implications where relevant;
- verification strategy and intended sequence.

For non-trivial work, also require:

- a preserved initial plan authored by the active Conductor session before it reads alternatives;
- independent alternative proposals from other model families, normally the two of Claude, Codex, and Grok that differ from the active session when their host CLIs are available;
- the planning-packet hash and provider/version metadata for each proposal round;
- a synthesis record explaining material ideas accepted, adapted, or rejected.
- a decision docket whose material product, architecture, risk, compatibility, and scope choices are resolved by the human;
- one canonical synthesized plan rather than a concatenation of proposals, updated only after the decision docket is resolved.

Small, local, or low-risk work may skip the panel when its overhead exceeds its decision value. Record that judgment and rationale rather than silently treating a single-model draft as triangulated. Run the panel through the `multi-model-convergence-planning` skill.

Do not demand irrelevant production machinery from a prototype.

## 3. Plan refinement

Pass when fresh critical review has challenged the plan, the planning coverage matrix is complete, and every material finding is resolved, accepted as a documented risk, or represented by tracked work. Preserve proposals, synthesis decisions, refinement evidence, and the convergence judgment in repository artifacts or task records.

A review performed by the author in the same context is useful but not independent. State that limitation.

## 4. Task translation

Pass when the accepted plan is represented by bounded work items with:

- enough context to execute without reconstructing the planning conversation;
- an explicit deliverable and testable acceptance criteria;
- likely subsystem or edit surface;
- required verification;
- dependencies and links back to the motivating plan section or decision.

Every material plan element must map to work, and every work item must be justified by the plan.

## 5. Task-graph validation

Pass when:

- no unresolved dependency cycles exist;
- ready work is genuinely unblocked;
- no material work is orphaned or duplicated;
- priorities reflect user value, risk, and graph leverage;
- task sizes fit a bounded implementation context;
- integration, documentation, migration, and hardening work are represented.

## 6. Execution readiness

Pass when:

- at least one task is ready with complete acceptance criteria, unless all work is complete;
- baseline build and tests are known, including any pre-existing failures;
- required dependencies and explicit local configuration are available;
- the working tree is understood and user-owned changes are protected;
- coordination and file-ownership rules are clear for every active writer.

## 7. Execution

This gate advances one bounded task at a time. For each task:

1. Confirm it is current and ready.
2. Claim it and reserve its edit surface when coordination is active.
3. Implement only the accepted scope.
4. Run the required checks and inspect the diff.
5. Record newly discovered work and material decisions.
6. Close the task only when its acceptance criteria pass.
7. Release reservations and re-run triage.

An implementation failure leaves the task open or blocked with evidence; it does not justify weakening acceptance criteria silently.

## 8. Review and hardening

Pass when proportionate evidence covers:

- fresh code review or an explicitly disclosed self-review;
- integration and important failure paths;
- security, privacy, migration, rollback, and operational risks where relevant;
- documentation accuracy;
- plan-versus-implementation reconciliation;
- unresolved-work and repository-state scans.

Material findings must be fixed, accepted as documented risk, or tracked.

## 9. Ship and learn

Pass when:

- product acceptance criteria pass;
- required build, tests, lint, and release checks pass;
- no unexplained changes or unfinished release-critical tasks remain;
- operational and rollback readiness is adequate for the target environment;
- documentation and task state describe reality;
- decisions and newly discovered follow-up work are durable;
- any actual release or deployment has explicit user authority.

Do not equate "code complete" with "shipped." If deployment is outside scope, report the repository as ship-ready rather than shipped.
