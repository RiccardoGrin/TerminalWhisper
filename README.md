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

5. **Run:**
   ```bash
   venv\Scripts\activate
   python voice_input.py
   ```

### Option 2: Run the Executable

1. **Download** the `TerminalWhisper` folder from the [Releases page](https://github.com/RiccardoGrin/TerminalWhisper/releases) (distributed as a zip)

2. **Create a `.env` file** in the `TerminalWhisper` folder (next to the exe):
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. **Run** `TerminalWhisper.exe` — no admin privileges required

## Usage

1. Launch TerminalWhisper
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

To have TerminalWhisper start automatically when you log in:

### Option 1: PowerShell (Recommended)

Run this in PowerShell, replacing the path with your actual exe location:

```powershell
$exePath = "C:\path\to\TerminalWhisper\TerminalWhisper.exe"
$workingDir = Split-Path $exePath
$action = New-ScheduledTaskAction -Execute $exePath -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "TerminalWhisper" -Action $action -Trigger $trigger -Settings $settings -Force
```

**Important:** The working directory must be set so the app can find your `.env` file.

### Option 2: Task Scheduler GUI

1. Press **Win+R**, type `taskschd.msc`, press Enter

2. Click **"Create Task"** (not "Create Basic Task")

3. **General tab:**
   - Name: `TerminalWhisper`
   - Configure for: Windows 10/11

4. **Triggers tab:**
   - Click "New..."
   - Begin the task: "At log on"
   - Specific user: Your username
   - Click OK

5. **Actions tab:**
   - Click "New..."
   - Action: "Start a program"
   - Program/script: `C:\path\to\TerminalWhisper\TerminalWhisper.exe`
   - **Start in (optional):** `C:\path\to\TerminalWhisper` (the folder containing the exe and .env file - **required!**)
   - Click OK

6. **Conditions tab:**
   - Uncheck "Start only if on AC power" (for laptops)

7. Click **OK** to save

The app will now start automatically at login.

### Disabling Auto-Start

To remove the scheduled task:

```powershell
schtasks /delete /tn "TerminalWhisper" /f
```

Or open Task Scheduler, find "TerminalWhisper" in the list, right-click and delete.

## Tray Icon Menu

Right-click the tray icon (green/red/yellow circle) for these options:

- **Status** - Shows the current state (e.g., "Running", "Resumed from sleep", "Hotkey re-registered")
- **Re-register Hotkey** - Re-registers the system hotkey. Use this if the hotkey stops responding.
- **View Log** - Opens the log file
- **Exit** - Stops the app

You can also end the process via Task Manager.

## Reliability

TerminalWhisper uses the Win32 `RegisterHotKey` API to register Ctrl+` as a system-wide hotkey. This is more reliable than low-level keyboard hooks because:

- **No hook death** - `RegisterHotKey` is managed by the OS and cannot be silently removed
- **No admin required** - Works without elevated privileges
- **Built-in suppression** - The hotkey combo is consumed by the OS and not passed to other apps
- **Sleep/wake safe** - The registration survives system sleep/wake cycles

Additional reliability features:
- **Single-instance guard** - Only one copy of TerminalWhisper can run at a time
- **Sleep/wake detection** - The app detects system resume events and updates the tray status
- **Manual re-register** - Right-click the tray icon and select "Re-register Hotkey" if the hotkey stops working

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

## Building the Executable

To build the app:

```bash
pip install pyinstaller
pyinstaller TerminalWhisper.spec
```

The output is a folder at `dist/TerminalWhisper/` containing `TerminalWhisper.exe` and all dependencies. Distribute this folder as a zip file. Users need to create a `.env` file inside the folder with their API key.

## Troubleshooting

### "OPENAI_API_KEY not found"
- Make sure `.env` file exists in the same folder as the script/exe
- Check the API key is correct and has no extra spaces

### Hotkey not working
- Right-click the tray icon and select "Re-register Hotkey"
- Check the tray icon is visible (green circle)
- Try pressing the keys slowly: Ctrl first, then backtick
- Check the log file for "RegisterHotKey FAILED" errors

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

## Privacy & Security

- Audio is sent to OpenAI's Whisper API for transcription
- No audio is stored locally after transcription
- Your API key is stored locally in `.env` (never commit this file)
- The tool only activates when you hold the hotkey

## License

MIT License - See LICENSE file for details.
