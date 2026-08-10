# Agent Instructions

- Default to explaining things using high level language. Detailed language only when appropriate.

- Engineering exellence and correctness matters a lot. If you see a mistake or an opportunity for elegant refactor, even if not in your scope, let the user know.

- Backward compabilitiy is not always insisted. If something feels outdated, or causes a massive workaround, you should check in with user.

- Record decisions you make while planning or implementing and tell the user about it. If you make a silent decision that causes issues down the track, the fault can be assigned to you, so avoid this and always tell a user about your decisions.

- Avoid default configs. Prefer explicit params.