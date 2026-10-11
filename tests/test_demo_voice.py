"""
test_demo_voice.py — Unit Tests for Voice Demo CLI
===================================================
Author: Dulana Chathurma (@dulana-chathurma)
Team: FutureStack | IntelliCon 2026
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.demo_voice import main, run_interactive_simulation
from src.voice_controller import VoiceCommand, VoiceController


class TestDemoVoice(unittest.TestCase):
    """Test the CLI flags and interactive simulation functions in demo_voice."""

    def setUp(self) -> None:
        self.controller = VoiceController(enabled=True)

    @patch("builtins.input", side_effect=["click", "scroll up", "quit"])
    def test_run_interactive_simulation_recognized(self, mock_input: MagicMock) -> None:
        """Should record recognized voice commands into history."""
        run_interactive_simulation(self.controller)
        history = self.controller.history.to_list()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["command"], VoiceCommand.CLICK.name)
        self.assertEqual(history[1]["command"], VoiceCommand.SCROLL_UP.name)

    @patch("builtins.input", side_effect=["gibberish unrecognized phrase", "quit"])
    def test_run_interactive_simulation_unknown(self, mock_input: MagicMock) -> None:
        """Unknown phrases should not add recognized commands to history."""
        run_interactive_simulation(self.controller)
        self.assertEqual(len(self.controller.history), 0)

    @patch("sys.argv", ["demo_voice.py", "--help"])
    def test_main_help_flag(self) -> None:
        """--help flag should trigger SystemExit with code 0."""
        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
