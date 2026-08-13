# Flywheel Tooling Adapter

Read this reference only when task-graph or multi-writer coordination is relevant.

## Detect capabilities

Inspect rather than assume:

```sh
command -v br
command -v bv
test -d .beads
```

Interpret the combinations explicitly:

- `.beads/` and `br`: use Beads normally.
- `.beads/` without `br`: inspect tracked JSONL only as read-only evidence; do not edit Beads files manually. Report that the CLI is unavailable.
- `br` without `.beads/`: planning may continue, but ask before initializing Beads because initialization changes repository state.
- neither: use repository artifacts through the Plan gates. At Task translation, recommend installing and initializing Beads, but do not install tools without approval.
- `bv` without current Beads data: do not use BV as evidence.

## Read task state

Prefer machine-readable commands:

```sh
RUST_LOG=error br ready --json
RUST_LOG=error br blocked --json
RUST_LOG=error br list --status in_progress --json
RUST_LOG=error br coordination status --json
```

When `bv` exists, use:

```sh
bv --robot-triage
bv --robot-next
```

Never run bare `bv`; it launches an interactive interface. Treat BV as a recommender, not the task system of record. Confirm the chosen ID is still ready with `br ready --json`, then inspect it with `br show <id> --json`.

## Translate an accepted plan

Create tasks only in Advance or Planning-only mode after the plan is accepted. Use explicit type and priority; do not rely on defaults.

```sh
RUST_LOG=error br create "<title>" --type <type> --priority <0-4> --json
RUST_LOG=error br dep add <issue> <depends-on>
```

Put execution context, deliverable, acceptance criteria, verification, plan/decision references, and likely edit surface into fields supported by the installed `br` version. Discover current flags with `br capabilities --format json --command "create"` or `br create --help`; do not guess unsupported flags.

Dependency direction is: `<issue>` cannot start until `<depends-on>` closes. Validate direction after adding edges.

## Execute one task

Use the installed version's capabilities to preserve explicit state transitions:

```sh
RUST_LOG=error br show <id> --json
RUST_LOG=error br update <id> --status in_progress --json
# implement and verify
RUST_LOG=error br close <id> --reason "<acceptance evidence>" --json
RUST_LOG=error br sync --flush-only
```

Do not close a task when checks fail, acceptance criteria remain incomplete, or a dependency cycle is unresolved. Record a blocker or discovered task using supported Beads fields instead.

Beads never substitutes for Git review. Inspect source and `.beads/` diffs. Do not commit, push, merge, or deploy unless separately authorized or required by applicable repository instructions.

## Coordinate multiple writers

Beads tracks work; the repository's coordination system tracks communication and file reservations. Use the bead ID as the shared thread and reservation reason.

Before writing:

1. Confirm the bead is ready and assigned.
2. Register or identify the worker using the configured coordination tool.
3. Reserve the narrowest practical file patterns.
4. Announce start under the bead ID.

After work:

1. Report validation and any new blockers in the same thread.
2. Close or update the bead.
3. Release reservations.
4. Re-run ready state and graph triage.

If no coordination tool is configured, serialize overlapping edits. Never pretend a reservation exists.
