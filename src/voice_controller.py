"""
voice_controller.py — AI Gesture Mouse Voice Command Integration
================================================================
Author: Dulana Chathurma (@dulana-chathurma)
Team: FutureStack | IntelliCon 2026 | Member 4

Provides an optional voice-command layer on top of the gesture engine,
allowing users to control modes, sensitivity, and common actions using
spoken keywords — hands-free, fully on-device (no cloud API required).

Features
--------
* Wake-word detection ("gesture") to activate the listener.
* Keyword-based commands: pause, resume, scroll up/down, click, sensitivity.
* Adjustable confidence threshold for command acceptance.
* Non-blocking background listener thread that emits VoiceEvent objects.
* Graceful fallback: if SpeechRecognition / PyAudio are unavailable,
  VoiceController degrades silently and logs a warning.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional speech-recognition import — graceful fallback if not installed
# ---------------------------------------------------------------------------
try:
    import speech_recognition as sr  # type: ignore

    _SR_AVAILABLE = True
except ImportError:
    sr = None  # type: ignore
    _SR_AVAILABLE = False
    logger.warning(
        "SpeechRecognition library not found. "
        "Voice commands will be disabled. "
        "Install with: pip install SpeechRecognition PyAudio"
    )


# ---------------------------------------------------------------------------
# Public API: VoiceCommand & VoiceEvent
# ---------------------------------------------------------------------------


class VoiceCommand(Enum):
    """Enumeration of all supported voice commands."""

    PAUSE = auto()
    RESUME = auto()
    CLICK = auto()
    RIGHT_CLICK = auto()
    DOUBLE_CLICK = auto()
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()
    SENSITIVITY_UP = auto()
    SENSITIVITY_DOWN = auto()
    CALIBRATE = auto()
    QUIT = auto()
    UNKNOWN = auto()


# Maps spoken keywords → VoiceCommand (order matters — more specific first)
_KEYWORD_MAP: dict[str, VoiceCommand] = {
    "pause": VoiceCommand.PAUSE,
    "stop tracking": VoiceCommand.PAUSE,
    "resume": VoiceCommand.RESUME,
    "start tracking": VoiceCommand.RESUME,
    "click": VoiceCommand.CLICK,
    "left click": VoiceCommand.CLICK,
    "right click": VoiceCommand.RIGHT_CLICK,
    "double click": VoiceCommand.DOUBLE_CLICK,
    "scroll up": VoiceCommand.SCROLL_UP,
    "scroll down": VoiceCommand.SCROLL_DOWN,
    "sensitivity up": VoiceCommand.SENSITIVITY_UP,
    "increase sensitivity": VoiceCommand.SENSITIVITY_UP,
    "sensitivity down": VoiceCommand.SENSITIVITY_DOWN,
    "decrease sensitivity": VoiceCommand.SENSITIVITY_DOWN,
    "calibrate": VoiceCommand.CALIBRATE,
    "quit": VoiceCommand.QUIT,
    "exit": VoiceCommand.QUIT,
}


@dataclass
class VoiceEvent:
    """A recognised voice command event emitted by :class:`VoiceController`."""

    command: VoiceCommand
    raw_text: str
    confidence: float  # 0.0 – 1.0; 1.0 when no confidence score available
    timestamp: float = field(default_factory=time.monotonic)

    def __str__(self) -> str:
        return (
            f"VoiceEvent(cmd={self.command.name}, "
            f"text='{self.raw_text}', conf={self.confidence:.2f})"
        )


# ---------------------------------------------------------------------------
# VoiceCommandHistory — lightweight session analytics for voice events
# ---------------------------------------------------------------------------


class VoiceCommandHistory:
    """
    Rolling in-memory history of :class:`VoiceEvent` objects for the current
    session, used for analytics, debugging, and potential undo/replay logic.

    Parameters
    ----------
    maxlen:
        Maximum number of events stored (oldest are evicted, default 200).
    """

    def __init__(self, maxlen: int = 200) -> None:
        from collections import deque

        self._events: "deque[VoiceEvent]" = deque(maxlen=maxlen)
        self._command_counts: dict[VoiceCommand, int] = {}

    def record(self, event: VoiceEvent) -> None:
        """Append *event* to the history and update command frequency counts."""
        self._events.append(event)
        self._command_counts[event.command] = (
            self._command_counts.get(event.command, 0) + 1
        )

    def most_used(self) -> Optional[VoiceCommand]:
        """Return the :class:`VoiceCommand` issued most often this session."""
        if not self._command_counts:
            return None
        return max(self._command_counts, key=lambda c: self._command_counts[c])

    def summary(self) -> dict:
        """Return a serialisable session summary dict for analytics export."""
        return {
            "total_events": len(self._events),
            "command_counts": {cmd.name: cnt for cmd, cnt in self._command_counts.items()},
            "most_used": self.most_used().name if self.most_used() else None,
        }

    def clear(self) -> None:
        """Reset history and counters (e.g., between sessions)."""
        self._events.clear()
        self._command_counts.clear()

    def __len__(self) -> int:
        return len(self._events)


# ---------------------------------------------------------------------------
# VoiceController
# ---------------------------------------------------------------------------


class VoiceController:
    """
    Background voice-command listener for AI Gesture Mouse.

    Usage
    -----
    >>> vc = VoiceController(on_command=handle_voice_event)
    >>> vc.start()
    ...
    >>> vc.stop()

    Parameters
    ----------
    on_command:
        Callback invoked (from the listener thread) whenever a recognised
        ``VoiceEvent`` is available.  Must be thread-safe.
    wake_word:
        Optional prefix that must appear in transcription before a command
        is accepted.  Set to ``None`` to accept any transcription.
    energy_threshold:
        Microphone energy threshold forwarded to the underlying recogniser.
        Increase for noisy environments (default 300).
    command_confidence_threshold:
        Minimum Google Speech confidence (0–1) required to accept a result.
        Only applied when the recogniser returns confidence data.
    pause_threshold:
        Seconds of silence that mark the end of a phrase (default 0.6 s).
    """

    def __init__(
        self,
        on_command: Optional[Callable[[VoiceEvent], None]] = None,
        wake_word: str = "gesture",
        energy_threshold: int = 300,
        command_confidence_threshold: float = 0.55,
        pause_threshold: float = 0.6,
    ) -> None:
        self._on_command = on_command
        self._wake_word = wake_word.lower() if wake_word else None
        self._energy_threshold = energy_threshold
        self._conf_threshold = command_confidence_threshold
        self._pause_threshold = pause_threshold

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._event_queue: queue.Queue[VoiceEvent] = queue.Queue()

        # State
        self._paused_by_voice = False
        self._sensitivity_level: int = 5  # 1 (min) – 10 (max)

        if not _SR_AVAILABLE:
            logger.warning("VoiceController initialised without SpeechRecognition — no-op mode.")

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """
        Start the background listener thread.

        Returns ``True`` if started successfully, ``False`` if the
        ``SpeechRecognition`` library is unavailable.
        """
        if not _SR_AVAILABLE:
            logger.info("Voice control not started — SpeechRecognition unavailable.")
            return False

        if self._running:
            logger.warning("VoiceController already running.")
            return True

        self._running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            name="VoiceControllerThread",
            daemon=True,
        )
        self._thread.start()
        logger.info("VoiceController started (wake_word=%r).", self._wake_word)
        return True

    def stop(self) -> None:
        """Signal the listener thread to stop and wait for it to exit."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("VoiceController stopped.")

    @property
    def is_running(self) -> bool:
        return self._running and bool(self._thread and self._thread.is_alive())

    @property
    def sensitivity_level(self) -> int:
        """Current sensitivity level (1–10). Thread-safe read."""
        return self._sensitivity_level

    # ------------------------------------------------------------------
    # Internal: background listen loop
    # ------------------------------------------------------------------

    def _listen_loop(self) -> None:
        """Continuous background microphone listen loop."""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self._energy_threshold
        recognizer.pause_threshold = self._pause_threshold
        recognizer.dynamic_energy_threshold = True

        try:
            mic = sr.Microphone()
        except OSError as exc:
            logger.error("Cannot open microphone: %s. Voice control disabled.", exc)
            self._running = False
            return

        logger.info("VoiceController: adjusting for ambient noise…")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
        logger.info(
            "VoiceController: ambient calibrated (energy_threshold=%.0f). Listening…",
            recognizer.energy_threshold,
        )

        while self._running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=5.0, phrase_time_limit=4.0)
            except sr.WaitTimeoutError:
                continue  # no speech detected — loop again
            except Exception as exc:  # noqa: BLE001
                logger.debug("Microphone read error: %s", exc)
                time.sleep(0.1)
                continue

            # Run recognition in a sub-thread to avoid blocking the mic
            threading.Thread(
                target=self._recognise_and_dispatch,
                args=(recognizer, audio),
                daemon=True,
            ).start()

    def _recognise_and_dispatch(
        self,
        recognizer: "sr.Recognizer",  # type: ignore[name-defined]
        audio: "sr.AudioData",  # type: ignore[name-defined]
    ) -> None:
        """Attempt to recognise *audio* and dispatch a :class:`VoiceEvent`."""
        try:
            result = recognizer.recognize_google(audio, show_all=True)
        except sr.UnknownValueError:
            return  # unintelligible audio — silently ignore
        except sr.RequestError as exc:
            logger.warning("Google Speech API error: %s", exc)
            return

        text, confidence = self._parse_recognition_result(result)
        if not text:
            return

        text_lower = text.lower().strip()
        logger.debug("Recognised: '%s' (conf=%.2f)", text_lower, confidence)

        # Wake-word gate
        if self._wake_word and self._wake_word not in text_lower:
            return

        # Strip wake word for cleaner keyword matching
        if self._wake_word:
            text_lower = text_lower.replace(self._wake_word, "").strip()

        # Confidence gate
        if confidence < self._conf_threshold:
            logger.debug("Confidence %.2f below threshold %.2f — rejected.", confidence, self._conf_threshold)
            return

        command = self._classify(text_lower)
        event = VoiceEvent(command=command, raw_text=text, confidence=confidence)

        logger.info("VoiceEvent: %s", event)
        self._apply_state_changes(event)
        self._event_queue.put(event)

        if self._on_command:
            try:
                self._on_command(event)
            except Exception as exc:  # noqa: BLE001
                logger.error("on_command callback raised: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_recognition_result(result: object) -> tuple[str, float]:
        """
        Extract (text, confidence) from the Google ``show_all=True`` payload.

        Falls back to (``""``, ``0.0``) on empty / unexpected format.
        """
        if not result:
            return "", 0.0

        if isinstance(result, dict):
            alternatives = result.get("alternative", [])
            if alternatives:
                top = alternatives[0]
                text = top.get("transcript", "")
                confidence = float(top.get("confidence", 1.0))
                return text, confidence
        elif isinstance(result, str):
            return result, 1.0

        return "", 0.0

    @staticmethod
    def _classify(text: str) -> VoiceCommand:
        """Map *text* to the best-matching :class:`VoiceCommand`."""
        for keyword, command in _KEYWORD_MAP.items():
            if keyword in text:
                return command
        return VoiceCommand.UNKNOWN

    def _apply_state_changes(self, event: VoiceEvent) -> None:
        """Apply internal state transitions driven by the command."""
        if event.command == VoiceCommand.SENSITIVITY_UP:
            self._sensitivity_level = min(10, self._sensitivity_level + 1)
            logger.info("Voice → sensitivity level: %d", self._sensitivity_level)

        elif event.command == VoiceCommand.SENSITIVITY_DOWN:
            self._sensitivity_level = max(1, self._sensitivity_level - 1)
            logger.info("Voice → sensitivity level: %d", self._sensitivity_level)

        elif event.command == VoiceCommand.PAUSE:
            self._paused_by_voice = True
            logger.info("Voice → tracking PAUSED")

        elif event.command == VoiceCommand.RESUME:
            self._paused_by_voice = False
            logger.info("Voice → tracking RESUMED")

    # ------------------------------------------------------------------
    # Utility: drain event queue (for polling-style consumers)
    # ------------------------------------------------------------------

    def poll_events(self) -> list[VoiceEvent]:
        """
        Return all pending :class:`VoiceEvent` objects without blocking.

        Suitable for frame-loop consumers that prefer polling over callbacks.
        """
        events: list[VoiceEvent] = []
        while True:
            try:
                events.append(self._event_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def get_status(self) -> dict:
        """Return a snapshot of the controller's current state."""
        return {
            "running": self.is_running,
            "sr_available": _SR_AVAILABLE,
            "wake_word": self._wake_word,
            "sensitivity_level": self._sensitivity_level,
            "paused_by_voice": self._paused_by_voice,
            "pending_events": self._event_queue.qsize(),
        }


# ---------------------------------------------------------------------------
# Module-level convenience factory
# ---------------------------------------------------------------------------


def create_voice_controller_from_config(config: dict) -> "VoiceController":
    """
    Instantiate a :class:`VoiceController` from the project's ``config.json``
    ``voice_control`` sub-dict.

    Example
    -------
    >>> import json
    >>> cfg = json.load(open("config.json"))
    >>> vc = create_voice_controller_from_config(cfg)
    >>> vc.start()

    Parameters
    ----------
    config:
        The full parsed ``config.json`` dictionary.  The ``voice_control``
        key is optional — if absent, default values are used.

    Returns
    -------
    VoiceController
        A configured (but not yet started) controller instance.
    """
    vc_cfg = config.get("voice_control", {})
    return VoiceController(
        wake_word=vc_cfg.get("wake_word", "gesture"),
        energy_threshold=int(vc_cfg.get("energy_threshold", 300)),
        command_confidence_threshold=float(vc_cfg.get("command_confidence_threshold", 0.55)),
        pause_threshold=float(vc_cfg.get("pause_threshold", 0.6)),
    )
