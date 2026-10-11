# Changelog

All notable changes to **AI Gesture Mouse** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] — Voice & Accessibility Release (2026-10-11)

### Added — Voice Control Subsystem (Lead: Dulana Chathurma)
- **`src/voice_controller.py`** — new optional voice command module:
  - `VoiceCommand` enum with 12 distinct system & mouse commands
  - `VoiceEvent` dataclass (command, raw_text, confidence, timestamp)
  - `VoiceCommandHistory` session analytics helper with rolling buffer, frequency telemetry, and JSON export
  - `VoiceController` class with multi-threaded audio listener, wake-word gating (`"gesture"`), and confidence filtering
  - `create_voice_controller_from_config(config)` factory helper
  - `is_speech_recognition_available()` runtime detection helper
  - Graceful zero-dependency fallback when `SpeechRecognition` / `PyAudio` are absent
- **`src/demo_voice.py`** — interactive CLI demo and validation utility:
  - Simulated text prompt mode for testing commands without microphone
  - Live microphone recognition mode via `--live` flag
  - Added `gesture-voice` CLI console script entry point
- **`tests/test_voice_controller.py`** & **`tests/test_demo_voice.py`** — 28 comprehensive automated unit test cases
- **`docs/VOICE_CONTROL.md`** — comprehensive integration and architectural guide
- **`.github/CODEOWNERS`** — module code ownership assignments

### Changed
- `src/__init__.py` — exported `VoiceController`, `VoiceCommand`, `VoiceEvent`, and bumped package `__version__ = "1.1.0"`
- `pyproject.toml` — bumped version to 1.1.0, added optional `voice` dependency extra, added `gesture-voice` entry point
- `config.json` — added `voice_control` configuration block
- `requirements.txt` — added optional voice control dependencies
- `README.md` — documented Member 4 Dulana Chathurma, added Voice Control subsystem guide, demo usage, and team details
- `CONTRIBUTING.md` — added module ownership table and voice control contribution guidelines
- `docs/TEAM_WORK_SPLIT.md` — updated team roster and detailed responsibilities for Dulana Chathurma

---

## [1.0.0] — Gate 3 Submission (2026-10-10)

### Added
- **Core gesture tracking pipeline**: 21 3D landmark extraction via Google MediaPipe
- **3-stage jitter suppression**: 3-point median buffer → 1-Euro adaptive low-pass filter → cubic Hermite deadzone easing
- **Gesture state machine**: Point, Two-Finger click, Thumbs-Up right-click, Open Hand double-click, 3-Finger scroll, Swipe navigation, Fist idle
- **850 ms transition guard** preventing accidental clicks on gesture exit
- **Always-On-Top HUD** using `WS_EX_TOPMOST` / `WS_EX_TOOLWINDOW` ctypes API
- **Dark-mode Tkinter launcher** with gesture cheatsheet and camera selector
- **Interactive calibration tool** (`src/calibration.py`) saving to `config.json`
- **Local session analytics** exporting `analytics_report.json`
- **37 automated unit tests** across 8 test files (100% passing)
- **Business Case**, **AI Usage Report**, and **Gate 3 README** deliverables

### Team — FutureStack (`802359D5`)
| Member | Role |
| :--- | :--- |
| Minindu Rajapaksha | Team Leader & Core AI / Systems Engineer |
| G.W. Sulochana Prabodhani Mihirangi De Silva | Co-Developer & QA Lead |
| Kavindu Gimshan | Co-Developer & UI/UX / Product Strategy |
| Dulana Chathurma | Co-Developer & Voice / Accessibility Engineer |
