"""
demo_voice.py — Interactive Voice Controller CLI Demo & Tester
===============================================================
Author: Dulana Chathurma (@dulana-chathurma)
Team: FutureStack | IntelliCon 2026

Interactive utility to test the VoiceController module without needing the
webcam or full gesture loop active. Supports both live microphone listening
(if SpeechRecognition is installed) and simulated phrase entry.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.voice_controller import (
    VoiceCommand,
    VoiceController,
    VoiceEvent,
    is_speech_recognition_available,
)


def print_banner() -> None:
    print("=" * 65)
    print("  AI Gesture Mouse — Voice Controller Interactive Demo")
    print("  Author: Dulana Chathurma (@dulana-chathurma) | Team FutureStack")
    print("=" * 65)


def run_interactive_simulation(controller: VoiceController) -> None:
    print("\n[Mode] Interactive Keyboard Simulation")
    print("Type spoken phrases to test command recognition (or 'quit' to exit).")
    print("Examples: 'click', 'double click', 'pause', 'scroll up', 'screenshot'\n")

    while True:
        try:
            line = input("Voice Prompt > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not line:
            continue
        if line.lower() in ("exit", "quit", "q"):
            print("Session ended.")
            break

        cmd = controller.parse_command(line)
        if cmd != VoiceCommand.UNKNOWN:
            event = VoiceEvent(
                command=cmd,
                raw_text=line,
                confidence=1.0,
                timestamp=time.time(),
            )
            controller.history.record(event)
            print(f"  -> Recognized Command: [{cmd.name}] (raw: '{line}')")
            print(f"     Action mapping: {cmd.value}")
        else:
            print(f"  -> Unrecognized: '{line}' (Confidence: N/A)")


def run_live_microphone(controller: VoiceController) -> None:
    if not is_speech_recognition_available():
        print("\n[!] SpeechRecognition is not installed.")
        print("    Install via: pip install SpeechRecognition pyaudio")
        print("    Falling back to simulation mode.\n")
        run_interactive_simulation(controller)
        return

    print("\n[Mode] Live Microphone Listening")
    print("Listening for speech in the background... Press Ctrl+C to stop.\n")

    def on_voice_event(event: VoiceEvent) -> None:
        print(f"\n[VOICE EVENT] Command: {event.command.name} | Text: '{event.raw_text}' | Confidence: {event.confidence:.2f}")

    controller.start(callback=on_voice_event)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping voice listener...")
    finally:
        controller.stop()
        print("Voice listener stopped successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the AI Gesture Mouse Voice Control subsystem."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real microphone with SpeechRecognition if available.",
    )
    parser.add_argument(
        "--language",
        default="en-US",
        help="Language code (default: en-US).",
    )
    parser.add_argument(
        "--energy-threshold",
        type=int,
        default=300,
        help="Microphone energy threshold (default: 300).",
    )
    args = parser.parse_args()

    print_banner()
    sr_status = "Available" if is_speech_recognition_available() else "Not Installed (simulation fallback)"
    print(f"SpeechRecognition status: {sr_status}")

    controller = VoiceController(
        enabled=True,
        language=args.language,
        energy_threshold=args.energy_threshold,
    )

    if args.live:
        run_live_microphone(controller)
    else:
        run_interactive_simulation(controller)


if __name__ == "__main__":
    main()
