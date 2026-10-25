Developers section
==================

Documentation:

* Update script: update_docs.sh

Testing:

* run_tests.sh

Benchmarks:

Benchmarks are in ``benchmarks/``, run with `pyperformance <https://pyperformance.readthedocs.io/>`_, an optional
dependency. ``benchmarks/MANIFEST`` lists them; each one is a ``bm_<name>/`` directory with a ``pyproject.toml``
and a ``run_benchmark.py``.

* Install: ``poetry install --with benchmark``
* Run all: ``poetry run pyperformance run --manifest benchmarks/MANIFEST -o results.json``. pyperformance creates its own virtual environment in ``./venv``; benchmarks import ``eric_sse`` from the working tree
* Run one, without pyperformance: ``poetry run python benchmarks/bm_builder_dispatch/run_benchmark.py``
* Compare two results: ``poetry run pyperformance compare before.json after.json``

Available benchmarks:

* ``builder_dispatch``: 10000 messages dispatched to one listener of a channel built with ``ChannelRepositoryBuilder`` defaults, then delivered
