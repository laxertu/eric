.. toctree::
   :maxdepth: 2
   :hidden:

   docs
   devs
   changelog

The lightweight library for async messaging nobody expects.
===========================================================


*Installation*

* pip install eric-sse

*Features*

* Send to one listener and broadcast
* SSE format was adopted by design, making the library suitable for such kind of model
* Callbacks and threading support
* Sockets server prefab for offline inter process communication
* Optional persistence layer with Redis as default engine


*Possible applications*

* Message delivery mechanisms based on SSE
* Message queue processing (logging, etc)
* See https://github.com/laxertu/eric-api

*Sources*

* Home https://github.com/laxertu/eric
* Examples https://github.com/laxertu/eric/tree/master/examples


*Trivia*

* Library name pretends to be a tribute to the following movie https://en.wikipedia.org/wiki/Looking_for_Eric
