<a id="module-eric_sse.exception"></a>

<a id="exceptions"></a>

# Exceptions

<a id="eric_sse.exception.InvalidChannelException"></a>

### *exception* InvalidChannelException

<a id="eric_sse.exception.InvalidConnectionException"></a>

### *exception* InvalidConnectionException

<a id="eric_sse.exception.InvalidListenerException"></a>

### *exception* InvalidListenerException

<a id="eric_sse.exception.InvalidMessageFormat"></a>

### *exception* InvalidMessageFormat

<a id="eric_sse.exception.ItemNotFound"></a>

### *exception* ItemNotFound

Raised to inform that a key was not found in a repository

<a id="eric_sse.exception.ItemNotFound.__init__"></a>

#### \_\_init_\_(key)

* **Parameters:**
  **key** ([*str*](https://docs.python.org/3/library/stdtypes.html#str))

<a id="eric_sse.exception.NoMessagesException"></a>

### *exception* NoMessagesException

Raised when trying to fetch from an empty queue

<a id="eric_sse.exception.RepositoryError"></a>

### *exception* RepositoryError

Raised when an unexpected error occurs while trying to fetch messages from a queue.

Concrete implementations of `ObjectRepositoryInterface` should wrap here the unexpected exceptions they catch before raising.
