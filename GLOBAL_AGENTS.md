# Agent Instructions

Only human can edit GLOBAL_AGENTS.md, agents can only suggest.

## Coding & planning
- Engineering exellence and correctness, matter a lot. Let the user know if you see a mistake, or an opportunity for elegant refactor, even if not in your scope.
- Elegance often trump backward compatibility. If you see an opportunity, point it out.
- Tell user about decisions you've made. If you make a silent decision that causes issues down the track, the fault can be assigned to you, so avoid this and always tell a user about your decisions.
- Avoid default configs in favour of explicit configs, until you're told otherwise.

## My attitude towards secrets differ from industry standards. I prefer: 
- if a key directly controls money more than $100 -> encrypt at rest, do not commit
- if repo is private -> can commit
- if repo is public -> do not commit

## For any relevant directory (repo root or subtree):
- `AGENTS.md` — for agents: directives, workflows, hard rules. The only file with authority; agents obey it over defaults.
- `CLAUDE.md` — a symlink to AGENTS.md (so Claude Code auto-loads it).
- `README.md` — for humans: what the thing is and how it's wired. Never put agent directives here, and never let it contradict AGENTS.md.

Auto-load only covers the repo a session starts in. When work spans repos, AGENTS.md must name the other repo's AGENTS.md explicitly (e.g. "before touching ~/X, read ~/X/AGENTS.md").
