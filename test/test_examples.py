import os
import re
import subprocess
import sys
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).parent.parent
TUTORIALS_PAGE = ROOT / 'docs' / 'source' / 'tutorials.rst'
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')


def documented_outputs() -> dict[str, list[str]]:
    """
    Maps each example included in the tutorials page to the lines of the ``Output::`` block that follows it.
    """
    outputs = {}
    example = None
    lines = TUTORIALS_PAGE.read_text().splitlines()
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
    """The tutorials page shows each example and its output: both must match what the example does."""

    def test_the_tutorials_page_documents_examples(self):
        self.assertGreater(len(documented_outputs()), 0)

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
