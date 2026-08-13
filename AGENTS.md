# Agent Instructions

- Engineering exellence and correctness, matter a lot. Let the user know if you see a mistake, or an opportunity for elegant refactor, even if not in your scope.

- Backward compabilitiy is not always desired. If something feels outdated, or causes a massive workaround, consider suggesting to user about a refactor.

- Tell user about decisions you've made. If you make a silent decision that causes issues down the track, the fault can be assigned to you, so avoid this and always tell a user about your decisions.

- Avoid default configs in favour of explicit configs, until you're told otherwise.

- My attitude towards secrets differ from industry standards. I prefer: 
  - if a key directly controls money more than $100 -> encrypt at rest, do not commit
  - if repo is private -> can commit
  - if repo is public -> do not commit