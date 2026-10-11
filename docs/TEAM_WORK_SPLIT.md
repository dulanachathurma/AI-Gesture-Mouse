# 👥 Team Work Distribution & Task Split

This document outlines the division of development tasks for **AI Gesture Mouse** (IntelliCon '26 Project — Team FutureStack, Code: `802359D5`) across four core team members.

---

## 🎯 Overview & Architectural Responsibility Split

```
                              ┌─────────────────────────────────────────┐
                              │     AI GESTURE MOUSE (FutureStack)      │
                              └─────────────────────────────────────────┘
                                                   │
         ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
         │                                         │                                         │
         ▼                                         ▼                                         ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│   MEMBER 1: TEAM LEADER & AI    │   │  MEMBER 2: GESTURES & QA        │   │    MEMBER 3: UX/UI & HUD        │
│      (Minindu Rajapaksha)       │   │ (G.W. Sulochana P. M. De Silva) │   │        (Kavindu Gimshan)        │
│       @Rajapakshaminindu        │   │          @Mihirangi315          │   │         @kavindugimshan         │
├─────────────────────────────────┤   ├─────────────────────────────────┤   ├─────────────────────────────────┤
│ • Action Mapping Engine         │   │ • Gesture Recognition Filters   │   │ • HUD Live Dashboard Overlay    │
│ • Custom Hotkeys & Actions      │   │ • Per-Gesture Debounce Engine   │   │ • Landmark Calibration Tool     │
│ • 1-Euro Adaptive Stabilization │   │ • Directional Swipe Dynamics    │   │ • Startup Splash Screen         │
│ • Gesture Analytics Telemetry   │   │ • Confidence Threshold Gating   │   │ • Interactive Visual Feedback   │
└─────────────────────────────────┘   └─────────────────────────────────┘   └─────────────────────────────────┘

                                  ┌─────────────────────────────────┐
                                  │  MEMBER 4: VOICE & ACCESS.      │
                                  │      (Dulana Chathurma)         │
                                  │      @dulana-chathurma          │
                                  ├─────────────────────────────────┤
                                  │ • Voice Command Engine          │
                                  │ • Wake-Word Listener            │
                                  │ • Confidence Threshold Gating   │
                                  │ • Sensitivity Voice Control     │
                                  └─────────────────────────────────┘
```

---

## 👤 Member 1: Minindu Rajapaksha (@Rajapakshaminindu) — Team Leader & Core AI Engineer

### 📌 Focus Area: System Architecture, 1-Euro Smoothing, Action Mapping & Telemetry
**Status**: 🟢 Completed & Integrated into `main`

### Assigned Tasks & Modules:
1. **Dynamic Action Mapping Engine (`src/action_mapper.py`)**:
   - Implemented configurable action mapping layer to bind recognized gestures to system actions, keyboard shortcuts (`Ctrl+C`, `Ctrl+V`, `Alt+Tab`), media controls, and custom OS triggers.
2. **1-Euro Adaptive Velocity-Based Smoothing (`src/mouse_controller.py`)**:
   - Dynamic 1-Euro filter and 3-point median buffer based on Instantaneous Hand Velocity. Uses high tremor absorption for fine precision during micro-movements and low smoothing during fast flicks.
3. **Session Analytics & Telemetry Engine (`src/analytics.py`)**:
   - Real-time logging of active gesture frequency, stroke speed, landmark confidence tracking, and session report exporter (`analytics_report.json`).
4. **Configuration Validation Engine (`src/config.py`)**:
   - Schema filtering and parameter clamping to prevent crashes from unrecognized settings.
5. **AI Engine Unit Tests (`tests/test_action_mapper.py`, `tests/test_adaptive_smoothing.py`, `tests/test_analytics.py`, `tests/test_config.py`)**:
   - Full unit test coverage for action dispatching, dynamic velocity scaling, and metrics collection.

---

## 👤 Member 2: G.W. Sulochana Prabodhani Mihirangi De Silva (@Mihirangi315) — Gesture Recognition & QA

### 📌 Focus Area: Gesture Detection Enhancement, Debounce Logic & Test QA
**Status**: 🟢 Completed & Merged into `main` (`src/gesture_recognizer.py`, `tests/test_gesture_enhancements.py`)

### Assigned Tasks & Modules:
1. **Confidence Threshold Gating (`src/gesture_recognizer.py`)**:
   - Implemented confidence verification to suppress false positives when hand detection quality is low.
2. **Per-Gesture Debounce & Cooldown Logic (`src/gesture_recognizer.py`)**:
   - Implemented cooldown timers per gesture type to prevent rapid unintentional double triggers.
3. **Horizontal Swipe Detection (`src/gesture_recognizer.py`)**:
   - Dynamic tracking of horizontal fingertip velocity for left/right browser page swipes.
4. **Gesture Test Suite (`tests/test_gesture_enhancements.py`)**:
   - Comprehensive automated unit tests for swipe detection, debounce cooldowns, and confidence gating.

---

## 👤 Member 3: Kavindu Gimshan (@kavindugimshan) — UX/UI, Dashboard & Calibration

### 📌 Focus Area: Live Camera HUD Overlay, Cursor Diagnostics & Calibration
**Status**: 🟢 Completed & Merged into `main` (`src/main.py`, `src/calibration.py`)

### Assigned Tasks & Modules:
1. **HUD Overlay & Live Diagnostics (`src/main.py`)**:
   - Real-time gesture state badges, active bounding box guide, cursor preview, and FPS counter.
2. **Webcam Landmark Calibration Tool (`src/calibration.py`)**:
   - Interactive pinch and scroll threshold measurement tool with visual progress bars.
3. **Startup Splash Screen (`src/main.py`)**:
   - Alpha-blended onboarding splash screen displaying instructions on startup.

---

## 🛠️ Repository Architecture & Status

- **`main`**: Single unified, authoritative production branch.
- **Test Coverage**: **55 / 55 unit tests passing (100% green)**.
- **Collaborators**: All team member commits are preserved in the git history of `main`.

---

## 👤 Member 4: Dulana Chathurma (@dulana-chathurma) — Voice Control & Accessibility Engineer

### 📌 Focus Area: On-Device Voice Command Integration, Accessibility & Test Automation
**Status**: 🟢 Completed & Integrated into `main` (`src/voice_controller.py`, `tests/test_voice_controller.py`, `docs/VOICE_CONTROL.md`)

### Assigned Tasks & Modules:
1. **Voice Command Engine (`src/voice_controller.py`)**:
   - Designed and implemented the complete `VoiceController` class with background listener thread, wake-word gating, keyword classification, confidence threshold filtering, and graceful degradation when `SpeechRecognition` / `PyAudio` are not installed.
   - Supports both callback (`on_command`) and frame-polling (`poll_events()`) integration patterns.
2. **VoiceCommand Classification System**:
   - Defined the `VoiceCommand` enum (12 commands) and `_KEYWORD_MAP` (14 keyword → command mappings) covering pause/resume, click variants, scroll, sensitivity adjustment, calibration trigger, and quit.
3. **Event Data Model (`VoiceEvent`)**:
   - Implemented the `VoiceEvent` dataclass carrying command, raw transcript, recognition confidence, and monotonic timestamp for reliable event tracing and testing.
4. **Sensitivity & State Management**:
   - Built internal state machine handling pause/resume tracking flags and bounded sensitivity level (1–10) adjustable live by voice without restarting the application.
5. **Voice Control Test Suite (`tests/test_voice_controller.py`)**:
   - 18 fully mocked automated unit tests covering: enum completeness, keyword map structure, event creation, `_classify()` (19 parametrised cases), `_parse_recognition_result()` (6 edge cases), `_apply_state_changes()` (6 cases), `poll_events()` (3 cases), `get_status()` (3 cases), and lifecycle management.
6. **Voice Control Documentation (`docs/VOICE_CONTROL.md`)**:
   - Comprehensive integration guide including command table, installation steps for macOS/Windows, callback and polling usage examples, configuration parameters, architecture diagram, and feature roadmap.
