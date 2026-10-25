# CLAUDE.md

<!--
Project memory for Claude Code. Loaded automatically at the start of every
session in this repository, so keep it short, factual and up to date.
Commit it: it is shared with everyone working on the repo.
Put here only what cannot be quickly derived from the code itself.
-->

## Project overview

<!-- One or two paragraphs: what eric-sse is, who uses it, and how it relates
to the sibling packages (eric-redis-queues, eric-api). -->

Main goal of this project is to be an easy to extend and customize event-driven development toolkit.
It's audience are developers that wants to build an event-driven application without having to deal with complex to
understand and / or maintain solutions, like kafka, rabbit md and similar tools.

## Architecture

<!-- The main concepts and how they fit together, pointing to the modules in
eric_sse/ (entities, listener, queues, repository, servers, prefabs, facade...).
Describe the responsibilities and the extension points, not every class. -->

Main concepts are:
An implementation of something similar to publish-subscribe pattern, defined in entities.py, and a persistence layer, 
defined in interfaces.py.

Library users should be able to define theis own persistence layers and / or channel listeners


## Commands

<!-- The exact commands to install, test, lint, build docs and package, e.g.:
- Install: `poetry install --with test,doctools`
- Tests: `./run_tests.sh`
- Docs: `./update_docs.sh`
Include how to run a single test. -->

- Tests: `./run_tests.sh`
- Update docs: `./update_docs.sh`

## Conventions

<!-- Coding style, naming, typing, async patterns, error handling (exception.py),
public vs internal API, backward compatibility rules. -->

## Testing

<!-- Where tests live (test/, test/mock/), what must be tested, mocking
approach, anything that is slow or flaky. -->

tests are defined in test/ directory

## Documentation

<!-- How docs are generated (Sphinx in docs/ -> docs_html/, docs_markdown/),
which files are generated and must not be edited by hand, docstring format. -->

Update docs/source/changelog.rst

## Release process

<!-- Versioning scheme (pyproject.toml version), changelog location, how a
release is published to PyPI. -->

this is a poetry project and uses semantic versioning


## Gotchas

<!-- Non-obvious pitfalls, things that broke before, files or directories to
leave alone (dist/, docs_archive/, ...). -->

