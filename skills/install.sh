#!/usr/bin/env bash
# Symlink the skills in this directory into Claude, Codex, and Grok.
# Idempotent: re-running just refreshes the links. A pre-existing real directory
# (not a symlink) is moved aside to "<name>.bak.<pid>" rather than deleted.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.grok/skills")

for target in "${TARGETS[@]}"; do
  mkdir -p "$target"
  for skill in "$ROOT"/*/; do
    name="$(basename "$skill")"
    if [ ! -f "$skill/SKILL.md" ]; then
      continue
    fi
    link="$target/$name"
    if [ -e "$link" ] && [ ! -L "$link" ]; then
      mv "$link" "$link.bak.$$"
      echo "backed up existing $link -> $link.bak.$$"
    fi
    ln -sfn "$ROOT/$name" "$link"
    echo "linked $link -> $ROOT/$name"
  done
done
