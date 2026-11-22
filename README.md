<a id="the-lightweight-library-for-async-messaging-nobody-expects"></a>

# The lightweight library for async messaging nobody expects.

![coverage](https://laxertu.github.io/eric/coverage.svg)

*Installation*

pip install eric-sse

*Versioning*

Starting from 3.0.0, the project follows [semantic versioning](https://semver.org/).

*Related packages*

Not yet updated for 3.0.0: use them with eric-sse 2.x.

* https://pypi.org/project/eric-redis-queues/ Redis integration
* https://pypi.org/project/eric-api/ FastApi microservice

*Features*

* Send to one connection or broadcast to all of them
* SSE format was adopted by design, making the library suitable for such kind of model
* Parallel message processing in an executor
* Optional persistence layer, with pluggable storage engines and a builder that wires it
* Error handlers, with Dead Letter and Reliable Queue (explicit ack) patterns
* Sockets server prefab for offline inter process communication
* Profiling decorators for queues and listeners
* Contracts: test suites to verify your own storages, queues and channels
* Python 3.10 to 3.14

*Possible applications*

* Message delivery mechanisms based on Server Side Events model
* Message queue processing (logging, ETL, http based notification systems, etc)

*Documentation*

* Reference https://laxertu.github.io/eric
* Tutorials https://laxertu.github.io/eric/tutorials.html
* A good example of usage is eric api service definition: https://github.com/laxertu/eric-api/blob/master/eric_api.py (eric-sse 2.x)
* Some more example about other usages of the library: https://github.com/laxertu/eric/tree/master/examples


*Trivia*

* Library name pretends to be a tribute to the following movie [https://en.wikipedia.org/wiki/Looking_for_Eric](https://en.wikipedia.org/wiki/Looking_for_Eric)
