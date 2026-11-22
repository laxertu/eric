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

.. image:: https://laxertu.github.io/eric/coverage.svg
   :alt: coverage

*Installation*

* pip install eric-sse

*Versioning*

Starting from 3.0.0, the project follows [semantic versioning](https://semver.org/).


*Features*

* Send to one connection or broadcast to all of them
* SSE format was adopted by design, making the library suitable for such kind of model
* Parallel message processing in an executor
* Optional persistence layer, with pluggable storage engines and a builder that wires it
* Error handlers, with Dead Letter and Reliable Queue (explicit ack) patterns
* Sockets server prefab for offline inter process communication
* Profiling decorators for queues and listeners
* Contracts: test suites to verify your own storages, queues and channels

*Possible applications*

* Message delivery mechanisms based on Server SEnt Events model
* Message queue processing (logging, event-driven mechanisms, etc)
* See https://github.com/laxertu/eric-api (not yet updated for 3.0.0)

*Sources*

* Home https://github.com/laxertu/eric
* Tutorials: :doc:`tutorials`
* Examples https://github.com/laxertu/eric/tree/master/examples
* Api service definition: https://github.com/laxertu/eric-api/blob/master/eric_api.py (eric-sse 2.x)


*Trivia*

* Library name pretends to be a tribute to the following movie https://en.wikipedia.org/wiki/Looking_for_Eric
