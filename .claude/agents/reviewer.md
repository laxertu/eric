---
name: reviewer
description: <When Claude should delegate to this subagent, e.g. "Reviews changes to eric_sse for API compatibility and async correctness">
# tools: Read, Grep, Glob, Bash
# model: inherit
---

<!--
Subagent definition. Claude can delegate tasks to it, and it runs with its own
context window, tools and system prompt (the body of this file).
The `description` decides when it is picked, so make it specific.
-->

<!-- System prompt: the agent's role, what to check, and the format of the
report it must return. -->
