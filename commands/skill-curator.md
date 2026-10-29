---
description: Inventory, search, audit, dedupe, install, and safely remove local ZCode skills
allowed-tools: Read, Bash, Write, Glob, Grep
argument-hint: <subcommand: list | search <query> | audit | dedupe | install <path> | remove <name>>
---
Invoke the `skill-curator` skill with this input: **$ARGUMENTS**

If no arguments are given, run `list` to show the full local skill catalog,
then `audit` to surface duplicates and broken references. Never run `remove`
without the user confirming the exact file list from the dry-run first.
