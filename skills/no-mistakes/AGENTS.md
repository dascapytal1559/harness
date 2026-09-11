# no-mistakes Skill

- Canonical source: `kunchenguid/no-mistakes`, under `skills/no-mistakes`. The same text is embedded in the `no-mistakes` binary.
- `no-mistakes init` rewrites `SKILL.md` unconditionally, following symlinks, so the copy here is overwritten with the installed binary's version whenever `init` runs. That is the intended sync path: keep the binary current with `no-mistakes update`, then re-run `init` in any repo.
- Do not hand-edit `SKILL.md`. Local edits are lost on the next `init`; propose changes upstream instead.
- After an overwrite, verify the diff against `upstream.yaml`'s pin and advance the pin to the matching release tag.
