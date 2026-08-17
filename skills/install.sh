#!/usr/bin/env bash
# Symlink the skills in this directory into Claude (default home and every
# profile under ~/.claude-profiles), Codex, and Grok.
# Idempotent: re-running refreshes the links and prunes stale ones — any
# symlink pointing into this directory whose skill no longer exists is
# removed, so deletions and renames propagate. A pre-existing real directory
# (not a symlink) is moved aside to "<name>.bak.<pid>" rather than deleted.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.grok/skills")
for profile in "$HOME"/.claude-profiles/*/; do
  [ -d "$profile" ] && TARGETS+=("${profile%/}/skills")
done

for target in "${TARGETS[@]}"; do
  mkdir -p "$target"

  # Prune: drop symlinks that point into $ROOT but whose target is gone.
  for link in "$target"/*; do
    [ -L "$link" ] || continue
    dest="$(readlink "$link")"
    case "$dest" in
      "$ROOT"/*)
        if [ ! -f "$dest/SKILL.md" ]; then
          rm "$link"
          echo "pruned $link -> $dest"
        fi
        ;;
    esac
  done

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
