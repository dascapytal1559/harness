- Only human can edit this particular AGENTS.md, agents can only suggest.
- Communicate in plain language
- Engineering exellence and correctness, matter a lot. Let the user know if you see a mistake, or an opportunity for elegant refactor, even if not in your scope.
- Elegance often trump backward compatibility. If you see an opportunity, point it out.
- Tell user about decisions you've made. If you make a silent decision that causes issues down the track, the fault can be assigned to you, so avoid this and always tell a user about your decisions.
- Avoid default configs in favour of explicit configs, until you're told otherwise.

## For any relevant directory (repo root or subtree):
- `AGENTS.md` — for agents: directives, workflows, hard rules. The only file with authority; agents obey it over defaults.
- `CLAUDE.md` — a symlink to AGENTS.md (so Claude Code auto-loads it).
- `README.md` — for humans: what the thing is and how it's wired. Never put agent directives here, and never let it contradict AGENTS.md.
