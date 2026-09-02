#!/usr/bin/env bash
# Deploy GLOBAL_AGENTS.md as the global agent instructions for Claude
# (default home and every profile under ~/.claude-profiles), Codex, and Grok,
# by symlinking each CLI's global instructions file directly at it.
# Idempotent: re-running refreshes the links. A pre-existing real file
# (not a symlink) is moved aside to "<name>.bak.<pid>" rather than deleted.
#
# Hosts that compose GLOBAL_AGENTS.md with host-specific extras (e.g. zdata's
# FINAL_AGENTS.md) have their own installer — do not run this one there.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/GLOBAL_AGENTS.md"

LINKS=(
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.codex/AGENTS.md"
  "$HOME/.grok/AGENTS.md"
)
for profile in "$HOME"/.claude-profiles/*/; do
  [ -d "$profile" ] && LINKS+=("${profile%/}/CLAUDE.md")
done

for link in "${LINKS[@]}"; do
  mkdir -p "$(dirname "$link")"
  if [ -e "$link" ] && [ ! -L "$link" ]; then
    mv "$link" "$link.bak.$$"
    echo "backed up existing $link -> $link.bak.$$"
  fi
  ln -sfn "$SRC" "$link"
  echo "linked $link -> $SRC"
done
