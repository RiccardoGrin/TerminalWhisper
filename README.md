# TerminalWhisper

A Windows voice input tool that lets you dictate text into any application. Hold a hotkey, speak, and your words are transcribed and pasted wherever your cursor is.

## How It Works

```
Hold Ctrl+` → Speak → Release → Text appears at cursor
```

1. **Hold** the hotkey (Ctrl+`) to start recording
2. **Speak** your text
3. **Release** the hotkey to stop recording
4. **Text is transcribed** via OpenAI Whisper API and pasted at your cursor

A system tray icon shows the current state:
- **Green** - Ready/Idle
- **Red** - Recording
- **Yellow** - Processing/Transcribing

## Requirements

- **Windows 10/11**
- **OpenAI API Key** - Get one at [platform.openai.com](https://platform.openai.com/api-keys)
- **Administrator privileges** - Required for global hotkey suppression
- **Microphone** - For voice input

## Installation

### Option 1: Run from Source (Python)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RiccardoGrin/TerminalWhisper.git
   cd TerminalWhisper
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key:**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

5. **Run as Administrator:**
   - Open Command Prompt or PowerShell **as Administrator**
   - Navigate to the project folder and run:
   ```bash
   venv\Scripts\activate
   python voice_input.py
   ```

### Option 2: Run the Executable

1. **Download** `TerminalWhisper.exe` from the [Releases page](https://github.com/RiccardoGrin/TerminalWhisper/releases)

2. **Create a `.env` file** in the same folder as the exe:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. **Run as Administrator:**
   - Right-click `TerminalWhisper.exe`
   - Select "Run as administrator"

## Usage

1. Launch TerminalWhisper (as Administrator)
2. Look for the green circle in your system tray
3. Click into any text field (terminal, browser, notepad, etc.)
4. Hold **Ctrl+`** and speak
5. Release to transcribe and paste

### Tips
- Speak clearly at a normal pace
- The backtick key (`) is usually above Tab, left of 1
- Longer recordings = better context for transcription
- Check the tray icon color to confirm recording state

## Running at Startup

To have TerminalWhisper start automatically when you log in (with admin privileges):

### Option 1: Command Line (Quick)

Run this in an **Administrator PowerShell**:

```powershell
schtasks /create /tn "TerminalWhisper" /tr "C:\path\to\TerminalWhisper.exe" /sc onlogon /rl highest /f
```

Replace `C:\path\to\` with the actual path to your exe.

### Option 2: Task Scheduler GUI

1. Press **Win+R**, type `taskschd.msc`, press Enter

2. Click **"Create Task"** (not "Create Basic Task")

3. **General tab:**
   - Name: `TerminalWhisper`
   - Check "Run with highest privileges"
   - Configure for: Windows 10/11

4. **Triggers tab:**
   - Click "New..."
   - Begin the task: "At log on"
   - Specific user: Your username
   - Click OK

5. **Actions tab:**
   - Click "New..."
   - Action: "Start a program"
   - Program/script: `C:\path\to\TerminalWhisper.exe`
   - (Or for Python: `C:\path\to\venv\Scripts\pythonw.exe`)
   - Add arguments (Python only): `C:\path\to\voice_input.py`
   - Click OK

6. **Conditions tab:**
   - Uncheck "Start only if on AC power" (for laptops)

7. Click **OK** to save

The app will now start automatically at login with admin privileges, no UAC prompt required.

### Disabling Auto-Start

To remove the scheduled task, run in **Administrator PowerShell**:

```powershell
schtasks /delete /tn "TerminalWhisper" /f
```

Or open Task Scheduler, find "TerminalWhisper" in the list, right-click and delete.

## Stopping the App

- **Right-click** the tray icon (green/red/yellow circle) → **Exit**
- Or use Task Manager to end the process

## Configuration

Edit `config.py` to customize:

```python
# Hotkey (default: Ctrl+`)
HOTKEY_MODIFIERS = {"ctrl"}
HOTKEY_KEY = "`"

# Audio settings
SAMPLE_RATE = 16000  # 16kHz for Whisper
CHANNELS = 1         # Mono

# Paste delay (increase if paste is unreliable)
PASTE_DELAY = 0.05   # 50ms
```

## Why Administrator Privileges?

TerminalWhisper requires admin rights to:

1. **Suppress the hotkey** - Prevents Ctrl+` from triggering other app shortcuts (like opening VS Code's terminal)
2. **Global keyboard hooks** - The `keyboard` library needs elevated permissions on Windows to capture keys system-wide

Without admin rights, the hotkey will still work but won't be suppressed, meaning other apps may also respond to Ctrl+`.

## Troubleshooting

### "OPENAI_API_KEY not found"
- Make sure `.env` file exists in the same folder as the script/exe
- Check the API key is correct and has no extra spaces

### Hotkey not working
- Confirm you're running as Administrator
- Check the tray icon is visible (green circle)
- Try pressing the keys slowly: Ctrl first, then backtick

### Text not pasting
- Some applications block simulated keyboard input
- Try increasing `PASTE_DELAY` in config.py
- Ensure the target application is focused

### No audio recorded
- Check your microphone is working in Windows settings
- Make sure no other app is exclusively using the microphone

### Tray icon not visible
- Click the "^" arrow in the system tray to see hidden icons
- Drag the icon to the visible area if desired

## Building the Executable

To create your own `.exe`:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name TerminalWhisper voice_input.py
```

The executable will be in the `dist` folder. Users will need to create their own `.env` file with their API key in the same folder as the exe.

## Privacy & Security

- Audio is sent to OpenAI's Whisper API for transcription
- No audio is stored locally after transcription
- Your API key is stored locally in `.env` (never commit this file)
- The tool only activates when you hold the hotkey

## License

MIT License - See LICENSE file for details.
