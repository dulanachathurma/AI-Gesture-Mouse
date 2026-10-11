# Changelog

All notable changes to **AI Gesture Mouse** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added — Voice Control Integration (Dulana Chathurma)
- **`src/voice_controller.py`** — new optional voice command module:
  - `VoiceCommand` enum with 12 command types
  - `VoiceEvent` dataclass (command, raw_text, confidence, timestamp)
  - `VoiceCommandHistory` session analytics helper (rolling deque, frequency counts, summary export)
  - `VoiceController` class with background listener thread, wake-word gating, confidence threshold filtering, sensitivity/pause state management, callback and polling interfaces
  - Graceful no-op degradation when `SpeechRecognition` / `PyAudio` are absent
- **`tests/test_voice_controller.py`** — 25 mocked unit tests covering all public API surfaces
- **`docs/VOICE_CONTROL.md`** — comprehensive integration guide
- **`config.json`** — `voice_control` configuration block added
- **`requirements.txt`** — optional voice control deps section added (commented-out)

### Changed
- `README.md` — added Dulana Chathurma (Member 4), Voice Control section, updated test count, updated deliverables table and navigation
- `docs/TEAM_WORK_SPLIT.md` — updated to four members, added Member 4 detailed task breakdown, updated test coverage count

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
