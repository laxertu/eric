.. toctree::
   :maxdepth: 2
   :hidden:

   docs
   tutorials
   class_reference
   devs
   changelog

The lightweight library for async messaging nobody expects.
===========================================================


*Installation*

* pip install eric-sse

*Features*

* Send to one connection or broadcast to all of them
* SSE format was adopted by design, making the library suitable for such kind of model
* Async streaming that waits for messages without polling, and hooks to customise channels
* Listener callbacks, and parallel message processing in an executor
* Optional persistence layer, with pluggable storage engines and a builder that wires it
* Error handlers, with Dead Letter and Reliable Queue (explicit ack) patterns
* Sockets server prefab for offline inter process communication
* Profiling decorators for queues and listeners
* Contracts: test suites to verify your own storages, queues and channels
* Python 3.10 to 3.14

*Possible applications*

* Message delivery mechanisms based on SSE
* Message queue processing (logging, etc)
* See https://github.com/laxertu/eric-api (not yet updated for 3.0.0)

*Sources*

* Home https://github.com/laxertu/eric
* Tutorials: :doc:`tutorials`
* Examples https://github.com/laxertu/eric/tree/master/examples
* Previous versions: :doc:`docs_archive`
* Api service definition: https://github.com/laxertu/eric-api/blob/master/eric_api.py (eric-sse 2.x)


*Trivia*

* Library name pretends to be a tribute to the following movie https://en.wikipedia.org/wiki/Looking_for_Eric
