from unittest import TestCase

from eric_sse.persistence import PersistableListener

class TestPersistence(TestCase):

    def test_persistable_listener(self):
        listener = PersistableListener()

        listener_clone = PersistableListener()
        listener_clone.setup_by_dict(listener.kv_value_as_dict)

        self.assertEqual(listener.id, listener_clone.id)
        self.assertFalse(listener.is_running())
        listener.start()

        listener_clone = PersistableListener()
        listener_clone.setup_by_dict(listener.kv_value_as_dict)
        self.assertTrue(listener.is_running())


