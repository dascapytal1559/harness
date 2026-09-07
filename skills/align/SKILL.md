---
name: align
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round, then wait for the user's answers before the next round.

Every frontier decision goes to the user in one of two tiers. Sort each one honestly before you present it:

- A **question** is a decision you genuinely need the user's input on: the answer would materially change the design, is expensive to reverse, or you can't confidently pick between the options yourself.
- An **assumption** is a decision you _can_ confidently make yourself. Don't dress it up as a question. Make the call and put it on the round's assumption list for the user to challenge.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

After the questions, list this round's assumptions:

```
📌 **A1** - **<assumption title>**: <the call you're making, with a one-or-two-line rationale>
```

Number questions and assumptions continuously across rounds (Q1…Qn, A1…An) so the user can refer back to any of them.

The two tiers settle differently. A question stays open until the user answers. An assumption settles its node **immediately** (its children join the frontier without waiting), but the user may challenge any assumption, now or in a later round; a challenged assumption reopens as a question, and everything downstream of it goes back into the tree.

Each round the user's answers and challenges reshape the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, every decision either answered by the user or standing visibly on the assumption list, nothing left _silently_ assumed. Close with a recap of the full assumption list as the user's last chance to challenge. Do not act on it until the user confirms you have reached a shared understanding.
