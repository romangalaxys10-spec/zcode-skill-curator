#!/usr/bin/env python3
"""skill_catalog.py: local ZCode skill catalog.

Scans skill roots (~/.zcode/skills, ~/.agents/skills, installed plugin
cache) for SKILL.md files, then lists, searches, audits, and dedupes
them. Python 3 stdlib only. Cross-OS.

Exit codes:
  0  success, or (audit) no issues found
  1  no results (search), or (audit) issues found, or (remove) needs --yes
  2  bad usage, or (remove) path not found

Usage examples:
  python3 skill_catalog.py list [--json] [--dirs ROOT ...]
  python3 skill_catalog.py search "kubernetes" [--json]
  python3 skill_catalog.py audit [--json]
  python3 skill_catalog.py dedupe [--json]
  python3 skill_catalog.py remove --path /abs/path/to/skills/foo [--dry-run] --yes
"""
import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


def expand_root(path_str: str) -> Path:
    """Expand ~ and shell-style quoting on macOS without shell=True."""
    p = os.path.expandvars(path_str)
    p = os.path.expanduser(p)
    # Handle quoted paths passed as a single shell-expanded string
    if len(p) > 1 and p[0] in "\"'" and p[-1] == p[0]:
        p = p[1:-1]
    return Path(p)


@dataclass
class SkillEntry:
    skill_md: str
    name: str
    source: str
    version: str
    description: str
    issues: list

    def to_dict(self):
        d = asdict(self)
        if not d["issues"]:
            d.pop("issues")
        return d


def default_roots():
    home = Path.home()
    return [
        (home / ".zcode" / "skills", "user"),
        (home / ".agents" / "skills", "agents"),
        (
            home / ".zcode" / "cli" / "plugins" / "cache",
            "plugin-cache",
        ),
    ]


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
SCRIPT_REF_RE = re.compile(r"(scripts/[A-Za-z0-9_./\-]+\.(?:py|sh|js))")


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML frontmatter reader: flat `key: value` pairs only."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if line.startswith((" ", "\t")) or not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            fm[key] = value
    return fm


def scan(root_path: Path, source: str, entries: list):
    if not root_path.exists():
        return
    for skill_md in sorted(root_path.rglob("SKILL.md")):
        text = ""
        issues = []
        try:
            text = skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            text = ""
            issues.append(f"unreadable SKILL.md ({e})")
        fm = parse_frontmatter(text)
        name = fm.get("name") or skill_md.parent.name
        version = fm.get("version", "")
        description = fm.get("description", "")
        if not text.strip().startswith("---"):
            issues.append("missing frontmatter")
        if not fm.get("name"):
            issues.append("frontmatter missing name")
        if not description:
            issues.append("frontmatter missing or empty description")
        # Stale script references: SKILL.md pointing at scripts that do not exist
        base_dir = skill_md.parent
        for ref in set(SCRIPT_REF_RE.findall(text)):
            if not (base_dir / ref).exists():
                issues.append(f"stale reference: {ref} not found")
        entries.append(
            SkillEntry(
                skill_md=str(skill_md),
                name=name,
                source=source,
                version=version,
                description=description,
                issues=issues,
            )
        )


def build_catalog(args) -> list:
    entries = []
    if args.dirs:
        for raw in args.dirs:
            p = expand_root(raw)
            if not p.exists():
                print(f"warning: root does not exist, skipping: {p}", file=sys.stderr)
                continue
            scan(p, f"dir:{p}", entries)
    else:
        for root, label in default_roots():
            scan(root, label, entries)
    entries.sort(key=lambda e: (e.name, e.source, e.skill_md))
    return entries


def dedupe_groups(entries: list) -> dict:
    by_name = {}
    for e in entries:
        by_name.setdefault(e.name, []).append(e)
    return {n: es for n, es in by_name.items() if len(es) > 1}


def print_markdown_catalog(entries: list):
    print(f"| Name | Source | Version | Description |")
    print(f"|---|---|---|---|")
    for e in entries:
        desc = (e.description or "(none)").replace("|", "\\|").replace("\n", " ")
        print(f"| {e.name} | {e.source} | {e.version or '-'} | {desc} |")
    dupes = dedupe_groups(entries)
    if dupes:
        print(f"\n## Duplicates ({sum(len(v) for v in dupes.values())} entries, {len(dupes)} names)")
        for n, es in sorted(dupes.items()):
            for e in es:
                print(f"- {n} <- {e.skill_md} ({e.source})")
    flagged = [e for e in entries if e.issues]
    if flagged:
        print(f"\n## Audit flags ({len(flagged)} skills)")
        for e in flagged:
            print(f"- {e.name} ({e.skill_md}): " + "; ".join(e.issues))


def print_audit(entries: list, as_json: bool):
    dupes = dedupe_groups(entries)
    flagged = [e for e in entries if e.issues]
    report = {
        "scanned": len(entries),
        "duplicate_names": {n: [e.skill_md for e in es] for n, es in dupes.items()},
        "flagged": [e.to_dict() for e in flagged],
    }
    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Scanned {len(entries)} SKILL.md files.")
        print(f"Duplicate names: {len(dupes)}")
        for n, es in sorted(dupes.items()):
            print(f"  - {n}: " + ", ".join(e.source for e in es))
        print(f"Issue flags: {len(flagged)}")
        for e in flagged:
            print(f"  - {e.name} ({e.skill_md}): " + "; ".join(e.issues))
    sys.exit(1 if (dupes or flagged) else 0)


def cmd_list(args):
    entries = build_catalog(args)
    if args.json:
        print(json.dumps([e.to_dict() for e in entries], indent=2, ensure_ascii=False))
    else:
        print_markdown_catalog(entries)
    print(f"\nTotal: {len(entries)} skills", file=sys.stderr)


def cmd_search(args):
    entries = build_catalog(args)
    q = args.query.lower()
    hits = [
        e
        for e in entries
        if q in e.name.lower()
        or q in (e.description or "").lower()
        or q in e.source.lower()
    ]
    if args.json:
        print(json.dumps([e.to_dict() for e in hits], indent=2, ensure_ascii=False))
    else:
        if not hits:
            print(f"No matches for '{args.query}' in {len(entries)} skills.")
            sys.exit(1)
        for e in hits:
            ver = f" v{e.version}" if e.version else ""
            print(f"{e.name}{ver}  [{e.source}]  {e.description or '(no description)'}")
            print(f"    {e.skill_md}")
    sys.exit(0 if hits else 1)


def cmd_audit(args):
    entries = build_catalog(args)
    print_audit(entries, args.json)


def cmd_dedupe(args):
    entries = build_catalog(args)
    dupes = dedupe_groups(entries)
    if args.json:
        out = {
            n: [
                {"skill_md": e.skill_md, "source": e.source, "issues": e.issues}
                for e in es
            ]
            for n, es in dupes.items()
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        if not dupes:
            print("No duplicate skill names found.")
        else:
            print(f"Duplicate names: {len(dupes)}")
            for n, es in sorted(dupes.items()):
                print(f"\n{n} appears {len(es)} times:")
                for e in es:
                    mark = " [has issues]" if e.issues else ""
                    print(f"  - {e.skill_md} ({e.source}){mark}")
                print(
                    "  Suggestion: keep the one WITHOUT issues (plugin cache wins over copies),\n"
                    "  then remove the rest with: skill_catalog.py remove --path <SKILL.md parent> --dry-run, then --yes."
                )
            sys.exit(1)


def cmd_remove(args):
    target = expand_root(args.path)
    if not target.exists():
        print(f"error: path not found: {target}", file=sys.stderr)
        sys.exit(2)
    files = sorted(p for p in target.rglob("*") if p.is_file())
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = Path.home() / ".zcode" / "skill-curator-backups" / stamp
    if args.dry_run:
        print("DRY RUN: would back up and remove:")
        for f in files:
            rel = f.relative_to(target)
            print(f"  {f}  ->  {backup_root / rel}")
        print(f"Remove root: {target}")
        print("Re-run with --yes to perform the removal.")
        return
    if not args.yes:
        print(
            f"Refusing to remove {target}: {len(files)} files.\n"
            "This script never deletes without an explicit --yes flag, and the SKILL.md\n"
            "workflow requires the user to confirm in the session before --yes is passed.",
            file=sys.stderr,
        )
        sys.exit(1)
    backup_root.mkdir(parents=True, exist_ok=True)
    for f in files:
        dest = backup_root / f.relative_to(target)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
    shutil.rmtree(target)
    print(f"Backed up {len(files)} files to {backup_root}")
    print(f"Removed {target}")


def main():
    ap = argparse.ArgumentParser(
        prog="skill_catalog.py",
        description="Local ZCode skill catalog: list, search, audit, dedupe, safe remove.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dirs",
        nargs="+",
        default=None,
        help="extra roots to scan (repeatable); default roots are ~/.zcode/skills, "
        "~/.agents/skills, ~/.zcode/cli/plugins/cache",
    )

    p_list = sub.add_parser("list", parents=[common], help="build and print the catalog")
    p_list.add_argument("--json", action="store_true", help="JSON output")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", parents=[common], help="match query against the catalog")
    p_search.add_argument("query")
    p_search.add_argument("--json", action="store_true")
    p_search.set_defaults(func=cmd_search)

    p_audit = sub.add_parser(
        "audit",
        parents=[common],
        help="flag duplicates, stale refs, missing frontmatter",
    )
    p_audit.add_argument("--json", action="store_true")
    p_audit.set_defaults(func=cmd_audit)

    p_dedupe = sub.add_parser(
        "dedupe", parents=[common], help="list duplicate names with removal suggestions"
    )
    p_dedupe.add_argument("--json", action="store_true")
    p_dedupe.set_defaults(func=cmd_dedupe)

    p_remove = sub.add_parser("remove", help="back up then remove a skill dir (needs --yes)")
    p_remove.add_argument("--path", required=True, help="skill directory (parent of SKILL.md)")
    p_remove.add_argument("--dry-run", action="store_true", help="show files, change nothing")
    p_remove.add_argument("--yes", action="store_true", help="actually remove (backup first)")
    p_remove.set_defaults(func=cmd_remove)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
