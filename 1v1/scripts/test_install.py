"""Installer regression tests in disposable projects; no Claude Code required."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).resolve().with_name("install.py")
OWN_COMMAND = f'python "{SCRIPT.with_name("hook_guard.py")}"'


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.settings = self.root / ".claude" / "settings.json"
        self.settings.parent.mkdir()

    def write_settings(self, value):
        self.settings.write_text(json.dumps(value))

    def read_settings(self):
        return json.loads(self.settings.read_text()) if self.settings.exists() else {}

    def run_installer(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            env={**os.environ, "ONEV1_ROOT": str(self.root), "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_same_named_foreign_hook_does_not_skip_install_or_get_removed(self):
        foreign = {"matcher": "Bash", "hooks": [
            {"type": "command", "command": "python /other/tool/hook_guard.py"}
        ]}
        original = {"permissions": {"allow": ["Read"]}, "hooks": {"PreToolUse": [foreign]}}
        self.write_settings(original)
        self.run_installer()
        entries = self.read_settings()["hooks"]["PreToolUse"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0], foreign)
        self.assertEqual(entries[1]["hooks"][0]["command"], OWN_COMMAND)
        self.run_installer("--uninstall")
        self.assertEqual(self.read_settings(), original)

    def test_uninstall_preserves_foreign_hook_in_shared_entry(self):
        foreign = {"type": "command", "command": "echo keep me"}
        other_event = [{"matcher": "Read", "hooks": [foreign]}]
        self.write_settings({"hooks": {
            "PreToolUse": [{"matcher": "Bash", "timeout": 12, "hooks": [
                {"type": "command", "command": OWN_COMMAND}, foreign
            ]}],
            "PostToolUse": other_event,
        }})
        self.run_installer("--uninstall")
        self.assertEqual(self.read_settings(), {"hooks": {
            "PreToolUse": [{"matcher": "Bash", "timeout": 12, "hooks": [foreign]}],
            "PostToolUse": other_event,
        }})

    def test_prompt_mentioning_script_is_not_an_installed_command(self):
        prompt = {"matcher": "Bash", "hooks": [
            {"type": "prompt", "prompt": f"Review {OWN_COMMAND}"}
        ]}
        self.write_settings({"hooks": {"PreToolUse": [prompt]}})
        self.run_installer()
        self.assertEqual(len(self.read_settings()["hooks"]["PreToolUse"]), 2)
        self.run_installer("--uninstall")
        self.assertEqual(self.read_settings(), {"hooks": {"PreToolUse": [prompt]}})

    def test_repeated_install_is_idempotent_and_restores_original_agent(self):
        agents = self.root / ".claude" / "agents"
        agents.mkdir()
        (agents / "builder.md").write_text("my original agent")
        self.run_installer()
        installed = self.read_settings()
        self.run_installer()
        self.assertEqual(self.read_settings(), installed)
        self.run_installer("--uninstall")
        self.assertEqual((agents / "builder.md").read_text(), "my original agent")
        self.assertFalse(self.settings.exists())

    def test_dry_runs_leave_settings_and_agents_unchanged(self):
        original = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": OWN_COMMAND}
        ]}]}}
        self.write_settings(original)
        before = self.settings.read_bytes()
        self.run_installer("--dry-run")
        self.run_installer("--uninstall", "--purge", "--dry-run")
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertFalse((self.root / ".claude" / "agents").exists())
        self.assertFalse((self.root / ".1v1").exists())


if __name__ == "__main__":
    unittest.main()
