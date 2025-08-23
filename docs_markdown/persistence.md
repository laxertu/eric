<a id="persistence"></a>

# Persistence

**Channels**

![image](_static/persistence-layer-channels.png)

**Connections**

![image](_static/persistence-layer-connections.png)

<a id="module-eric_sse.persistence"></a>

<a id="abstractions"></a>

# Abstractions

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin"></a>

### *class* ObjectAsKeyValuePersistenceMixin

Bases: `ABC`

Adds KV persistence support.

By implementing this abstract mixin should be possible to persist every object that is not directly
serializable by pickle, for example, if your Queues implementation wraps some incompatible dependency, e.g. a Redis client.

For this reason, the idea is that dict values should be serializable by pickle too.

see `importlib_create_instance()`

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_as_dict"></a>

#### *property* kv_as_dict *: dict*

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_key"></a>

#### *abstract property* kv_key *: str*

The key to use when persisting object

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_setup_values_as_dict"></a>

#### *abstract property* kv_setup_values_as_dict *: dict*

Returns value that will be persisted as a dictionary.

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_setup_by_dict"></a>

#### *abstract* kv_setup_by_dict(setup)

Does necessary post-creation setup of object given its persisted values

* **Parameters:**
  **setup** (*dict*)

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_class_absolute_path"></a>

#### *property* kv_class_absolute_path *: str*

Returns class full path as string

<a id="eric_sse.persistence.ObjectAsKeyValuePersistenceMixin.kv_constructor_params_as_dict"></a>

#### *abstract property* kv_constructor_params_as_dict *: dict*

Class constructor parameters as dict

<a id="eric_sse.persistence.KvStorageEngine"></a>

### *class* KvStorageEngine

Bases: `ABC`

<a id="eric_sse.persistence.KvStorageEngine.fetch_by_prefix"></a>

#### *abstract* fetch_by_prefix(prefix)

* **Parameters:**
  **prefix** (*str*)
* **Return type:**
  *Iterable*[any]

<a id="eric_sse.persistence.KvStorageEngine.fetch_all"></a>

#### *abstract* fetch_all()

* **Return type:**
  *Iterable*[any]

<a id="eric_sse.persistence.KvStorageEngine.upsert"></a>

#### *abstract* upsert(key, value)

* **Parameters:**
  * **key** (*str*)
  * **value** (*any*)

<a id="eric_sse.persistence.KvStorageEngine.fetch_one"></a>

#### *abstract* fetch_one(key)

* **Parameters:**
  **key** (*str*)
* **Return type:**
  any

<a id="eric_sse.persistence.KvStorageEngine.delete"></a>

#### *abstract* delete(key)

* **Parameters:**
  **key** (*str*)

<a id="module-eric_sse.interfaces"></a>

<a id="eric_sse.interfaces.ListenerRepositoryInterface"></a>

### *class* ListenerRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.ListenerRepositoryInterface.load"></a>

#### *abstract* load(listener_id)

* **Parameters:**
  **listener_id** (*str*)
* **Return type:**
  [*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener)

<a id="eric_sse.interfaces.ListenerRepositoryInterface.persist"></a>

#### *abstract* persist(listener)

* **Parameters:**
  **listener** ([*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener))

<a id="eric_sse.interfaces.ListenerRepositoryInterface.delete"></a>

#### *abstract* delete(listener_id)

* **Parameters:**
  **listener_id** (*str*)

<a id="eric_sse.interfaces.QueueRepositoryInterface"></a>

### *class* QueueRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.QueueRepositoryInterface.load"></a>

#### *abstract* load(queue_id)

* **Parameters:**
  **queue_id** (*str*)
* **Return type:**
  [*Queue*](channels.md#eric_sse.queues.Queue)

<a id="eric_sse.interfaces.QueueRepositoryInterface.persist"></a>

#### *abstract* persist(queue)

* **Parameters:**
  **queue** ([*Queue*](channels.md#eric_sse.queues.Queue))

<a id="eric_sse.interfaces.QueueRepositoryInterface.delete"></a>

#### *abstract* delete(queue_id)

* **Parameters:**
  **queue_id** (*str*)

<a id="eric_sse.interfaces.ConnectionRepositoryInterface"></a>

### *class* ConnectionRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.load_all"></a>

#### *abstract* load_all(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  *Iterable*[[*Connection*](channels.md#eric_sse.connection.Connection)]

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.load_one"></a>

#### *abstract* load_one(connection_id)

* **Parameters:**
  **connection_id** (*str*)
* **Return type:**
  [*Connection*](channels.md#eric_sse.connection.Connection)

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.persist"></a>

#### *abstract* persist(connection)

* **Parameters:**
  **connection** ([*Connection*](channels.md#eric_sse.connection.Connection))

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.delete"></a>

#### *abstract* delete(connection_id)

* **Parameters:**
  **connection_id** (*str*)

<a id="eric_sse.interfaces.ChannelRepositoryInterface"></a>

### *class* ChannelRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.ChannelRepositoryInterface.load_all"></a>

#### *abstract* load_all()

* **Return type:**
  *Iterable*[[*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel)]

<a id="eric_sse.interfaces.ChannelRepositoryInterface.load_one"></a>

#### *abstract* load_one(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  [*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel)

<a id="eric_sse.interfaces.ChannelRepositoryInterface.persist"></a>

#### *abstract* persist(channel)

* **Parameters:**
  **channel** ([*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel))

<a id="eric_sse.interfaces.ChannelRepositoryInterface.delete"></a>

#### *abstract* delete(channel_id)

* **Parameters:**
  **channel_id** (*str*)

<a id="module-eric_sse.inmemory"></a>

<a id="in-memory-implementations"></a>

# In memory implementations

<a id="eric_sse.inmemory.InMemoryStorage"></a>

### *class* InMemoryStorage

Bases: [`KvStorageEngine`](#eric_sse.persistence.KvStorageEngine)

<a id="eric_sse.inmemory.InMemoryStorage.__init__"></a>

#### \_\_init_\_(objects=None)

* **Parameters:**
  **objects** (*dict* *[**str* *,* *any* *]*  *|* *None*)

<a id="eric_sse.inmemory.InMemoryConnectionRepository"></a>

### *class* InMemoryConnectionRepository

Bases: [`ConnectionRepository`](#eric_sse.serializable.ConnectionRepository)

<a id="eric_sse.inmemory.InMemoryConnectionRepository.__init__"></a>

#### \_\_init_\_(connections=None)

* **Parameters:**
  **connections** (*dict* *[**str* *,* [*Connection*](channels.md#eric_sse.connection.Connection) *]*  *|* *None*)

<a id="eric_sse.inmemory.InMemoryChannelRepository"></a>

### *class* InMemoryChannelRepository

Bases: [`ChannelRepository`](#eric_sse.serializable.ChannelRepository)

<a id="eric_sse.inmemory.InMemoryChannelRepository.__init__"></a>

#### \_\_init_\_(channels=None)

* **Parameters:**
  **channels** (*dict* *[**str* *,* [*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel) *]*  *|* *None*)

<a id="eric_sse.inmemory.InMemoryQueueRepository"></a>

### *class* InMemoryQueueRepository

Bases: [`QueueRepository`](#eric_sse.serializable.QueueRepository)

<a id="eric_sse.inmemory.InMemoryQueueRepository.__init__"></a>

#### \_\_init_\_(queues=None)

* **Parameters:**
  **queues** (*dict* *[**str* *,* [*Queue*](channels.md#eric_sse.queues.Queue) *]*  *|* *None*)

<a id="module-eric_sse.serializable"></a>

<a id="implementation-for-serializable-objects"></a>

# Implementation for serializable objects

If you have to persist a serializable participant, you can use this module if correspondant storage engine supports its format

see [`InMemoryChannelRepository`](#eric_sse.inmemory.InMemoryChannelRepository)

<a id="eric_sse.serializable.ListenerRepository"></a>

### *class* ListenerRepository

Bases: [`ListenerRepositoryInterface`](#eric_sse.interfaces.ListenerRepositoryInterface)

<a id="eric_sse.serializable.ListenerRepository.__init__"></a>

#### \_\_init_\_(storage_engine)

* **Parameters:**
  **storage_engine** ([*KvStorageEngine*](#eric_sse.persistence.KvStorageEngine))

<a id="eric_sse.serializable.ListenerRepository.load"></a>

#### load(listener_id)

* **Parameters:**
  **listener_id** (*str*)
* **Return type:**
  [*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener)

<a id="eric_sse.serializable.ListenerRepository.persist"></a>

#### persist(listener)

* **Parameters:**
  **listener** ([*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener))

<a id="eric_sse.serializable.ListenerRepository.delete"></a>

#### delete(listener_id)

* **Parameters:**
  **listener_id** (*str*)

<a id="eric_sse.serializable.QueueRepository"></a>

### *class* QueueRepository

Bases: [`QueueRepositoryInterface`](#eric_sse.interfaces.QueueRepositoryInterface)

<a id="eric_sse.serializable.QueueRepository.__init__"></a>

#### \_\_init_\_(storage_engine)

* **Parameters:**
  **storage_engine** ([*KvStorageEngine*](#eric_sse.persistence.KvStorageEngine))

<a id="eric_sse.serializable.QueueRepository.load"></a>

#### load(queue_id)

* **Parameters:**
  **queue_id** (*str*)
* **Return type:**
  [*Queue*](channels.md#eric_sse.queues.Queue)

<a id="eric_sse.serializable.QueueRepository.persist"></a>

#### persist(queue)

* **Parameters:**
  **queue** ([*Queue*](channels.md#eric_sse.queues.Queue))

<a id="eric_sse.serializable.QueueRepository.delete"></a>

#### delete(queue_id)

* **Parameters:**
  **queue_id** (*str*)

<a id="eric_sse.serializable.ConnectionRepository"></a>

### *class* ConnectionRepository

Bases: [`ConnectionRepositoryInterface`](#eric_sse.interfaces.ConnectionRepositoryInterface)

<a id="eric_sse.serializable.ConnectionRepository.__init__"></a>

#### \_\_init_\_(storage_engine)

* **Parameters:**
  **storage_engine** ([*KvStorageEngine*](#eric_sse.persistence.KvStorageEngine))

<a id="eric_sse.serializable.ConnectionRepository.load_all"></a>

#### load_all(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  *Iterable*[[*Connection*](channels.md#eric_sse.connection.Connection)]

<a id="eric_sse.serializable.ConnectionRepository.load_one"></a>

#### load_one(connection_id)

* **Parameters:**
  **connection_id** (*str*)
* **Return type:**
  [*Connection*](channels.md#eric_sse.connection.Connection)

<a id="eric_sse.serializable.ConnectionRepository.persist"></a>

#### persist(connection)

* **Parameters:**
  **connection** ([*Connection*](channels.md#eric_sse.connection.Connection))

<a id="eric_sse.serializable.ConnectionRepository.delete"></a>

#### delete(connection_id)

* **Parameters:**
  **connection_id** (*str*)

<a id="eric_sse.serializable.ChannelRepository"></a>

### *class* ChannelRepository

Bases: [`ChannelRepositoryInterface`](#eric_sse.interfaces.ChannelRepositoryInterface)

<a id="eric_sse.serializable.ChannelRepository.__init__"></a>

#### \_\_init_\_(storage_engine)

* **Parameters:**
  **storage_engine** ([*KvStorageEngine*](#eric_sse.persistence.KvStorageEngine))

<a id="eric_sse.serializable.ChannelRepository.load_all"></a>

#### load_all()

* **Return type:**
  *Iterable*[[*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel)]

<a id="eric_sse.serializable.ChannelRepository.load_one"></a>

#### load_one(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  [*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel)

<a id="eric_sse.serializable.ChannelRepository.persist"></a>

#### persist(channel)

* **Parameters:**
  **channel** ([*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel))

<a id="eric_sse.serializable.ChannelRepository.delete"></a>

#### delete(channel_id)

* **Parameters:**
  **channel_id** (*str*)
