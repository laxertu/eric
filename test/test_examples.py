import os
import re
import subprocess
import sys
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).parent.parent
DOCS = ROOT / 'docs' / 'source'
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')


def documented_outputs() -> dict[str, list[str]]:
    """
    Maps each example included in a docs page to the lines of the ``Output::`` block that follows it.
    """
    outputs = {}
    for page in sorted(DOCS.glob('**/*.rst')):
        outputs.update(_page_outputs(page.read_text().splitlines()))
    return outputs


def _page_outputs(lines: list[str]) -> dict[str, list[str]]:
    outputs = {}
    example = None
    for i, line in enumerate(lines):
        if match := re.match(r'\.\. literalinclude:: \.\./\.\./(\S+)', line):
            example = match.group(1)
        elif line.strip() == 'Output::' and example is not None:
            block = []
            for following in lines[i + 1:]:
                if following and not following.startswith(' '):
                    break
                block.append(following.strip())
            outputs[example] = [line for line in block if line]
            example = None
    return outputs


def normalise(lines: list[str]) -> list[str]:
    """Generated ids differ on every run."""
    return [UUID.sub('<uuid>', line).strip() for line in lines if line.strip()]


class TutorialsTestCase(TestCase):
    """Docs pages show examples and their output: both must match what the example does."""

    def test_both_tutorials_are_documented_with_their_output(self):
        self.assertTrue({'examples/tutorial_in_memory.py', 'examples/tutorial_kv_storage.py'} <= set(documented_outputs()))

    def test_every_tutorial_prints_its_documented_output(self):
        for example, expected in documented_outputs().items():
            with self.subTest(example=example):
                result = subprocess.run(
                    [sys.executable, str(ROOT / example)],
                    cwd=ROOT,
                    env={**os.environ, 'PYTHONPATH': str(ROOT)},
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(normalise(expected), normalise(result.stdout.splitlines()))
