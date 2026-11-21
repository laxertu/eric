<a id="module-eric_sse.exception"></a>

<a id="exceptions"></a>

# Exceptions

<a id="eric_sse.exception.InternalStreamError"></a>

### *exception* InternalStreamError

Stands for an unexpected error in a channel stream, without its details, that could expose internals to clients.
See [`adapt_error()`](entities.md#eric_sse.entities.AbstractChannel.adapt_error).

<a id="eric_sse.exception.InternalStreamError.__init__"></a>

#### \_\_init_\_()

<a id="eric_sse.exception.InvalidChannelException"></a>

### *exception* InvalidChannelException

<a id="eric_sse.exception.InvalidConnectionException"></a>

### *exception* InvalidConnectionException

<a id="eric_sse.exception.InvalidMessageFormat"></a>

### *exception* InvalidMessageFormat

<a id="eric_sse.exception.ItemNotFound"></a>

### *exception* ItemNotFound

Raised to inform that a key was not found in a repository

<a id="eric_sse.exception.ItemNotFound.__init__"></a>

#### \_\_init_\_(key)

* **Parameters:**
  **key** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))

<a id="eric_sse.exception.NoMessagesException"></a>

### *exception* NoMessagesException

Raised when trying to fetch from an empty queue

<a id="eric_sse.exception.RepositoryError"></a>

### *exception* RepositoryError

Raised when an unexpected error occurs while trying to fetch messages from a queue.

Concrete implementations of `ObjectRepositoryInterface` should wrap here the unexpected exceptions they catch before raising.

<a id="eric_sse.exception.StoppedListenerException"></a>

### *exception* StoppedListenerException

Raised when waiting for messages of a listener that is not running, see [`deliver_next()`](entities.md#eric_sse.entities.AbstractChannel.deliver_next) and [`wait_next()`](entities.md#eric_sse.entities.AbstractChannel.wait_next).

<a id="eric_sse.exception.StoppedListenerException.__init__"></a>

#### \_\_init_\_(connection_id)

* **Parameters:**
  **connection_id** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str))
