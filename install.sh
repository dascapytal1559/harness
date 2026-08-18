#!/usr/bin/env bash
# Build FINAL_AGENTS.md = AGENTS.md + EXTRA_AGENTS.md (host-local, optional)
# and symlink it into every agent's global instruction path.
#
# Idempotent — rerun after `git pull` or after editing either source file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FINAL="$ROOT/FINAL_AGENTS.md"

{
  cat "$ROOT/AGENTS.md"
  if [ -f "$ROOT/EXTRA_AGENTS.md" ]; then
    printf '\n---\n\n'
    cat "$ROOT/EXTRA_AGENTS.md"
  fi
} > "$FINAL"

# agent global instruction destinations
DESTS=(
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.codex/AGENTS.md"
  "$HOME/.grok/AGENTS.md"
)

for dest in "${DESTS[@]}"; do
  mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    mv "$dest" "$dest.bak.$$"
    echo "backed up existing $dest -> $dest.bak.$$"
  fi
  ln -sfn "$FINAL" "$dest"
  echo "linked $dest -> $FINAL"
done

echo "built $FINAL ($(wc -l < "$FINAL") lines$([ -f "$ROOT/EXTRA_AGENTS.md" ] && echo ', with EXTRA_AGENTS.md' || echo ', no EXTRA_AGENTS.md'))"
