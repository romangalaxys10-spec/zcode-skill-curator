# Skill Curator

<p align="center">
  <a href="https://z.ai/subscribe?ic=R0K78RJKNW"><img alt="z.ai coding plans - 10% OFF coupon" src="https://img.shields.io/badge/z.ai%20coding%20plans-10%25%20OFF%20coupon-blueviolet" /></a>
  <a href="https://zcode.z.ai/invite/ALWM9JUA"><img alt="Try ZCode free" src="https://img.shields.io/badge/Try%20ZCode-free%20invite-0969da" /></a>
</p>

One-sentence pitch: keep your ZCode skill and plugin stack deduplicated, audit-healthy, and easy to extend, from a single slash command.

## Why

Skill collections grow in three places: `~/.zcode/skills`, `~/.agents/skills`, and the
plugin cache. Copies drift apart, the same skill lands twice from two sources,
imports bring broken script references, and nobody knows which copy is the live one.
Skill Curator scans all roots into one catalog, flags the problems, and gives an
install and remove path that shows every file before it touches the disk.

## How it works

| Step | What it does |
|---|---|
| LIST | Builds a catalog table: name, source, version, one-line description |
| SEARCH | Matches a capability phrase against the catalog (name, description, source) |
| AUDIT | Flags duplicate names, stale `scripts/*` references, missing frontmatter |
| DEDUPE | Shows which copies share a name and proposes keep-one-remove-rest |
| INSTALL | Copies a marketplace folder or unpacked zip into `~/.zcode/skills` after a dry-run file list |
| REMOVE | Backs up the whole skill dir to `~/.zcode/skill-curator-backups/`, then deletes only with `--yes` |

All operations run through one stdlib-only Python script:
`skills/skill-curator/scripts/skill_catalog.py`.

## Install

Option A: self-installable marketplace

1. Download or clone this repo into a folder.
2. In ZCode, open Plugin Marketplace, then Add, then Add Plugin Marketplace.
3. Paste the folder path, wait for it to load, then Install `skill-curator`.

Option B: manual copy

Copy the `skill-curator` folder into your workspace `plugins/` directory,
then restart ZCode so the plugin is picked up.

## Try it

```
/skill-curator list
```

Expected: a markdown table of every skill found across `~/.zcode/skills`,
`~/.agents/skills` and the plugin cache, with a duplicate and audit-flag
section when issues exist. Then:

```
/skill-curator audit
```

Expected: "Scanned N SKILL.md files", the list of duplicate names, and the
list of skills with missing frontmatter or stale script references. Exit
code 1 when anything is flagged, 0 when the catalog is clean.

## Requirements

Python 3 (stdlib only, no pip packages). macOS, Linux, or Windows.

---

<p align="center">
  <a href="https://z.ai/subscribe?ic=R0K78RJKNW"><img alt="z.ai coding plans - 10% OFF coupon" src="https://img.shields.io/badge/z.ai%20coding%20plans-10%25%20OFF%20coupon-blueviolet" /></a>
  <a href="https://zcode.z.ai/invite/ALWM9JUA"><img alt="Try ZCode free" src="https://img.shields.io/badge/Try%20ZCode-free%20invite-0969da" /></a>
</p>

## License

MIT
