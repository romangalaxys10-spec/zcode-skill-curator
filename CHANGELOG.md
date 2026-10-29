# Changelog

## 0.1.0 - 2026-10-29

- Initial release: catalog skill list across `~/.zcode/skills`, `~/.agents/skills`, and the plugin cache; query search over name, description and source.
- Audit and dedupe: flags duplicate skill names, stale `scripts/*` references inside SKILL.md, and missing frontmatter; proposes keep-one-remove-rest.
- Safe install: dry-run file list before copying a marketplace folder or repo zip into `~/.zcode/skills`.
- Safe remove: timestamped backup to `~/.zcode/skill-curator-backups/` and a hard refusal to delete without `--yes`.
