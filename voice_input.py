#!/usr/bin/env python3
"""
TerminalWhisper - Voice input tool for terminal.

Hold Ctrl+Shift+Space to record, release to transcribe and paste.
"""

import sys
import threading
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from text_injector import TextInjector
from hotkey_manager import HotkeyManager
from tray_icon import TrayIcon, TrayState


class VoiceInputApp:
    """Main application coordinating all components."""

    def __init__(self):
        self._recorder = AudioRecorder()
        self._transcriber = Transcriber()
        self._injector = TextInjector()
        self._tray = TrayIcon(on_exit=self._shutdown)
        self._hotkey = HotkeyManager(
            on_press=self._on_record_start,
            on_release=self._on_record_stop,
        )
        self._running = True
        self._processing_lock = threading.Lock()

    def _on_record_start(self):
        """Called when hotkey is pressed - start recording."""
        print("Recording...")
        self._tray.set_state(TrayState.RECORDING)
        self._recorder.start()

    def _on_record_stop(self):
        """Called when hotkey is released - stop and transcribe."""
        # Run transcription in background thread to not block hotkey listener
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self):
        """Process the recorded audio (runs in background thread)."""
        with self._processing_lock:
            print("Processing...")
            self._tray.set_state(TrayState.PROCESSING)

            # Stop recording and get audio buffer
            audio_buffer = self._recorder.stop()

            if audio_buffer.getbuffer().nbytes > 0:
                # Transcribe
                text = self._transcriber.transcribe(audio_buffer)

                if text:
                    print(f"Transcribed: {text}")
                    # Inject into terminal
                    self._injector.inject(text)
                else:
                    print("No transcription result")
            else:
                print("No audio recorded")

            self._tray.set_state(TrayState.IDLE)
            print("Ready")

    def _shutdown(self):
        """Shutdown the application."""
        self._running = False
        self._hotkey.stop()

    def run(self):
        """Run the application."""
        print("TerminalWhisper started")
        print("Hold Ctrl+Shift+Space to record, release to transcribe")
        print("Right-click tray icon to exit")
        print()

        # Start components
        self._tray.start()
        self._hotkey.start()

        # Keep running until shutdown
        try:
            self._hotkey.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            self._shutdown()


def main():
    """Entry point."""
    try:
        app = VoiceInputApp()
        app.run()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
