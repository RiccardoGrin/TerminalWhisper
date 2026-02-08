"""Monitor Windows power events (sleep/wake) to detect system resume."""

import ctypes
import ctypes.wintypes
import threading
from typing import Callable, Optional

# Windows constants
WM_POWERBROADCAST = 0x0218
PBT_APMRESUMEAUTOMATIC = 0x0012
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMSUSPEND = 0x0004

# Window class style
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001

# Window messages
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010

# Load Windows DLLs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Set proper argument/return types for DefWindowProcW to handle 64-bit values
user32.DefWindowProcW.argtypes = [
    ctypes.wintypes.HWND,
    ctypes.c_uint,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
]
user32.DefWindowProcW.restype = ctypes.c_longlong

# Define WNDPROC type — use c_longlong for return to match LRESULT on 64-bit
WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    ctypes.wintypes.HWND,
    ctypes.c_uint,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


class WNDCLASSEX(ctypes.Structure):
    """Windows WNDCLASSEX structure."""
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.wintypes.HINSTANCE),
        ("hIcon", ctypes.wintypes.HICON),
        ("hCursor", ctypes.wintypes.HICON),
        ("hbrBackground", ctypes.wintypes.HBRUSH),
        ("lpszMenuName", ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
        ("hIconSm", ctypes.wintypes.HICON),
    ]


class MSG(ctypes.Structure):
    """Windows MSG structure."""
    _fields_ = [
        ("hWnd", ctypes.wintypes.HWND),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.wintypes.WPARAM),
        ("lParam", ctypes.wintypes.LPARAM),
        ("time", ctypes.wintypes.DWORD),
        ("pt", ctypes.wintypes.POINT),
    ]


class PowerMonitor:
    """
    Monitors Windows power state changes and triggers callbacks on resume.

    Uses a hidden window to receive WM_POWERBROADCAST messages from Windows.
    When the system resumes from sleep/hibernate, the on_resume callback is called.
    """

    def __init__(self, on_resume: Optional[Callable[[], None]] = None):
        """
        Initialize the power monitor.

        Args:
            on_resume: Callback function to invoke when system resumes from sleep.
        """
        self._on_resume = on_resume
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._hwnd: Optional[ctypes.wintypes.HWND] = None
        self._wndproc: Optional[WNDPROC] = None  # Must keep reference to prevent GC
        self._class_atom: Optional[int] = None

    def _window_proc(
        self,
        hwnd: ctypes.wintypes.HWND,
        msg: int,
        wparam: ctypes.wintypes.WPARAM,
        lparam: ctypes.wintypes.LPARAM,
    ) -> int:
        """Window procedure to handle Windows messages."""
        if msg == WM_POWERBROADCAST:
            if wparam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                # System has resumed from sleep
                if self._on_resume:
                    try:
                        self._on_resume()
                    except Exception as e:
                        print(f"Error in power resume callback: {e}")
            return 1  # TRUE - message handled

        elif msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)
            return 0

        elif msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _create_window(self) -> bool:
        """Create hidden window to receive power messages."""
        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "TerminalWhisperPowerMonitor"

        # Keep reference to prevent garbage collection
        self._wndproc = WNDPROC(self._window_proc)

        # Register window class
        wc = WNDCLASSEX()
        wc.cbSize = ctypes.sizeof(WNDCLASSEX)
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = self._wndproc
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinstance
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = class_name
        wc.hIconSm = None

        self._class_atom = user32.RegisterClassExW(ctypes.byref(wc))
        if not self._class_atom:
            error = kernel32.GetLastError()
            # Class already registered is OK (error 1410)
            if error != 1410:
                print(f"Failed to register window class: {error}")
                return False
            # Use existing class
            self._class_atom = None

        # Create hidden message-only window
        # HWND_MESSAGE (-3) makes it a message-only window (no visible UI)
        HWND_MESSAGE = ctypes.wintypes.HWND(-3)
        self._hwnd = user32.CreateWindowExW(
            0,  # dwExStyle
            class_name,  # lpClassName
            "TerminalWhisper Power Monitor",  # lpWindowName
            0,  # dwStyle (no visible style)
            0, 0, 0, 0,  # x, y, width, height
            HWND_MESSAGE,  # hWndParent - message-only window
            None,  # hMenu
            hinstance,  # hInstance
            None,  # lpParam
        )

        if not self._hwnd:
            print(f"Failed to create window: {kernel32.GetLastError()}")
            return False

        return True

    def _message_loop(self):
        """Run the Windows message loop."""
        if not self._create_window():
            return

        msg = MSG()
        while self._running:
            # Use GetMessage with timeout via MsgWaitForMultipleObjects pattern
            # PeekMessage with PM_REMOVE to check for messages without blocking forever
            result = user32.PeekMessageW(
                ctypes.byref(msg),
                None,  # All windows
                0,  # Filter min
                0,  # Filter max
                1,  # PM_REMOVE
            )

            if result:
                if msg.message == 0x0012:  # WM_QUIT
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                # No message, sleep briefly to prevent busy-waiting
                # MsgWaitForMultipleObjects would be better but this is simpler
                import time
                time.sleep(0.1)

        # Cleanup
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)
            self._hwnd = None

    def start(self):
        """Start monitoring power events in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring power events."""
        self._running = False

        # Post quit message to break the message loop
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self._thread = None
