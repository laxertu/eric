from unittest import TestCase

from eric_sse.exception import ItemNotFound, NoMessagesException
from eric_sse.facade import Facade
from eric_sse.message import Message
from eric_sse.repository import InMemoryStorage


class FacadeInMemoryStorageIntegrationTestCase(TestCase):
    """
    End-to-end scenarios: two facades sharing the same InMemoryStorage instance
    simulate producer and consumer sides of an application.
    """

    def setUp(self):
        self.storage = InMemoryStorage()
        self.producer = Facade(storage=self.storage)
        self.consumer = Facade(storage=self.storage)

    def test_full_lifecycle(self):
        channel = self.producer.create_channel(retry_timeout_milliseconds=10)
        listener_1 = self.producer.add_listener(channel.id)
        listener_2 = self.producer.add_listener(channel.id)

        # Producer side: broadcast and persist
        channel = self.producer.get_channel(channel.id)
        channel.broadcast(Message(msg_type='greeting', msg_payload='hello'))
        channel.dispatch(listener_2.id, Message(msg_type='private', msg_payload='only for 2'))
        self.producer.repository.persist(channel)

        # Consumer side: reload from storage and consume
        channel = self.consumer.get_channel(channel.id)
        self.assertEqual(10, channel.retry_timeout_milliseconds)
        channel.get_listener(listener_1.id).start()
        channel.get_listener(listener_2.id).start()

        self.assertEqual('hello', channel.deliver_next(listener_1.id).payload)
        with self.assertRaises(NoMessagesException):
            channel.deliver_next(listener_1.id)

        self.assertEqual('hello', channel.deliver_next(listener_2.id).payload)
        self.assertEqual(
            {'event': 'private', 'retry': 10, 'data': 'only for 2'},
            channel.adapt(channel.deliver_next(listener_2.id))
        )

        # Removal is visible from the other facade
        self.consumer.remove_listener(channel.id, listener_1.id)
        connections = list(self.producer.get_channel(channel.id).get_connections())
        self.assertEqual([listener_2.id], [c.listener.id for c in connections])
        self.assertEqual(
            {f'listener:{connections[0].id}'},
            {k for k in self.storage.items if k.startswith('listener:')}
        )

        # Deletion cleans up every namespace
        self.producer.delete_channel(channel.id)
        with self.assertRaises(ItemNotFound):
            self.consumer.get_channel(channel.id)
        self.assertEqual({}, self.storage.items)

    def test_channels_are_isolated(self):
        channel_a = self.producer.create_channel()
        channel_b = self.producer.create_channel()
        listener_a = self.producer.add_listener(channel_a.id)
        listener_b = self.producer.add_listener(channel_b.id)

        channel_a = self.producer.get_channel(channel_a.id)
        channel_a.broadcast(Message(msg_type='test', msg_payload='a'))
        self.producer.repository.persist(channel_a)

        loaded_b = self.consumer.get_channel(channel_b.id)
        self.assertEqual([listener_b.id], [c.listener.id for c in loaded_b.get_connections()])
        loaded_b.get_listener(listener_b.id).start()
        with self.assertRaises(NoMessagesException):
            loaded_b.deliver_next(listener_b.id)

        loaded_a = self.consumer.get_channel(channel_a.id)
        loaded_a.get_listener(listener_a.id).start()
        self.assertEqual('a', loaded_a.deliver_next(listener_a.id).payload)

        self.consumer.delete_channel(channel_a.id)
        self.assertEqual([channel_b.id], [c.id for c in self.producer.get_channels()])
        self.assertEqual(
            {f'channel:{channel_b.id}'},
            {k for k in self.storage.items if k.startswith('channel:')}
        )

    def test_storage_layout(self):
        channel = self.producer.create_channel()
        listener = self.producer.add_listener(channel.id)
        connection = next(iter(self.producer.get_channel(channel.id).get_connections()))

        self.assertEqual(
            {
                f'channel:{channel.id}',
                f'connection:{channel.id}:{connection.id}',
                f'listener:{connection.id}',
                f'queue:{connection.id}',
            },
            set(self.storage.items)
        )
        self.assertEqual(listener.id, self.storage.items[f'listener:{connection.id}'].id)
