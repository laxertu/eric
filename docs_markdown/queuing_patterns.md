<a id="queuing-patterns"></a>

# Queuing patterns

Common messaging patterns, in the `eric_sse.queue_patterns` module:

* [Dead Letter](dead_letter.md): messages that can’t be delivered or processed go to a separate queue instead of being lost.
* [Reliable Queue](reliable_queue.md): popped messages are kept until acknowledged, so they can be delivered again.

* [Dead Letter](dead_letter.md)
* [Reliable Queue](reliable_queue.md)
