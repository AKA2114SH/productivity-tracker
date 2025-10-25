# ⏱️ Productivity Tracker

A cross-platform desktop productivity/time tracker with automatic idle detection, break management, system sleep/shutdown handling, Windows startup integration, and detailed activity logging.

## Features

- **Clock In/Out**: Track working sessions manually
- **Break Management**: Pause/resume work, tracks break time
- **Idle Detection**: Automatic clock-out after a configurable period of inactivity
- **Activity Monitoring**: Keyboard/mouse activity monitoring via [pynput]
- **System Integration**: Detects sleep, shutdown, lock/unlock (Windows APIs)
- **Auto-Start on Windows**: Optionally add/remove from startup via registry
- **Activity Logging**: Persists logs in both JSON and CSV for reporting
- **Recover from Unexpected Shutdown**: Session restored or auto-clocked-out/in
- **Configurable**: Tweak idle timeout in UI
- **Cross-platform**: Windows, macOS, Linux (with fallbacks)

## Installation

Clone the repo:

