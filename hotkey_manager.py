"""Global hotkey manager using keyboard library with suppression."""

import threading
from typing import Callable, Optional
import keyboard
from config import HOTKEY_MODIFIERS, HOTKEY_KEY


class HotkeyManager:
    """Manages global hotkey detection for push-to-talk with key suppression."""

    def __init__(
        self,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize hotkey manager.

        Args:
            on_press: Callback when hotkey combo is pressed
            on_release: Callback when hotkey combo is released
        """
        self._on_press = on_press
        self._on_release = on_release
        self._hotkey_active = False
        self._running = False
        self._wait_thread: Optional[threading.Thread] = None

        # Build hotkey string (e.g., "ctrl+`")
        modifiers = "+".join(sorted(HOTKEY_MODIFIERS))
        self._hotkey_string = f"{modifiers}+{HOTKEY_KEY}" if modifiers else HOTKEY_KEY

    def _on_hotkey_press(self):
        """Handle hotkey press event."""
        if not self._hotkey_active:
            self._hotkey_active = True
            if self._on_press:
                self._on_press()

    def _on_any_key_release(self, event):
        """Handle any key release to detect when hotkey combo is broken."""
        if not self._hotkey_active:
            return

        # Check if a key in our combo was released
        key_name = event.name.lower() if event.name else ""

        # Normalize modifier names
        modifier_map = {
            "ctrl": "ctrl",
            "left ctrl": "ctrl",
            "right ctrl": "ctrl",
            "shift": "shift",
            "left shift": "shift",
            "right shift": "shift",
            "alt": "alt",
            "left alt": "alt",
            "right alt": "alt",
        }

        normalized = modifier_map.get(key_name, key_name)

        # Check if released key is part of our hotkey
        is_main_key = (key_name == HOTKEY_KEY or key_name == "grave" or
                       normalized == HOTKEY_KEY)
        is_modifier = normalized in HOTKEY_MODIFIERS

        if is_main_key or is_modifier:
            self._hotkey_active = False
            if self._on_release:
                self._on_release()

    def start(self):
        """Start listening for hotkeys."""
        self._running = True

        # Register hotkey with suppression
        keyboard.add_hotkey(
            self._hotkey_string,
            self._on_hotkey_press,
            suppress=True,
            trigger_on_release=False,
        )

        # Hook key releases to detect when combo is broken
        keyboard.on_release(self._on_any_key_release)

        # Start a thread that keeps the manager alive
        self._wait_thread = threading.Thread(target=self._wait_loop, daemon=True)
        self._wait_thread.start()

    def _wait_loop(self):
        """Keep the manager running."""
        while self._running:
            keyboard.wait()

    def stop(self):
        """Stop listening for hotkeys."""
        self._running = False
        keyboard.unhook_all()

    def reinitialize(self):
        """
        Re-register hotkey hooks.

        Call this after system resume from sleep to restore functionality.
        Windows may invalidate low-level hooks during sleep/wake cycles.
        """
        # Clear any stale hook state
        self._hotkey_active = False

        # Remove all existing hooks
        keyboard.unhook_all()

        # Re-register hotkey with suppression
        keyboard.add_hotkey(
            self._hotkey_string,
            self._on_hotkey_press,
            suppress=True,
            trigger_on_release=False,
        )

        # Re-hook key releases
        keyboard.on_release(self._on_any_key_release)

        print("Hotkey hooks reinitialized after system resume")

    def join(self):
        """Wait for manager to finish."""
        if self._wait_thread:
            self._wait_thread.join()
