"""The check command is executed directly, without shell expansion."""
import json
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).resolve().with_name("time_check.py")


class TimeCheckTests(unittest.TestCase):
    def test_quoted_arguments_are_literal_and_exit_status_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            helper = root / "check arguments.py"
            helper.write_text(
                "import json, pathlib, sys\n"
                "pathlib.Path('arguments.json').write_text(json.dumps(sys.argv[1:]))\n"
                "sys.exit(7)\n"
            )
            literal = "$(touch${IFS}unexpected-shell-write)"
            command = shlex.join([sys.executable, str(helper), "argument with spaces"]) + " " + literal
            result = subprocess.run(
                [sys.executable, str(SCRIPT), command],
                cwd=root,
                env={**os.environ, "ONEV1_ROOT": str(root), "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
            self.assertIn("exit=7", result.stdout)
            self.assertEqual(json.loads((root / "arguments.json").read_text()),
                             ["argument with spaces", literal])
            self.assertFalse((root / "unexpected-shell-write").exists())


if __name__ == "__main__":
    unittest.main()
