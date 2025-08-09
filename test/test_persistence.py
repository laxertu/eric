from unittest import TestCase

from eric_sse.listener import PersistableListener
from eric_sse.prefabs import SSEChannel
from eric_sse.persistence import importlib_create_instance

class TestPersistence(TestCase):

    def test_persistable_listener(self):
        listener = PersistableListener()

        listener_clone = PersistableListener()
        listener_clone.kv_setup_by_dict(listener.kv_setup_values_as_dict)

        self.assertEqual(listener.id, listener_clone.id)
        self.assertFalse(listener.is_running())
        listener.start()

        listener_clone = PersistableListener()
        listener_clone.kv_setup_by_dict(listener.kv_setup_values_as_dict)
        self.assertTrue(listener.is_running())

    def test_importlib_create_instance(self):
        channel = SSEChannel(stream_delay_seconds=44, retry_timeout_milliseconds=123)

        self.assertTrue('channel_id' in channel.kv_constructor_params_as_dict)

        channel_clone = importlib_create_instance(
            class_full_path=channel.kv_class_absolute_path,
            constructor_params=channel.kv_constructor_params_as_dict,
            setup_values=channel.kv_setup_values_as_dict,
        )

        self.assertFalse(id(channel) == id(channel_clone))
        self.assertIsInstance(channel_clone, SSEChannel)

        self.assertEqual(channel.id, channel_clone.id)
        self.assertEqual(channel.kv_key, channel_clone.kv_key)

        self.assertEqual(channel_clone.stream_delay_seconds, channel_clone.stream_delay_seconds)
        self.assertEqual(channel_clone.retry_timeout_milliseconds, channel_clone.retry_timeout_milliseconds)
