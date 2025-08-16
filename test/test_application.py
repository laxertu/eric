from abc import ABC, abstractmethod
from unittest import TestCase
from unittest.mock import MagicMock

import pytest

from eric_sse.application import ApplicationTemplate
from eric_sse.entities import AbstractChannel
from eric_sse.exception import InvalidChannelException
from eric_sse.inmemory import (InMemoryChannelRepository, InMemoryConnectionRepository, InMemoryListenerRepository,
                               InMemoryQueueRepository)
from eric_sse.listener import MessageQueueListener
from eric_sse.queues import Queue, InMemoryQueue
from eric_sse.message import Message
from eric_sse.prefabs import SSEChannel

channels_repo = InMemoryChannelRepository()
connections_repo = InMemoryConnectionRepository()
listeners_repo = InMemoryListenerRepository()
queues_repo = InMemoryQueueRepository()

class AbstractTestApplication(TestCase, ABC):

    @abstractmethod
    def _create_sut(self) -> ApplicationTemplate:
        pass

    def setUp(self):
        self.sut: ApplicationTemplate = self._create_sut()

    def test_create_and_then_load_channel(self):
        channel = self.sut.create_channel()
        self.assertIs(channel, self.sut.load_channel(channel_id=channel.id))

    def test_channels_needs_to_be_created_by_application(self):
        other_channel = MagicMock(AbstractChannel)
        with pytest.raises(InvalidChannelException):
            self.sut.subscribe_channel(other_channel)

    def test_subscriptions_are_saved_and_can_be_loaded(self):
        channel = self.sut.create_channel()
        connection = self.sut.subscribe_channel(channel)
        message = Message(msg_type='test')
        channel.dispatch(connection.listener.id, message)

        other_application = self._create_sut()
        channels = other_application.boot()

        connection.listener.start()
        received_message = channels[channel.id].deliver_next(connection.listener.id)
        self.assertIs(received_message, message)

    def test_deletions(self):
        channel = self.sut.create_channel()
        connection = self.sut.subscribe_channel(channel)

        connections = [c for c in channel.get_connections()]
        self.assertEqual(len(connections), 1)

        self.sut.unsubscribe_channel(channel_id=channel.id, connection_id=connection.id)
        connections = [c for c in channel.get_connections()]
        self.assertEqual(len(connections), 0)


class TestInMemoryApplicationTemplate(AbstractTestApplication):

    class InMemoryApplicationTemplate(ApplicationTemplate):

        def _create_channel(self) -> AbstractChannel:
            return SSEChannel()

        def _create_listener(self) -> MessageQueueListener:
            return MessageQueueListener()

        def _create_queue(self) -> Queue:
            return InMemoryQueue()

    def _create_sut(self) -> ApplicationTemplate:
        return self.InMemoryApplicationTemplate(
            channel_repository=channels_repo,
            connection_repository=connections_repo,
            listener_repository=listeners_repo,
            queue_repository=queues_repo
        )