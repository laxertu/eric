<a id="the-lightweight-library-for-async-messaging-nobody-expects"></a>

# The lightweight library for async messaging nobody expects.

*Installation*

pip install eric-sse

*Related packages*

* https://pypi.org/project/eric-redis-queues/ Redis integration
* https://pypi.org/project/eric-api/ FastApi microservice

*Features*

* Send to one listener and broadcast
* SSE format was adopted by design, making the library suitable for such kind of model
* Callbacks and threading support
* Sockets server prefab for offline inter process communication

*Possible applications*

* Message delivery mechanisms based on SSE
* Message queue processing (logging, ETL, http based notification systems, etc)

*Documentation*

* Reference https://laxertu.github.io/eric/docs.html
* A good example of usage is eric api service definition: https://github.com/laxertu/eric-api/blob/master/eric_api.py
* Some more example about other usages of the library: https://github.com/laxertu/eric/tree/master/examples


*Trivia*

* Library name pretends to be a tribute to the following movie [https://en.wikipedia.org/wiki/Looking_for_Eric](https://en.wikipedia.org/wiki/Looking_for_Eric)
