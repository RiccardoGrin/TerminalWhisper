"""Global hotkey manager using Win32 RegisterHotKey API."""

import ctypes
import ctypes.wintypes as wt
import logging
import threading
import time
from typing import Callable, Optional

from config import HOTKEY_VK, HOTKEY_MOD

log = logging.getLogger(__name__)

user32 = ctypes.windll.user32

# Win32 constants
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000
_HOTKEY_ID = 1

# For release detection polling
VK_CONTROL = 0x11
_POLL_INTERVAL = 0.020  # 20ms


class HotkeyManager:
    """Manages global hotkey detection for push-to-talk using RegisterHotKey."""

    def __init__(
        self,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        self._on_press = on_press
        self._on_release = on_release
        self._on_status_change = on_status_change
        self._hotkey_active = False
        self._running = False
        self._stop_event = threading.Event()
        self._msg_thread: Optional[threading.Thread] = None
        self._registered = False

    def start(self):
        """Start listening for hotkeys."""
        self._running = True
        self._stop_event.clear()

        self._msg_thread = threading.Thread(target=self._message_loop, daemon=True)
        self._msg_thread.start()

    def _register(self) -> bool:
        """Register the hotkey. Must be called from the message loop thread."""
        modifiers = HOTKEY_MOD | MOD_NOREPEAT
        result = user32.RegisterHotKey(None, _HOTKEY_ID, modifiers, HOTKEY_VK)
        if result:
            self._registered = True
            log.info("RegisterHotKey succeeded (vk=0x%02X, mod=0x%04X)", HOTKEY_VK, modifiers)
        else:
            error = ctypes.windll.kernel32.GetLastError()
            log.error("RegisterHotKey FAILED (error=%d)", error)
            self._report_status("Hotkey registration failed")
        return bool(result)

    def _unregister(self):
        """Unregister the hotkey. Must be called from the message loop thread."""
        if self._registered:
            user32.UnregisterHotKey(None, _HOTKEY_ID)
            self._registered = False
            log.info("UnregisterHotKey done")

    def _message_loop(self):
        """GetMessage loop that receives WM_HOTKEY messages."""
        if not self._register():
            return

        msg = wt.MSG()
        while self._running:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result == -1 or result == 0:
                break
            if msg.message == WM_HOTKEY and msg.wParam == _HOTKEY_ID:
                self._on_hotkey_detected()

        self._unregister()

    def _on_hotkey_detected(self):
        """Handle hotkey press, then poll for release."""
        if self._hotkey_active:
            return

        self._hotkey_active = True
        log.info("Hotkey PRESSED")
        if self._on_press:
            self._on_press()

        # Poll for Ctrl release in a separate thread to not block GetMessage
        threading.Thread(target=self._poll_release, daemon=True).start()

    def _poll_release(self):
        """Poll GetAsyncKeyState until Ctrl is released."""
        while self._running:
            time.sleep(_POLL_INTERVAL)
            # GetAsyncKeyState returns short; high bit set = key is down
            state = user32.GetAsyncKeyState(VK_CONTROL)
            if not (state & 0x8000):
                break

        if self._hotkey_active:
            self._hotkey_active = False
            log.info("Hotkey RELEASED")
            if self._on_release:
                self._on_release()

    def stop(self):
        """Stop listening for hotkeys."""
        self._running = False
        # Post WM_QUIT to break GetMessage loop
        thread_id = self._msg_thread.ident if self._msg_thread else 0
        if thread_id:
            user32.PostThreadMessageW(thread_id, 0x0012, 0, 0)  # WM_QUIT
        self._stop_event.set()

    def reinitialize(self):
        """Re-register the hotkey (unregister then register)."""
        self._hotkey_active = False
        # Post a custom message to re-register on the message loop thread
        # Since Register/UnregisterHotKey must be called from the same thread,
        # we stop and restart the message loop
        self.stop()
        if self._msg_thread:
            self._msg_thread.join(timeout=2.0)
        self._running = True
        self._stop_event.clear()
        self._msg_thread = threading.Thread(target=self._message_loop, daemon=True)
        self._msg_thread.start()
        log.info("Hotkey reinitialized")
        self._report_status("Hotkey re-registered")

    def _report_status(self, status: str):
        """Report a status change to the callback if set."""
        if self._on_status_change:
            try:
                self._on_status_change(status)
            except Exception:
                pass

    def join(self):
        """Wait for manager to finish."""
        self._stop_event.wait()
