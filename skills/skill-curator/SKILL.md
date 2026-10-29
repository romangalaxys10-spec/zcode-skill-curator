---
name: skill-curator
description: "Use when the user wants to inventory their installed ZCode skills/plugins, find a capability by name, check for duplicate or broken skill installations, install a new skill from a marketplace folder or repo zip, or remove a skill safely. Triggers: 'list my skills', 'find a skill that does X', 'audit skills', 'dedupe skills', 'install this skill zip', 'remove the foo skill'."
---

# Skill Curator

Manage the local ZCode skill ecosystem: catalog, search, audit, dedupe, install, remove.

The catalog lives at `scripts/skill_catalog.py` (relative to this skill dir). It is
Python 3 stdlib only and works on macOS/Linux/Windows.

Default scan roots (override or extend with `--dirs`):

- `~/.zcode/skills` (user skills)
- `~/.agents/skills` (agent skills)
- `~/.zcode/cli/plugins/cache` (installed plugin cache)

## Workflow

### 1. LIST

Build the local catalog and show it:

```bash
python3 scripts/skill_catalog.py list
```

Output is a markdown table: name, source (user / agents / plugin-cache), version
(if parseable from frontmatter), one-line description from the `description`
frontmatter field. Duplicates and audit flags are appended at the bottom.
Use `--json` for machine-readable output.

### 2. SEARCH

Match a user query (capability phrase, keyword, skill name) against the catalog:

```bash
python3 scripts/skill_catalog.py search "kubectl"
```

Matching covers skill name, description, and source path. If the user asks for
something no local skill covers, say so plainly and suggest where it could be
obtained (a marketplace install, step 4).

### 3. AUDIT

Flag three issue classes:

- duplicate names (same skill name from two sources, e.g. a user copy and a
  plugin cache copy).
- stale references: SKILL.md mentions `scripts/foo.py` that does not exist next to it.
- missing frontmatter: no `---` block, no `name`, or no/empty `description`.

```bash
python3 scripts/skill_catalog.py audit
```

Exit code 1 means issues were found; 0 means the catalog is clean.
Use `dedupe` for a removal-plan view:

```bash
python3 scripts/skill_catalog.py dedupe
```

Keep the copy without issues (plugin cache copies usually win over loose user
copies); the rest are candidates for step 5.

### 4. INSTALL

From a marketplace folder or a repo zip.

1. Unpack or point at the source. A valid skill source is any folder containing
   `SKILL.md` with `name` frontmatter, optionally with `scripts/` next to it.
   For a zip: `unzip <file>.zip -d /tmp/skill-install/<name>`.
2. Dry-run first: show exactly which files land where.

   ```bash
   python3 - <<'PY'
   from pathlib import Path
   src = Path("<src-dir>")
   dst = Path.home() / ".zcode" / "skills" / src.name
   print(f"Install {src} -> {dst}")
   for f in sorted(p for p in src.rglob('*') if p.is_file()):
        print(f"  {f.relative_to(src)}")
   PY
   ```

3. Only after the user confirms the file list, copy:

   ```bash
   cp -R <src-dir> ~/.zcode/skills/<name>
   ```

4. Verify: `python3 scripts/skill_catalog.py list | grep <name>` and re-run
   `audit` to confirm no stale references were imported.

Honest limits: this copies files. It does not run installers, and it does not
register the skill with ZCode; ZCode picks up `~/.zcode/skills/<name>/SKILL.md`
on its next session. A skill that bundles its own config or credentials still
needs those set up by the user.

### 5. REMOVE

Never delete without explicit user confirmation in this session. Always back up first.

```bash
# 1. dry run: show what would move
python3 scripts/skill_catalog.py remove --path ~/.zcode/skills/<name> --dry-run

# 2. get user confirmation on the printed file list

# 3. execute (backup lands in ~/.zcode/skill-curator-backups/<timestamp>/)
python3 scripts/skill_catalog.py remove --path ~/.zcode/skills/<name> --yes
```

The script refuses to delete without `--yes`, and `--yes` must follow an
explicit confirmation from the user in this session. If the user did not confirm,
stop at the dry-run and ask.

## Output format

Always state: what was scanned (roots), how many skills, what was found or
flagged, and what the user should do next (keep, remove, install). One short
bullet list, no filler.
