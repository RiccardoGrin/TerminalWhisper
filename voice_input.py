#!/usr/bin/env python3
"""
TerminalWhisper - Voice input tool for terminal.

Hold Ctrl+` to record, release to transcribe and paste.
"""

import ctypes
import logging
import os
import sys
import threading
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from text_injector import TextInjector
from hotkey_manager import HotkeyManager
from tray_icon import TrayIcon, TrayState
from power_monitor import PowerMonitor

log = logging.getLogger(__name__)

# Log directory: %APPDATA%\TerminalWhisper (guaranteed writable)
_LOG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "TerminalWhisper")
_LOG_FILE = os.path.join(_LOG_DIR, "terminal_whisper.log")


def _setup_logging():
    """Configure file-based logging to %APPDATA%\\TerminalWhisper."""
    from logging.handlers import RotatingFileHandler
    os.makedirs(_LOG_DIR, exist_ok=True)
    handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    # Suppress noisy PIL debug logs
    logging.getLogger("PIL").setLevel(logging.WARNING)


class VoiceInputApp:
    """Main application coordinating all components."""

    def __init__(self):
        self._recorder = AudioRecorder()
        self._transcriber = Transcriber()
        self._injector = TextInjector()
        self._tray = TrayIcon(
            on_exit=self._shutdown,
            on_restart=self._on_restart,
            on_view_log=self._on_view_log,
        )
        self._hotkey = HotkeyManager(
            on_press=self._on_record_start,
            on_release=self._on_record_stop,
            on_status_change=self._on_hotkey_status,
        )
        self._power_monitor = PowerMonitor(on_resume=self._on_system_resume)
        self._running = True
        self._processing_lock = threading.Lock()

    def _on_record_start(self):
        """Called when hotkey is pressed - start recording."""
        log.info("Recording started")
        self._tray.set_state(TrayState.RECORDING)
        self._recorder.start()

    def _on_record_stop(self):
        """Called when hotkey is released - stop and transcribe."""
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self):
        """Process the recorded audio (runs in background thread)."""
        with self._processing_lock:
            log.info("Processing recording")
            self._tray.set_state(TrayState.PROCESSING)

            audio_buffer = self._recorder.stop()

            if audio_buffer.getbuffer().nbytes > 0:
                text = self._transcriber.transcribe(audio_buffer)
                if text:
                    log.info("Transcribed: %s", text)
                    self._injector.inject(text)
                else:
                    log.info("No transcription result")
            else:
                log.info("No audio recorded")

            self._tray.set_state(TrayState.IDLE)

    def _on_system_resume(self):
        """Called when system resumes from sleep."""
        log.info("System resumed from sleep")
        self._tray.set_status_text("Resumed from sleep")

    def _on_restart(self):
        """Called when user clicks Re-register Hotkey in tray menu."""
        log.info("Manual hotkey re-registration requested via tray menu")
        self._hotkey.reinitialize()

    def _on_view_log(self):
        """Called when user clicks View Log in tray menu."""
        try:
            os.startfile(_LOG_FILE)
        except Exception:
            # If the log file doesn't exist yet, open the directory
            try:
                os.startfile(_LOG_DIR)
            except Exception:
                pass

    def _on_hotkey_status(self, status: str):
        """Called when hotkey status changes."""
        self._tray.set_status_text(status)

    def _shutdown(self):
        """Shutdown the application."""
        log.info("Shutting down (PID %d)", os.getpid())
        self._running = False
        self._power_monitor.stop()
        self._hotkey.stop()
        os._exit(0)

    def run(self):
        """Run the application."""
        log.info("TerminalWhisper starting (PID %d)", os.getpid())

        self._tray.start()
        self._hotkey.start()
        self._power_monitor.start()

        log.info("All components started")

        try:
            self._hotkey.join()
        except KeyboardInterrupt:
            self._shutdown()


def _acquire_single_instance():
    """Ensure only one instance of TerminalWhisper is running."""
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "TerminalWhisper_SingleInstance")
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:
        log.error("Another instance is already running")
        sys.exit(0)
    log.info("Mutex acquired")
    return mutex


def main():
    """Entry point."""
    _setup_logging()
    log.info("======= PROCESS START (PID %d) =======", os.getpid())
    log.info("Log file: %s", _LOG_FILE)

    mutex = _acquire_single_instance()
    try:
        app = VoiceInputApp()
        app.run()
    except Exception as e:
        log.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
