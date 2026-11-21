---
description: Run the test suite and summarize failures
# argument-hint: [test path or -k expression]
# allowed-tools: Bash(pytest:*), Bash(./run_tests.sh)
---

<!--
Custom slash command, invoked as /run-tests. The filename is the command name.
The body is the prompt Claude receives; $ARGUMENTS is replaced with whatever
follows the command. Keep one command per file, focused on a repeatable task.
-->

<!-- Describe what Claude should do, e.g.: run ./run_tests.sh (or pytest on
$ARGUMENTS if given), then report failing tests with the likely cause. -->

run ./run_tests.sh