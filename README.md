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

git clone https://github.com/AKA2114SH/productivity-tracker.git
cd productivity-tracker


Install requirements:
pip install -r requirements.txt


> For advanced Windows system events, install `pywin32` as well (already in requirements).

---

## Usage

Run the app:


python productivity_tracker.py


python productivity_tracker.py

python productivity_tracker.py --enable-startup # Add to Windows startup
python productivity_tracker.py --disable-startup # Remove from startup



---

## Build Windows EXE

pyinstaller --onefile --windowed --icon=tracker.ico productivity_tracker.py


Your EXE is created in the `dist/` folder.  
To include resource/config/log files in your .exe, use `--add-data` options.

---

## Log and Config Files

- `activity_log.json` – detailed event logs
- `activity_log.csv` – summary log for analytics or Excel/Sheets
- `tracker_config.json` – stores user/session state, idle config, etc.

---

## Configuration

- Change idle timeout, check intervals directly in the UI or `tracker_config.json`.
- On macOS/Linux, granting Accessibility permission may be required for full activity monitoring.

---

## Author

**Akash Khatale** ([AKA2114SH](https://github.com/AKA2114SH))

---

## License

MIT License

---

## Notes

- For GitHub uploads: Only add code, config, and log files, not the built `.exe`.
- For best practices, include a `.gitignore`:
    ```
    *.exe
    __pycache__/
    build/
    dist/
    *.spec
    *.log
    ```
---

**Enjoy accurate time tracking with automated system integration and professional logging!**
