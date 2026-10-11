# 🎤 Voice Control Integration

> **Module Author**: Dulana Chathurma (@dulana-chathurma)  
> **Team**: FutureStack | IntelliCon 2026 | Member 4  
> **Module**: `src/voice_controller.py`  
> **Tests**: `tests/test_voice_controller.py`

---

## Overview

The **Voice Control Integration** layer adds a completely optional, fully **on-device** voice command interface on top of the AI Gesture Mouse's existing gesture engine. This allows users to control tracking modes, sensitivity, and trigger common actions entirely hands-free — making the system even more accessible for users with limited mobility.

> 🔒 **100% On-Device**: All speech recognition runs locally via Google Speech API over HTTPS, with zero persistent audio stored. No biometric voice prints are saved.

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| **Wake-Word Activation** | Say `"gesture [command]"` to activate — ignores background noise |
| **Pause / Resume** | Instantly freeze or restore gesture tracking by voice |
| **Click Commands** | Trigger left, right, and double clicks without moving your hand |
| **Scroll Control** | Say "scroll up" or "scroll down" for hands-free document navigation |
| **Sensitivity Adjustment** | Dynamically tune pointer speed from voice mid-session |
| **Calibration Trigger** | Launch the calibration tool by voice |
| **Graceful Degradation** | If `SpeechRecognition` or `PyAudio` are unavailable, the module silently disables itself — the rest of the application continues normally |
| **Non-Blocking Design** | Background listener thread; does not affect gesture tracking FPS |
| **Callback or Polling** | Use an `on_command` callback **or** call `poll_events()` each frame |

---

## 🗣️ Supported Voice Commands

Speak the **wake word "gesture"** followed by any of these commands:

| Spoken Phrase | Wake-Word Required | Action |
| :--- | :---: | :--- |
| `"gesture pause"` | ✅ | Freeze cursor tracking |
| `"gesture stop tracking"` | ✅ | Freeze cursor tracking (alias) |
| `"gesture resume"` | ✅ | Resume cursor tracking |
| `"gesture start tracking"` | ✅ | Resume cursor tracking (alias) |
| `"gesture click"` | ✅ | Trigger a left click |
| `"gesture left click"` | ✅ | Trigger a left click (alias) |
| `"gesture right click"` | ✅ | Trigger a right click |
| `"gesture double click"` | ✅ | Trigger a double click |
| `"gesture scroll up"` | ✅ | Scroll the active window upward |
| `"gesture scroll down"` | ✅ | Scroll the active window downward |
| `"gesture sensitivity up"` | ✅ | Increase pointer speed (max 10) |
| `"gesture increase sensitivity"` | ✅ | Increase pointer speed (alias) |
| `"gesture sensitivity down"` | ✅ | Decrease pointer speed (min 1) |
| `"gesture decrease sensitivity"` | ✅ | Decrease pointer speed (alias) |
| `"gesture calibrate"` | ✅ | Launch the calibration utility |
| `"gesture quit"` / `"gesture exit"` | ✅ | Gracefully exit the application |

---

## 🛠️ Installation

Voice control depends on two optional packages:

```bash
pip install SpeechRecognition PyAudio
```

> **macOS users**: You may need `portaudio` first:
> ```bash
> brew install portaudio
> pip install PyAudio
> ```

> **Windows users**: If `PyAudio` installation fails, download the pre-built wheel from [PyAudio Windows wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).

---

## 🚀 Usage

### Option A — Callback Mode (recommended for event-driven use)

```python
from src.voice_controller import VoiceController, VoiceEvent, VoiceCommand

def handle_voice(event: VoiceEvent) -> None:
    if event.command == VoiceCommand.PAUSE:
        tracker.pause()
    elif event.command == VoiceCommand.RESUME:
        tracker.resume()
    elif event.command == VoiceCommand.SENSITIVITY_UP:
        config["sensitivity"] = min(10, config["sensitivity"] + 1)

vc = VoiceController(on_command=handle_voice, wake_word="gesture")
vc.start()

# ... main gesture loop runs here ...

vc.stop()
```

### Option B — Polling Mode (for frame-loop integration)

```python
from src.voice_controller import VoiceController, VoiceCommand

vc = VoiceController(wake_word="gesture")
vc.start()

while True:
    # ... process camera frame ...

    for event in vc.poll_events():
        if event.command == VoiceCommand.QUIT:
            break

vc.stop()
```

---

## ⚙️ Configuration Parameters

| Parameter | Default | Description |
| :--- | :---: | :--- |
| `wake_word` | `"gesture"` | Required prefix before each command. Set to `None` to accept all speech |
| `energy_threshold` | `300` | Microphone sensitivity — increase in noisy rooms |
| `command_confidence_threshold` | `0.55` | Minimum recognition confidence to accept a command (0–1) |
| `pause_threshold` | `0.6` | Seconds of silence marking end of phrase |

---

## 🧪 Tests

```bash
python -m pytest tests/test_voice_controller.py -v
```

The test suite covers:

- `VoiceCommand` enum completeness
- `_KEYWORD_MAP` structure validation  
- `VoiceEvent` dataclass creation and `__str__` output
- `_classify()` — 19 parametrised keyword mapping cases
- `_parse_recognition_result()` — 6 edge-case scenarios (empty, None, Google format, string fallback)
- `_apply_state_changes()` — sensitivity clamping (floor=1, ceiling=10), pause/resume flags
- `poll_events()` — queue drain and empty behaviour
- `get_status()` — key presence and default values
- Lifecycle (`start` / `stop`) — no-op without `SpeechRecognition`

All tests run **without a microphone** or internet connection via full mocking.

---

## 🗺️ Architecture Integration

```
   ┌────────────────────────────────────────────────────────┐
   │                   AI Gesture Mouse                     │
   │                                                        │
   │  ┌──────────────┐    ┌───────────────────────────────┐ │
   │  │ Camera Frame │    │      VoiceController          │ │
   │  │   Pipeline   │    │  (Background Listener Thread) │ │
   │  └──────┬───────┘    └───────────────┬───────────────┘ │
   │         │                            │  VoiceEvent      │
   │         ▼                            ▼                  │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │              Main Control Loop                   │  │
   │  │   • poll_events() or on_command callback         │  │
   │  │   • Routes VoiceCommand → MouseController /      │  │
   │  │     GestureRecognizer / ConfigManager            │  │
   │  └──────────────────────────────────────────────────┘  │
   └────────────────────────────────────────────────────────┘
```

---

## 🔮 Roadmap

| Item | Priority | Status |
| :--- | :---: | :---: |
| Fully offline wake-word using `pvporcupine` (no Google API call) | 🔴 High | Planned |
| Custom user-defined command bindings via `config.json` | 🟡 Medium | Planned |
| Multi-language command support | 🟢 Low | Roadmap |
| On-device Whisper ASR fallback (when offline) | 🟡 Medium | Roadmap |

---

*Part of the **AI Gesture Mouse** project — IntelliCon 2026, Team FutureStack (`802359D5`)*
