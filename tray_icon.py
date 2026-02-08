"""System tray icon for visual feedback."""

from enum import Enum
from typing import Optional, Callable
import threading

from PIL import Image, ImageDraw
import pystray


class TrayState(Enum):
    """Tray icon states."""
    IDLE = "idle"          # Green - ready
    RECORDING = "recording"  # Red - recording audio
    PROCESSING = "processing"  # Yellow - transcribing


class TrayIcon:
    """System tray icon with state-based colors."""

    COLORS = {
        TrayState.IDLE: "#22c55e",      # Green
        TrayState.RECORDING: "#ef4444",  # Red
        TrayState.PROCESSING: "#eab308",  # Yellow
    }

    def __init__(
        self,
        on_exit: Optional[Callable[[], None]] = None,
        on_restart: Optional[Callable[[], None]] = None,
        on_view_log: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize tray icon.

        Args:
            on_exit: Callback when user clicks Exit in menu
            on_restart: Callback when user clicks Restart in menu
            on_view_log: Callback when user clicks View Log in menu
        """
        self._on_exit = on_exit
        self._on_restart = on_restart
        self._on_view_log = on_view_log
        self._icon: Optional[pystray.Icon] = None
        self._state = TrayState.IDLE
        self._thread: Optional[threading.Thread] = None
        self._status_text = "Running"

    def _create_icon_image(self, color: str) -> Image.Image:
        """Create a circular icon with the specified color."""
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw filled circle
        margin = 4
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=color,
        )

        return image

    def _create_menu(self):
        """Create the tray icon menu."""
        return pystray.Menu(
            pystray.MenuItem("TerminalWhisper", None, enabled=False),
            pystray.MenuItem("Hold Ctrl+` to transcribe into any text input", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: f"Status: {self._status_text}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Re-register Hotkey", self._handle_restart),
            pystray.MenuItem("View Log", self._handle_view_log),
            pystray.MenuItem("Exit", self._handle_exit),
        )

    def _handle_restart(self):
        """Handle restart menu click."""
        if self._on_restart:
            self._on_restart()

    def _handle_view_log(self):
        """Handle view log menu click."""
        if self._on_view_log:
            self._on_view_log()

    def _handle_exit(self):
        """Handle exit menu click."""
        if self._on_exit:
            self._on_exit()
        self.stop()

    def set_status_text(self, text: str):
        """Update the status text shown in the tray menu."""
        self._status_text = text
        if self._icon:
            self._icon.update_menu()

    def set_state(self, state: TrayState):
        """
        Update the tray icon state.

        Args:
            state: New state (affects icon color)
        """
        self._state = state
        if self._icon:
            color = self.COLORS.get(state, self.COLORS[TrayState.IDLE])
            self._icon.icon = self._create_icon_image(color)

    def start(self):
        """Start the tray icon in a background thread."""
        color = self.COLORS[self._state]
        self._icon = pystray.Icon(
            name="TerminalWhisper",
            icon=self._create_icon_image(color),
            title="TerminalWhisper - Hold Ctrl+` to record into any text input",
            menu=self._create_menu(),
        )

        # Run in background thread
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            self._icon.stop()
            self._icon = None
