"""
Dispatches 10000 messages to one listener of a channel built with ChannelRepositoryBuilder defaults
(in-memory storage and queues), then delivers them all.

Needs the optional benchmark dependencies: ``poetry install --with benchmark``. Then run it with pyperformance,
that creates its own virtual environment in ./venv::

    poetry run pyperformance run --manifest benchmarks/MANIFEST -o results.json

or directly with pyperf::

    poetry run python benchmarks/bm_builder_dispatch/run_benchmark.py
"""
import sys
from pathlib import Path

import pyperf

# Benchmarks the working tree, also inside the virtual environment pyperformance creates
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eric_sse.builder import ChannelRepositoryBuilder  # noqa: E402
from eric_sse.message import Message  # noqa: E402
from eric_sse.prefabs import SSEChannel  # noqa: E402

MESSAGES = 10_000


def dispatch_and_deliver(loops: int) -> float:
    elapsed = 0.0
    msg = Message(msg_type='test', msg_payload={'value': 42})
    for _ in range(loops):
        channel = ChannelRepositoryBuilder(SSEChannel).build().create({})
        listener = channel.add_listener()
        listener.start()

        start = pyperf.perf_counter()
        for _ in range(MESSAGES):
            channel.dispatch(listener.id, msg)
        for _ in range(MESSAGES):
            channel.deliver_next(listener.id)
        elapsed += pyperf.perf_counter() - start
    return elapsed


if __name__ == '__main__':
    runner = pyperf.Runner()
    runner.metadata['description'] = f'Builder defaults: dispatch and deliver {MESSAGES} messages to one listener'
    runner.bench_time_func('builder_dispatch', dispatch_and_deliver)
