"""Runs the tutorials shown in the docs, so they can't silently break."""
import asyncio
import io
import importlib
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase

EXAMPLES = Path(__file__).parent.parent / 'examples'


def run_tutorial(file_name: str) -> str:
    # A real import, so that pickle can find classes defined in the example
    if str(EXAMPLES) not in sys.path:
        sys.path.insert(0, str(EXAMPLES))
    module = importlib.import_module(Path(file_name).stem)
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main()
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    return output.getvalue()


class TutorialsTestCase(TestCase):

    def test_in_memory(self):
        output = run_tutorial('tutorial_in_memory.py')
        self.assertIn('[alice] private: hi alice, welcome!', output)
        self.assertIn('[bob] chat: hello everybody', output)
        self.assertNotIn('spam', output)
        self.assertIn('[room] bob left', output)

    def test_kv_storage(self):
        output = run_tutorial('tutorial_kv_storage.py')
        self.assertIn('loaded channel with retry timeout 1000 ms', output)
        self.assertIn('greeting: are you still there?', output)
