---
name: release
description: bump version, update changelog, rebuild docs
---

<!--
Skill: a packaged set of instructions (plus optional helper files in this
directory, such as scripts or templates) that Claude loads on demand when a
task matches the description. Unlike CLAUDE.md, it costs no context until used.
-->

## Steps

<!-- Ordered checklist Claude must follow, e.g. version bump in pyproject.toml,
changelog entry, ./update_docs.sh, poetry build, checks before publishing. -->
update changelog.md

## Checks

tests pass
<!-- What must be verified before the task counts as done. -->
