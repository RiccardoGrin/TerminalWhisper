"""Text injection module using clipboard and keyboard simulation."""

import time
import pyperclip
from pynput.keyboard import Controller, Key
from config import PASTE_DELAY


class TextInjector:
    """Injects text into the active window via clipboard + paste."""

    def __init__(self):
        self._keyboard = Controller()

    def inject(self, text: str):
        """
        Inject text into the active window.

        Copies text to clipboard and simulates Ctrl+V to paste.

        Args:
            text: The text to inject
        """
        if not text:
            return

        # Copy to clipboard
        pyperclip.copy(text)

        # Small delay for clipboard to be ready
        time.sleep(PASTE_DELAY)

        # Simulate Ctrl+V
        self._keyboard.press(Key.ctrl)
        self._keyboard.press("v")
        self._keyboard.release("v")
        self._keyboard.release(Key.ctrl)
