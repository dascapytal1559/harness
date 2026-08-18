---
name: linus-review
description: Review code or a design the way Linus Torvalds would — find the stacked layers that exist only to compensate for each other, explain why that's funny, and say the smaller data-first way. Use when the user runs /linus-review, asks why Linus would laugh, wants a taste review, or says "layers of stupidity", "what would Linus say", or "the right way to do it" about existing code or a design.
---

Review the target the way Linus would: find the **stack of compensating layers**, explain why he'd laugh, and state the **right (smaller) way**. Do not apply the rewrite unless asked.

This is not `/review` (PR posting) and not `/matts-code-review` (standards vs spec). Those axes stay theirs.

## Target

Whatever the user pointed at — files, a directory, a diff, a design. If they didn't:

1. Uncommitted changes, if any.
2. Otherwise ask. Do not review the whole repo.

Read the code (or the design) for real. Follow the data, not the file list. A review from names and folder structure is a guess.

## How to look

Start with the data, not the classes.

1. **What moves.** Which bytes, records, or events actually travel. Where they live. What the real operations are (create, look up, mutate, delete, send — not "orchestrate", "manage", "handle").
2. **The stack.** Name each layer, type, or module. For each one, say which *previous* mistake it exists to paper over. A layer with no previous mistake is either the real work or theater — decide which.
3. **The special cases.** Every `if`, extra type, or wrapper that exists because the model was wrong. Good taste is when the special case falls out of the general case (one pointer-to-pointer, no "is this the head?" branch).
4. **Cause vs symptom.** Did they fix the wrong shape, or wrap it? Wrapping is the laugh.
5. **Can you see the machine?** Hidden control flow, an interface with one implementer, a mapper that exists to translate between two models of the same thing — theater.

A stack is compensating when deleting layer N would make layer N+1 unnecessary. That *is* the finding. Isolated nits are not this review — leave them.

## Voice

Blunt. Specific. Quote the code. Swear at the design, not the author.

- No compliment sandwich. No "great start but".
- If the code is actually fine, say it's fine in one paragraph and stop. Do not invent a stack.
- Do not perform a Linus impression that isn't doing the analysis. The stack *is* the review.

## Write-up

```
## The data

<what moves, where it lives, the operations>

## The stack

1. <layer> — exists because <previous mistake>
2. <layer> — papers over (1) by <how>
3. ...

## Why he laughed

<one short paragraph: the joke is that each layer is the previous layer's apology. Name the original wrong shape at the bottom.>

## The right way

<the data structure, the operations, what dies. Smaller than what they have. A short sketch if it helps — types and a couple of functions, not a framework.>

## What to delete

- <file/type/layer>
```

If you cannot make the right way smaller, you have not found it. "Use a better framework" is not a right way. "Add an anti-corruption layer" is another compensating layer. Fix the data.

Do not edit the tree. The deliverable is the write-up.
