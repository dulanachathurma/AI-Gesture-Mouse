"""
test_voice_controller.py — Unit Tests for VoiceController
==========================================================
Author: Dulana Chathurma (@dulana-chathurma)
Team: FutureStack | IntelliCon 2026

Tests the voice command parsing, classification, state management,
and event queue logic — all without requiring a real microphone or
internet connection (fully mocked).
"""

from __future__ import annotations

import queue
import time
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# We test the module independently of SpeechRecognition being installed
# by patching the import before loading the module under test.
# ---------------------------------------------------------------------------
from src.voice_controller import (
    VoiceCommand,
    VoiceController,
    VoiceEvent,
    _KEYWORD_MAP,
    _SR_AVAILABLE,
)


# ===========================================================================
# VoiceCommand Enum
# ===========================================================================


class TestVoiceCommandEnum:
    """Verify the VoiceCommand enum has the expected members."""

    def test_all_expected_commands_present(self) -> None:
        expected = {
            "PAUSE",
            "RESUME",
            "CLICK",
            "RIGHT_CLICK",
            "DOUBLE_CLICK",
            "SCROLL_UP",
            "SCROLL_DOWN",
            "SENSITIVITY_UP",
            "SENSITIVITY_DOWN",
            "CALIBRATE",
            "QUIT",
            "UNKNOWN",
        }
        actual = {cmd.name for cmd in VoiceCommand}
        assert expected == actual

    def test_unknown_is_a_member(self) -> None:
        assert VoiceCommand.UNKNOWN in VoiceCommand


# ===========================================================================
# Keyword map
# ===========================================================================


class TestKeywordMap:
    def test_keyword_map_non_empty(self) -> None:
        assert len(_KEYWORD_MAP) > 0

    def test_all_values_are_voice_commands(self) -> None:
        for key, val in _KEYWORD_MAP.items():
            assert isinstance(key, str), f"Key '{key}' is not a string"
            assert isinstance(val, VoiceCommand), f"Value for '{key}' is not a VoiceCommand"

    def test_known_keywords_present(self) -> None:
        assert "pause" in _KEYWORD_MAP
        assert "resume" in _KEYWORD_MAP
        assert "click" in _KEYWORD_MAP
        assert "scroll up" in _KEYWORD_MAP
        assert "scroll down" in _KEYWORD_MAP
        assert "quit" in _KEYWORD_MAP


# ===========================================================================
# VoiceEvent dataclass
# ===========================================================================


class TestVoiceEvent:
    def test_creation_with_defaults(self) -> None:
        event = VoiceEvent(
            command=VoiceCommand.CLICK,
            raw_text="click",
            confidence=0.9,
        )
        assert event.command == VoiceCommand.CLICK
        assert event.raw_text == "click"
        assert event.confidence == pytest.approx(0.9)
        assert event.timestamp > 0

    def test_str_representation(self) -> None:
        event = VoiceEvent(command=VoiceCommand.PAUSE, raw_text="pause", confidence=0.75)
        text = str(event)
        assert "PAUSE" in text
        assert "pause" in text
        assert "0.75" in text

    def test_timestamp_is_monotonic(self) -> None:
        t0 = time.monotonic()
        event = VoiceEvent(command=VoiceCommand.RESUME, raw_text="resume", confidence=1.0)
        t1 = time.monotonic()
        assert t0 <= event.timestamp <= t1


# ===========================================================================
# VoiceController._classify
# ===========================================================================


class TestClassify:
    """Test the static keyword → VoiceCommand classifier."""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("pause", VoiceCommand.PAUSE),
            ("stop tracking", VoiceCommand.PAUSE),
            ("resume", VoiceCommand.RESUME),
            ("start tracking", VoiceCommand.RESUME),
            ("click", VoiceCommand.CLICK),
            ("left click", VoiceCommand.CLICK),
            ("right click", VoiceCommand.RIGHT_CLICK),
            ("double click", VoiceCommand.DOUBLE_CLICK),
            ("scroll up", VoiceCommand.SCROLL_UP),
            ("scroll down", VoiceCommand.SCROLL_DOWN),
            ("sensitivity up", VoiceCommand.SENSITIVITY_UP),
            ("increase sensitivity", VoiceCommand.SENSITIVITY_UP),
            ("sensitivity down", VoiceCommand.SENSITIVITY_DOWN),
            ("decrease sensitivity", VoiceCommand.SENSITIVITY_DOWN),
            ("calibrate", VoiceCommand.CALIBRATE),
            ("quit", VoiceCommand.QUIT),
            ("exit", VoiceCommand.QUIT),
            ("xyzzy unknown command", VoiceCommand.UNKNOWN),
            ("", VoiceCommand.UNKNOWN),
        ],
    )
    def test_classify(self, text: str, expected: VoiceCommand) -> None:
        result = VoiceController._classify(text)
        assert result == expected, f"classify({text!r}) → {result.name}, expected {expected.name}"


# ===========================================================================
# VoiceController._parse_recognition_result
# ===========================================================================


class TestParseRecognitionResult:
    def test_empty_result_returns_empty(self) -> None:
        text, conf = VoiceController._parse_recognition_result({})
        assert text == ""
        assert conf == 0.0

    def test_none_returns_empty(self) -> None:
        text, conf = VoiceController._parse_recognition_result(None)
        assert text == ""
        assert conf == 0.0

    def test_google_format_with_confidence(self) -> None:
        result = {"alternative": [{"transcript": "scroll up", "confidence": 0.87}]}
        text, conf = VoiceController._parse_recognition_result(result)
        assert text == "scroll up"
        assert conf == pytest.approx(0.87)

    def test_google_format_without_confidence(self) -> None:
        result = {"alternative": [{"transcript": "pause"}]}
        text, conf = VoiceController._parse_recognition_result(result)
        assert text == "pause"
        assert conf == pytest.approx(1.0)

    def test_string_result(self) -> None:
        text, conf = VoiceController._parse_recognition_result("click")
        assert text == "click"
        assert conf == pytest.approx(1.0)

    def test_multiple_alternatives_uses_first(self) -> None:
        result = {
            "alternative": [
                {"transcript": "scroll up", "confidence": 0.9},
                {"transcript": "scroll", "confidence": 0.6},
            ]
        }
        text, conf = VoiceController._parse_recognition_result(result)
        assert text == "scroll up"
        assert conf == pytest.approx(0.9)


# ===========================================================================
# VoiceController state management (_apply_state_changes)
# ===========================================================================


class TestApplyStateChanges:
    def _make_controller(self) -> VoiceController:
        return VoiceController(wake_word=None)

    def test_sensitivity_up_increments(self) -> None:
        vc = self._make_controller()
        initial = vc.sensitivity_level
        event = VoiceEvent(VoiceCommand.SENSITIVITY_UP, "sensitivity up", 1.0)
        vc._apply_state_changes(event)
        assert vc.sensitivity_level == initial + 1

    def test_sensitivity_up_caps_at_10(self) -> None:
        vc = self._make_controller()
        vc._sensitivity_level = 10
        event = VoiceEvent(VoiceCommand.SENSITIVITY_UP, "sensitivity up", 1.0)
        vc._apply_state_changes(event)
        assert vc.sensitivity_level == 10

    def test_sensitivity_down_decrements(self) -> None:
        vc = self._make_controller()
        vc._sensitivity_level = 5
        event = VoiceEvent(VoiceCommand.SENSITIVITY_DOWN, "sensitivity down", 1.0)
        vc._apply_state_changes(event)
        assert vc.sensitivity_level == 4

    def test_sensitivity_down_floors_at_1(self) -> None:
        vc = self._make_controller()
        vc._sensitivity_level = 1
        event = VoiceEvent(VoiceCommand.SENSITIVITY_DOWN, "sensitivity down", 1.0)
        vc._apply_state_changes(event)
        assert vc.sensitivity_level == 1

    def test_pause_sets_paused_flag(self) -> None:
        vc = self._make_controller()
        event = VoiceEvent(VoiceCommand.PAUSE, "pause", 1.0)
        vc._apply_state_changes(event)
        assert vc._paused_by_voice is True

    def test_resume_clears_paused_flag(self) -> None:
        vc = self._make_controller()
        vc._paused_by_voice = True
        event = VoiceEvent(VoiceCommand.RESUME, "resume", 1.0)
        vc._apply_state_changes(event)
        assert vc._paused_by_voice is False


# ===========================================================================
# VoiceController poll_events
# ===========================================================================


class TestPollEvents:
    def test_poll_returns_empty_when_no_events(self) -> None:
        vc = VoiceController(wake_word=None)
        assert vc.poll_events() == []

    def test_poll_drains_all_queued_events(self) -> None:
        vc = VoiceController(wake_word=None)
        e1 = VoiceEvent(VoiceCommand.CLICK, "click", 0.9)
        e2 = VoiceEvent(VoiceCommand.PAUSE, "pause", 0.95)
        vc._event_queue.put(e1)
        vc._event_queue.put(e2)

        events = vc.poll_events()
        assert len(events) == 2
        assert events[0] == e1
        assert events[1] == e2

    def test_queue_empty_after_poll(self) -> None:
        vc = VoiceController(wake_word=None)
        vc._event_queue.put(VoiceEvent(VoiceCommand.QUIT, "quit", 1.0))
        vc.poll_events()
        assert vc._event_queue.empty()


# ===========================================================================
# VoiceController get_status
# ===========================================================================


class TestGetStatus:
    def test_status_keys(self) -> None:
        vc = VoiceController(wake_word="gesture")
        status = vc.get_status()
        expected_keys = {
            "running",
            "sr_available",
            "wake_word",
            "sensitivity_level",
            "paused_by_voice",
            "pending_events",
        }
        assert expected_keys.issubset(status.keys())

    def test_status_defaults(self) -> None:
        vc = VoiceController(wake_word="gesture")
        status = vc.get_status()
        assert status["running"] is False
        assert status["wake_word"] == "gesture"
        assert status["sensitivity_level"] == 5
        assert status["paused_by_voice"] is False
        assert status["pending_events"] == 0

    def test_sr_available_key_matches_module_flag(self) -> None:
        vc = VoiceController()
        status = vc.get_status()
        assert status["sr_available"] == _SR_AVAILABLE


# ===========================================================================
# VoiceController lifecycle (no-op without SpeechRecognition)
# ===========================================================================


class TestLifecycle:
    def test_start_returns_false_when_sr_unavailable(self) -> None:
        with patch("src.voice_controller._SR_AVAILABLE", False):
            vc = VoiceController()
            result = vc.start()
            assert result is False

    def test_stop_does_not_raise_when_not_started(self) -> None:
        vc = VoiceController()
        vc.stop()  # should not raise

    def test_is_running_false_before_start(self) -> None:
        vc = VoiceController()
        assert vc.is_running is False


# ===========================================================================
# VoiceCommandHistory (added in refactor)
# ===========================================================================


class TestVoiceCommandHistory:
    """Tests for the VoiceCommandHistory analytics helper."""

    def _make_event(self, cmd: VoiceCommand, conf: float = 1.0) -> VoiceEvent:
        return VoiceEvent(command=cmd, raw_text=cmd.name.lower(), confidence=conf)

    def test_initial_length_is_zero(self) -> None:
        from src.voice_controller import VoiceCommandHistory

        h = VoiceCommandHistory()
        assert len(h) == 0

    def test_record_increases_length(self) -> None:
        from src.voice_controller import VoiceCommandHistory

        h = VoiceCommandHistory()
        h.record(self._make_event(VoiceCommand.CLICK))
        assert len(h) == 1

    def test_most_used_returns_correct_command(self) -> None:
        from src.voice_controller import VoiceCommandHistory

        h = VoiceCommandHistory()
        for _ in range(3):
            h.record(self._make_event(VoiceCommand.SCROLL_UP))
        h.record(self._make_event(VoiceCommand.PAUSE))
        assert h.most_used() == VoiceCommand.SCROLL_UP

    def test_most_used_returns_none_when_empty(self) -> None:
        from src.voice_controller import VoiceCommandHistory

        h = VoiceCommandHistory()
        assert h.most_used() is None

    def test_summary_keys(self) -> None:
        from src.voice_controller import VoiceCommandHistory

        h = VoiceCommandHistory()
        h.record(self._make_event(VoiceCommand.CLICK))
        summary = h.summary()
        assert "total_events" in summary
        assert "command_counts" in summary
        assert "most_used" in summary

    def test_clear_resets_state(self) -> None:
        from src.voice_controller import VoiceCommandHistory

        h = VoiceCommandHistory()
        h.record(self._make_event(VoiceCommand.QUIT))
        h.clear()
        assert len(h) == 0
        assert h.most_used() is None

    def test_maxlen_eviction(self) -> None:
        from src.voice_controller import VoiceCommandHistory

        h = VoiceCommandHistory(maxlen=3)
        for _ in range(5):
            h.record(self._make_event(VoiceCommand.RESUME))
        assert len(h) == 3
