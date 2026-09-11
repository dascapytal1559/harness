---
name: agent-ergonomics
description: Make a system legible and drivable for agents. Fresh-context probes drive it cold, session history says where it already hurt, and the design docs are rewritten as one tower of abstractions. Use when the user runs /agent-ergonomics, asks to make a repo or plan agent-intuitive, agent-ergonomic, or agent-accretive, or wants to check a project for ergonomic drift.
disable-model-invocation: true
---

Inspired by a Jeffrey Emanuel (@doodlestein) prompt.

You are not the driver. You have read the conversation, you know what everything was meant to be, and that knowledge is exactly what stops you from feeling the friction a cold agent feels. So the driver's seat goes to **probes**: fresh sub-agents that receive only the target and a task, attempt it, and log every place they had to guess. Your job is to read the system's **history**, send probes where it points, then synthesize what they felt into one **tower** of abstractions that the docs express and a ranked set of changes that remove the friction. Report first, apply on confirmation, verify with one more probe.

## Vocabulary

- **Target**: the system being reviewed. A repo, a plan, a CLI, a skill set, this harness. Default is the current repo.
- **Tower**: the layered map of the target as an agent sees it, top to bottom: purpose, the concepts it is made of, the surfaces you touch (docs, commands, files, signals), and what each surface sits on. Every layer names where it is documented and what links it to its neighbours. The tower lives in the target's "how it is wired" doc, README by default.
- **Layer**: one level of the tower. Friction is always reported against a layer.
- **Lens**: one of six questions asked of every layer. Legibility: can the agent see the state accurately? Controllability: can it act precisely in few steps? Verifiability: can it confirm the effect? Economy: how many tokens, calls, and re-reads does that cost? Accretion: does its work compound, and is there a place to leave knowledge behind? Coherence: is this one system or an assemblage?
- **Probe**: a fresh sub-agent given a task, cold. Its report is the evidence.
- **Instrument**: how a probe measures. **Drive**: run and inspect a system that exists. **Tabletop**: walk a task through a plan that is only written, using nothing but the page. **History**: past session transcripts, mined by the script, no tokens spent.
- **Friction event**: one moment a probe needed something and had to search, guess, re-derive, or hold ambiguity.
- **Carve-out**: a rule the user insists on. Every rule in the target's AGENTS.md is one. Carve-outs outrank ergonomics.
- **Drift**: the gap between the tower in the docs and the target as it is now, plus friction that appeared since the tower was last written.
- **Placement tier**: where a piece of knowledge is written down. Always-loaded (AGENTS.md) for rules of conduct only. On-demand docs (README, nested docs, path-scoped rules) for the tower and the wiring. Nowhere, for anything one command reveals.

## The three cases

1. **New**: the repo is empty or nearly so. Intent lives in the conversation and the arguments. Draft the to-be tower and doc layout in a temporary location outside the repo, tabletop-probe that draft, and report it as proposed files. Nothing is written into the repo before confirmation. If the intent is too thin to derive even one task, ask. This is the one case a question is unavoidable.
2. **First alignment**: an existing target with no tower in its docs. Drive it, build the tower, propose.
3. **Re-alignment**: a tower already exists. Everything above, plus the Drift section. "Since last alignment" is the git date of the tower's last change; history since then is the drift evidence.

A target can be mixed: a plan for changing an existing system. Each probe then both drives the current system and tabletops the plan for the same task, reporting the two separately. The budget stays at one probe per task.

## Arguments

Free text. It may carry any of: a target pointer; explicit probe tasks, used verbatim; a budget word, "quick" for one probe, "thorough" for five, default three; per-run carve-outs the user settled in this session and has not written down yet. When a carve-out arrives this way the report includes a suggested AGENTS.md diff recording it, so the next run inherits it.

## Procedure

### 1. Orient

Read the target's AGENTS.md: that is the carve-out set. Locate the tower if one exists: the README or whichever doc the target uses for how it is wired. Decide which of the three cases applies. Then run the history instrument:

```
python3 <this skill's directory>/scripts/mine_transcripts.py --target <path> [--since <ISO date of the tower's last change>]
```

It reports, for this target's past Claude and Codex sessions: files re-read within a session and across sessions, searches repeated across sessions, failing commands, reads of files that no longer exist, and hook errors. It says which transcript stores it found. Treat its counts as questions to investigate, never as verdicts.

Skim the target only enough to choose tasks. Do not write the tower yet.

### 2. Choose tasks

Pick the tasks the target most obviously exists to support, as many as the budget allows. History steers the choice: send probes where it shows repeated friction. Tasks given in the arguments are used verbatim. Do not pause for approval; the chosen tasks appear in the report and the user can re-run with explicit ones.

A task is something a working agent would actually be asked to do here, phrased as that agent would receive it. "Add a new skill and get it installed on all three CLIs" is a task. "Evaluate the docs" is not.

### 3. Launch probes

One fresh sub-agent per task, whatever your host calls that. Each probe receives only the text below, filled in. Never the conversation, never your reading of the system. Probes never mutate the target: use worktree isolation if the host offers it, otherwise the probe is limited to reading and non-mutating commands such as tests, dry runs, and help output.

```
You are working cold in <target path>. Your task: <task>.

<If tabletop: The system does not exist yet. The plan is at <path>. Using only the plan, walk through exactly how you would do the task, step by step, and where the plan leaves you guessing.>

Attempt the task the way you normally would. Do not modify anything: read, run non-mutating commands, run tests and dry runs. Stop when you have done it, or when you would have to guess to continue, or after roughly 40 tool calls.

Report in exactly this shape:

TASK: <restated>
INSTRUMENT: drive | tabletop
STEPS: numbered, one line each, what you did and why
FRICTION: one block per event
  needed: what you had to know or do
  looked: where you looked, in order
  guessed: what you assumed, if anything
  cost: tool calls spent on this event
  layer: the doc, command, file, or concept this is about
OUTCOME: done | gave up | done wrong (say what was wrong)
ONE THING: the single change that would have made this task trivial
```

### 4. Synthesize

Now, with the probe reports and the history in hand, do the deep work.

- **Write the tower.** Top to bottom. For each layer: what it is, where it is documented, what it sits on, what links it to its neighbours. Mark every place a probe fell through a missing link. A target with no discernible layering gets, as its first proposal, a tower to create.
- **Group friction** by layer, then by lens. Weight each finding by how many probes hit it and how badly: gave up outranks done wrong outranks done slowly.
- **Diff for drift** on re-alignments: parts of the target not in the tower, tower entries that no longer exist, friction absent last time.
- **Challenge carve-outs** that cost. For each carve-out with measured friction, state the cost across probes and the elegant change it blocks. These are suggested AGENTS.md diffs. They are never ranked as proposals, never applied, and never silently worked around.
- **Rank proposals** by friction removed per unit cost. Friction removed is probe hits times severity. Cost is the size and reversibility of the change. Each proposal names the friction it removes, the layer, the placement tier it writes to, and what it costs. Small doc fixes that unblock every probe rise to the top.
- **Apply the placement rule** to every proposal that writes text. Rules of conduct go always-loaded, and AGENTS.md stays under two hundred lines. The tower and the wiring go on demand. Anything a single command reveals is not written down at all.
- **Include the standing directive** as a suggested AGENTS.md diff whenever it is absent, see below.

Every proposal needs a probe finding or a direct inspection behind it. History alone is not enough.

### 5. Report

Fixed layout, in this order. Findings are grouped, short, and refer to layers by name.

1. **Tower**: the layered map, with the missing links marked.
2. **Friction**: by layer, then lens, with probe counts. Say which instrument each probe used and which tasks ran.
3. **Drift**: re-alignments only.
4. **Constraint challenges**: carve-outs with measured cost, as suggested AGENTS.md diffs.
5. **Proposals**: numbered, ranked, each with friction removed, layer, tier, and cost.
6. **Suggested AGENTS.md diffs**: the standing directive if absent, recorded carve-outs from the arguments, and any challenge the user may want to accept.

Then the gate: the user replies with proposal numbers or "all". Wait.

### 6. Apply

Apply the confirmed proposals. AGENTS.md is never edited by this skill; its items stay suggestions regardless of what the user selected. In the new case, write the proposed files into the repo now. Tell the user every judgment call made while applying.

### 7. Verify

Re-run one probe, cold, on the task that had the worst friction, against the changed target. Report whether that friction is gone, in the probe's own words. If it is not, say so plainly and propose the next change; do not apply it without confirmation.

## The standing directive

Suggested for the target's AGENTS.md whenever it is absent. Keep it this short:

```
- README holds this system's tower: its layers, what each sits on, and where each is documented. Any change that adds, removes, or renames a layer, command, or doc updates the tower in the same change. New things state which layer they belong to.
```

Drift will still happen. Re-alignment is the audit.

## Not this skill

- Product planning: what the system does. That is `align` for hashing out what the user insists on, and `wayfinder` for a plan too big for one session. Insistences settled there belong in AGENTS.md, where this skill reads them as carve-outs.
- Finding compensating layers in code: `linus-review`. Cite it when the tower shows one.
- Recording a decision with its context: `matts-domain-modeling` writes ADRs. Cite it when a layer wants one.
- Install-level economy: `/doctor` and `/skill-doctor` in Claude Code check unused skills, MCP servers, and CLAUDE.md size. Point at them when the target is the harness itself. Never invoke them; they are host-specific and interactive.

## Hard rules

- Probes are cold. Target, task, schema, nothing else.
- Probes never mutate.
- AGENTS.md is never edited. Suggest diffs.
- No new log or state files. Findings live in chat; accepted changes land in the target's existing docs. A target's first design doc is an ordinary proposal.
- Nothing is written before the gate.
- Every proposal is backed by a probe or a direct inspection.
- Every judgment call is told to the user.
