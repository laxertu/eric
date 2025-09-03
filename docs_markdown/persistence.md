<a id="module-eric_sse.interfaces"></a>

<a id="persistence"></a>

# Persistence

<a id="eric_sse.interfaces.QueueRepositoryInterface"></a>

### *class* QueueRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.QueueRepositoryInterface.load"></a>

#### *abstract* load(connection_id)

Loads a queue given the connection id it belongs to.

* **Parameters:**
  **connection_id** (*str*)
* **Return type:**
  [*Queue*](channels.md#eric_sse.queues.Queue)

<a id="eric_sse.interfaces.QueueRepositoryInterface.persist"></a>

#### *abstract* persist(connection_id, queue)

* **Parameters:**
  * **connection_id** (*str*)
  * **queue** ([*Queue*](channels.md#eric_sse.queues.Queue))

<a id="eric_sse.interfaces.QueueRepositoryInterface.delete"></a>

#### *abstract* delete(connection_id)

Deletes a queue given the connection id it belongs to.

* **Parameters:**
  **connection_id** (*str*)

<a id="eric_sse.interfaces.ListenerRepositoryInterface"></a>

### *class* ListenerRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.ListenerRepositoryInterface.load"></a>

#### *abstract* load(connection_id)

Loads a listener given the connection id it belongs to.

* **Parameters:**
  **connection_id** (*str*)
* **Return type:**
  [*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener)

<a id="eric_sse.interfaces.ListenerRepositoryInterface.persist"></a>

#### *abstract* persist(connection_id, listener)

* **Parameters:**
  * **connection_id** (*str*)
  * **listener** ([*MessageQueueListener*](channels.md#eric_sse.listener.MessageQueueListener))

<a id="eric_sse.interfaces.ListenerRepositoryInterface.delete"></a>

#### *abstract* delete(connection_id)

Deleted a listener given the connection id it belongs to.

* **Parameters:**
  **connection_id** (*str*)

<a id="eric_sse.interfaces.ConnectionRepositoryInterface"></a>

### *class* ConnectionRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.queues_repository"></a>

#### *abstract property* queues_repository *: [QueueRepositoryInterface](#eric_sse.interfaces.QueueRepositoryInterface)*

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.listeners_repository"></a>

#### *abstract property* listeners_repository *: [ListenerRepositoryInterface](#eric_sse.interfaces.ListenerRepositoryInterface)*

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.load_all"></a>

#### *abstract* load_all(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  *Iterable*[[*Connection*](channels.md#eric_sse.connection.Connection)]

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.load_one"></a>

#### *abstract* load_one(channel_id, connection_id)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection_id** (*str*)
* **Return type:**
  [*Connection*](channels.md#eric_sse.connection.Connection)

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.persist"></a>

#### *abstract* persist(channel_id, connection)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection** ([*Connection*](channels.md#eric_sse.connection.Connection))

<a id="eric_sse.interfaces.ConnectionRepositoryInterface.delete"></a>

#### *abstract* delete(channel_id, connection_id)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection_id** (*str*)

<a id="eric_sse.interfaces.ChannelRepositoryInterface"></a>

### *class* ChannelRepositoryInterface

Bases: `ABC`

<a id="eric_sse.interfaces.ChannelRepositoryInterface.connections_factory"></a>

#### *abstract property* connections_factory *: [ConnectionsFactory](channels.md#eric_sse.connection.ConnectionsFactory)*

<a id="eric_sse.interfaces.ChannelRepositoryInterface.connections_repository"></a>

#### *abstract property* connections_repository *: [ConnectionRepositoryInterface](#eric_sse.interfaces.ConnectionRepositoryInterface)*

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

<a id="eric_sse.interfaces.ChannelRepositoryInterface.create"></a>

#### *abstract* create(channel_data)

* **Parameters:**
  **channel_data** (*dict*)
* **Return type:**
  [*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel)

<a id="module-eric_sse.repository"></a>

<a id="base-repositories"></a>

# Base repositories

<a id="eric_sse.repository.KvStorage"></a>

### *class* KvStorage

Bases: `ABC`

<a id="eric_sse.repository.KvStorage.fetch_by_prefix"></a>

#### *abstract* fetch_by_prefix(prefix)

* **Parameters:**
  **prefix** (*str*)
* **Return type:**
  *Iterable*[*Any*]

<a id="eric_sse.repository.KvStorage.fetch_all"></a>

#### *abstract* fetch_all()

* **Return type:**
  *Iterable*[*Any*]

<a id="eric_sse.repository.KvStorage.upsert"></a>

#### *abstract* upsert(key, value)

* **Parameters:**
  * **key** (*str*)
  * **value** (*Any*)

<a id="eric_sse.repository.KvStorage.fetch_one"></a>

#### *abstract* fetch_one(key)

* **Parameters:**
  **key** (*str*)
* **Return type:**
  *Any*

<a id="eric_sse.repository.KvStorage.delete"></a>

#### *abstract* delete(key)

* **Parameters:**
  **key** (*str*)

<a id="eric_sse.repository.InMemoryStorage"></a>

### *class* InMemoryStorage

Bases: [`KvStorage`](#eric_sse.repository.KvStorage)

<a id="eric_sse.repository.InMemoryStorage.__init__"></a>

#### \_\_init_\_(items=None)

* **Parameters:**
  **items** (*dict* *[**str* *,* *Any* *]*  *|* *None*)

<a id="eric_sse.repository.InMemoryStorage.fetch_by_prefix"></a>

#### fetch_by_prefix(prefix)

* **Parameters:**
  **prefix** (*str*)
* **Return type:**
  *Iterable*[*Any*]

<a id="eric_sse.repository.InMemoryStorage.fetch_all"></a>

#### fetch_all()

* **Return type:**
  *Iterable*[*Any*]

<a id="eric_sse.repository.InMemoryStorage.upsert"></a>

#### upsert(key, value)

* **Parameters:**
  * **key** (*str*)
  * **value** (*Any*)

<a id="eric_sse.repository.InMemoryStorage.fetch_one"></a>

#### fetch_one(key)

* **Parameters:**
  **key** (*str*)
* **Return type:**
  *Any*

<a id="eric_sse.repository.InMemoryStorage.delete"></a>

#### delete(key)

* **Parameters:**
  **key** (*str*)

<a id="eric_sse.repository.AbstractChannelRepository"></a>

### *class* AbstractChannelRepository

Bases: [`ChannelRepositoryInterface`](#eric_sse.interfaces.ChannelRepositoryInterface), `ABC`

<a id="eric_sse.repository.AbstractChannelRepository.__init__"></a>

#### \_\_init_\_(storage, connections_repository, connections_factory)

* **Parameters:**
  * **storage** ([*KvStorage*](#eric_sse.repository.KvStorage))
  * **connections_repository** ([*ConnectionRepositoryInterface*](#eric_sse.interfaces.ConnectionRepositoryInterface))
  * **connections_factory** ([*ConnectionsFactory*](channels.md#eric_sse.connection.ConnectionsFactory))

<a id="eric_sse.repository.AbstractChannelRepository.connections_factory"></a>

#### *property* connections_factory *: [ConnectionsFactory](channels.md#eric_sse.connection.ConnectionsFactory)*

<a id="eric_sse.repository.AbstractChannelRepository.connections_repository"></a>

#### *property* connections_repository *: [ConnectionRepositoryInterface](#eric_sse.interfaces.ConnectionRepositoryInterface)*

<a id="eric_sse.repository.AbstractChannelRepository.load_all"></a>

#### load_all()

* **Return type:**
  *Iterable*[[*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel)]

<a id="eric_sse.repository.AbstractChannelRepository.load_one"></a>

#### load_one(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  [*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel)

<a id="eric_sse.repository.AbstractChannelRepository.persist"></a>

#### persist(channel)

* **Parameters:**
  **channel** ([*AbstractChannel*](channels.md#eric_sse.entities.AbstractChannel))

<a id="eric_sse.repository.AbstractChannelRepository.delete"></a>

#### delete(channel_id)

* **Parameters:**
  **channel_id** (*str*)

<a id="eric_sse.repository.ConnectionRepository"></a>

### *class* ConnectionRepository

Bases: [`ConnectionRepositoryInterface`](#eric_sse.interfaces.ConnectionRepositoryInterface)

<a id="eric_sse.repository.ConnectionRepository.__init__"></a>

#### \_\_init_\_(storage, listeners_repository, queues_repository)

* **Parameters:**
  * **storage** ([*KvStorage*](#eric_sse.repository.KvStorage))
  * **listeners_repository** ([*ListenerRepositoryInterface*](#eric_sse.interfaces.ListenerRepositoryInterface))
  * **queues_repository** ([*QueueRepositoryInterface*](#eric_sse.interfaces.QueueRepositoryInterface))

<a id="eric_sse.repository.ConnectionRepository.queues_repository"></a>

#### *property* queues_repository *: [QueueRepositoryInterface](#eric_sse.interfaces.QueueRepositoryInterface)*

<a id="eric_sse.repository.ConnectionRepository.listeners_repository"></a>

#### *property* listeners_repository *: [ListenerRepositoryInterface](#eric_sse.interfaces.ListenerRepositoryInterface)*

<a id="eric_sse.repository.ConnectionRepository.load_all"></a>

#### load_all(channel_id)

* **Parameters:**
  **channel_id** (*str*)
* **Return type:**
  *Iterable*[[*Connection*](channels.md#eric_sse.connection.Connection)]

<a id="eric_sse.repository.ConnectionRepository.load_one"></a>

#### load_one(channel_id, connection_id)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection_id** (*str*)
* **Return type:**
  [*Connection*](channels.md#eric_sse.connection.Connection)

<a id="eric_sse.repository.ConnectionRepository.persist"></a>

#### persist(channel_id, connection)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection** ([*Connection*](channels.md#eric_sse.connection.Connection))

<a id="eric_sse.repository.ConnectionRepository.delete"></a>

#### delete(channel_id, connection_id)

* **Parameters:**
  * **channel_id** (*str*)
  * **connection_id** (*str*)
