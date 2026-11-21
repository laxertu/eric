<a id="tutorials"></a>

# Tutorials

Two complete, runnable programs. Both live in the
[examples](https://github.com/laxertu/eric/tree/master/examples) directory. The test suite runs them and compares
what they print with the output shown on their pages, so their code always works with the current version.

* [In-memory application](tutorial_in_memory.md): a chat room where users subscribe, receive private and broadcast messages, and leave.
  Everything lives in the current process.
* [Persistence with a custom KvStorage](tutorial_kv_storage.md): the same building blocks, persisted with SQLite, so channels, listeners and pending
  messages survive a restart.

* [In-memory application](tutorial_in_memory.md)
* [Persistence with a custom KvStorage](tutorial_kv_storage.md)
