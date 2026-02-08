"""Configuration settings for TerminalWhisper."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Audio settings
SAMPLE_RATE = 16000  # 16kHz for Whisper
CHANNELS = 1  # Mono
DTYPE = "int16"  # 16-bit audio

# Hotkey settings (Ctrl+`)
HOTKEY_MODIFIERS = {"ctrl"}
HOTKEY_KEY = "`"

# Win32 hotkey constants
HOTKEY_VK = 0xC0       # VK_OEM_3 = backtick/tilde key
HOTKEY_MOD = 0x0002    # MOD_CONTROL

# Text injection settings
PASTE_DELAY = 0.05  # 50ms delay between clipboard copy and paste

# Whisper model
WHISPER_MODEL = "whisper-1"
