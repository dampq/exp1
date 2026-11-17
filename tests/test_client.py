"""Check the actual terminal workflow, including MCP subprocess startup."""
from pathlib import Path
import subprocess
import sys
import unittest


class TerminalTests(unittest.TestCase):
    def test_questions_and_exit(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "client.py")],
            input="What is deep learning?\nWhich document discusses CNN?\nSummarize the machine learning document.\nunknownxyz\nexit\n",
            capture_output=True, text=True, timeout=20, cwd="/tmp",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Source: deep_learning.txt", result.stdout)
        self.assertIn("Matching documents:\ndeep_learning.txt", result.stdout)
        self.assertIn("Source: machine_learning.txt", result.stdout)
        self.assertIn("Supervised learning", result.stdout)
        self.assertIn("No relevant information found", result.stdout)
        self.assertIn("Goodbye!", result.stdout)
        self.assertNotIn("Processing request", result.stdout + result.stderr)
