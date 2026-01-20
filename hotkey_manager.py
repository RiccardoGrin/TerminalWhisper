"""Global hotkey manager using pynput."""

from typing import Callable, Optional
from pynput import keyboard
from config import HOTKEY_MODIFIERS, HOTKEY_KEY


class HotkeyManager:
    """Manages global hotkey detection for push-to-talk."""

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
        self._listener: Optional[keyboard.Listener] = None
        self._pressed_modifiers: set[str] = set()
        self._hotkey_active = False

    def _normalize_key(self, key) -> Optional[str]:
        """Normalize key to string representation."""
        try:
            # First try character
            if hasattr(key, "char") and key.char:
                return key.char.lower()
            # Then try named keys (like ctrl, shift, etc.)
            elif hasattr(key, "name") and key.name:
                return key.name.lower()
            # Fall back to virtual key code for keys that lose char when Ctrl is held
            elif hasattr(key, "vk") and key.vk:
                # Map virtual key codes to key names
                vk_map = {
                    192: "`",  # VK_OEM_3 - backtick/grave on US keyboard
                }
                return vk_map.get(key.vk)
        except AttributeError:
            pass
        return None

    def _is_modifier(self, key_name: str) -> bool:
        """Check if key is a modifier we're tracking."""
        # Map key names to our modifier names
        modifier_map = {
            "ctrl": "ctrl",
            "ctrl_l": "ctrl",
            "ctrl_r": "ctrl",
            "shift": "shift",
            "shift_l": "shift",
            "shift_r": "shift",
            "alt": "alt",
            "alt_l": "alt",
            "alt_r": "alt",
            "alt_gr": "alt",
        }
        return modifier_map.get(key_name, key_name) in HOTKEY_MODIFIERS

    def _get_modifier_name(self, key_name: str) -> str:
        """Get normalized modifier name."""
        modifier_map = {
            "ctrl": "ctrl",
            "ctrl_l": "ctrl",
            "ctrl_r": "ctrl",
            "shift": "shift",
            "shift_l": "shift",
            "shift_r": "shift",
            "alt": "alt",
            "alt_l": "alt",
            "alt_r": "alt",
            "alt_gr": "alt",
        }
        return modifier_map.get(key_name, key_name)

    def _on_key_press(self, key):
        """Handle key press event."""
        key_name = self._normalize_key(key)
        if not key_name:
            return

        # Track modifier presses
        if self._is_modifier(key_name):
            self._pressed_modifiers.add(self._get_modifier_name(key_name))
            return

        # Check if this is our hotkey combo
        if key_name == HOTKEY_KEY and self._pressed_modifiers == HOTKEY_MODIFIERS:
            if not self._hotkey_active:
                self._hotkey_active = True
                if self._on_press:
                    self._on_press()

    def _on_key_release(self, key):
        """Handle key release event."""
        key_name = self._normalize_key(key)
        if not key_name:
            return

        # Track modifier releases
        if self._is_modifier(key_name):
            modifier_name = self._get_modifier_name(key_name)
            self._pressed_modifiers.discard(modifier_name)

        # Check if hotkey was released
        if self._hotkey_active:
            # Release if the main key or any required modifier is released
            if key_name == HOTKEY_KEY or (
                self._is_modifier(key_name)
                and self._get_modifier_name(key_name) in HOTKEY_MODIFIERS
            ):
                self._hotkey_active = False
                if self._on_release:
                    self._on_release()

    def start(self):
        """Start listening for hotkeys."""
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.start()

    def stop(self):
        """Stop listening for hotkeys."""
        if self._listener:
            self._listener.stop()
            self._listener = None

    def join(self):
        """Wait for listener to finish."""
        if self._listener:
            self._listener.join()
