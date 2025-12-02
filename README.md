# 🔮 InkSage [Experimental Version]

**The Local Context Engine.**

InkSage is a privacy-first, neural interface that sits on top of your operating system. Unlike standard writing assistants that just autocomplete text, InkSage is **context-aware**—it automatically changes its personality based on whether you are coding in VS Code, writing a novel in Obsidian, or sending a professional email.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green?logo=qt&logoColor=white)
![PyTorch](https://img.shields.io/badge/AI-PyTorch-orange?logo=pytorch&logoColor=white)

---

## ✨ Key Features

### 🦎 **The Chameleon Engine**
InkSage watches your active window title to understand your context. It switches its "System Persona" automatically:
* **Coding Mode:** (VS Code, PyCharm) → Concise, technical, code-heavy responses.
* **Professional Mode:** (Outlook, Slack) → Formal grammar, polite tone, clear structure.
* **Creative Mode:** (Obsidian, Notion) → Descriptive, fluid, and vocabulary-rich.

### 🧠 **100% Local Intelligence**
* Powered by **PyTorch** and **Hugging Face Transformers**.
* Default Model: `Qwen/Qwen2.5-1.5B-Instruct` (Fast, lightweight, smart).
* **Zero Data Leaks:** Your keystrokes and text never leave your machine. No APIs. No Cloud.

### 🛡️ **Privacy Guard**
* Built-in **PII Scrubber**: Automatically detects and redacts emails, phone numbers, IP addresses, and credit card numbers *before* they even reach the local AI engine.

### ⚡ **Modern "Command Bar" UI**
* **Solid Visibility:** High-contrast, dark-mode interface designed for maximum readability.
* **Non-Intrusive:** Runs quietly in the System Tray until summoned.
* **Smart Overlay:** Suggestion widgets appear near your cursor, clamping to screen edges so they never go off-screen.

---

## 🚀 Installation

### Prerequisites
* **OS:** Windows 10/11 (Recommended), macOS, or Linux.
* **Python:** Version **3.10** or higher.
* **RAM:** Minimum 8GB (16GB recommended for smooth performance).

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/inksage.git](https://github.com/yourusername/inksage.git)
cd inksage
````

### 2\. Create a Virtual Environment (Critical)

To avoid conflicts with system libraries (especially if you use Anaconda), **always** create a fresh virtual environment.

**Windows (PowerShell):**

```powershell
# 1. If you use Anaconda, deactivate it first to prevent DLL conflicts
conda deactivate

# 2. Create the environment
python -m venv venv

# 3. Activate it
.\venv\Scripts\activate
```

**Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3\. Install Dependencies

InkSage uses PySide6 for the GUI and PyTorch for the brain.

```bash
pip install -r requirements.txt
```

*(Note: This will download PyTorch (\~2.5GB). This step may take a few minutes.)*

-----

## 🏃 Usage

### First Launch

Run the application launcher:

```bash
python run_inksage.py
```

**Note:** On the very first run, InkSage will automatically download the AI model (`Qwen 2.5 1.5B`) from Hugging Face. This is a one-time process.

### Global Hotkeys

| Keystroke | Action |
| :--- | :--- |
| **`Ctrl + Shift + Q`** | **Toggle Command Bar.** Opens the main dashboard. |
| **`Ctrl + Shift + C`** | **Quick Complete.** Reads your current sentence and suggests an ending via popup. |
| **`Ctrl + Shift + R`** | **Rephrase.** Opens the rephrase tool with your clipboard content pre-filled. |

### Core Workflows

1.  **Auto-Write:** Open the dashboard (`Ctrl+Shift+Q`) → Click "Auto Write" → Describe what you want (e.g., *"Write a polite decline to a wedding invitation"*).
2.  **Rephrase:** Copy text → Open dashboard → Click "Rephrase".
3.  **Quick Suggestion:** Type the start of a sentence in Notepad (e.g., *"The future of AI is"*) → Press `Ctrl+Shift+C` → Click the popup to auto-paste the result.

-----

## ⚙️ Configuration

You can customize InkSage by editing `config/settings.yaml`.

### Changing the AI Model

If you have more RAM, you can switch to a larger model easily by changing the Repo ID:

```yaml
engine:
  model_path: "Qwen/Qwen2.5-7B-Instruct"  # Larger, smarter model
```

### Customizing Context Awareness

Add your own apps to specific roles:

```yaml
context_awareness:
  roles:
    code:
      apps: ["code", "pycharm", "cursor", "godot", "unity"] # Added Godot/Unity
      system_prompt: "You are a game developer..."
```

-----

## 🏗️ Architecture

InkSage follows a modular, event-driven architecture:

```text
inksage/
├── config/
│   └── settings.yaml          # Central configuration (Model, UI, Hotkeys)
├── logs/
│   └── inksage.log            # Runtime logs for debugging
├── models/
│   └── .keep                  # Placeholder for downloaded AI models
├── src/
│   ├── core/                  # --- The Brains ---
│   │   ├── __init__.py
│   │   ├── assistant.py       # Central Coordinator (Signals & State)
│   │   ├── audio_manager.py   # Voice Recording & Transcription (Whisper)
│   │   ├── context_sniffer.py # Active Window Detector (The Chameleon)
│   │   ├── engine.py          # PyTorch/Transformers Wrapper (The AI)
│   │   ├── keyboard_monitor.py# Global Hotkeys & Input Hook
│   │   ├── pii_scrubber.py    # Privacy Guard (Redacts sensitive data)
│   │   └── text_buffer.py     # Thread-safe input memory
│   ├── ui/                    # --- The Looks ---
│   │   ├── __init__.py
│   │   ├── auto_write_dialog.py # Long-form generation window
│   │   ├── main_window.py     # The Command Bar (Dashboard)
│   │   ├── rephrase_widget.py # Text rewriting tool
│   │   ├── styles.py          # Visual Theme Manager (Solid Mode)
│   │   ├── suggestion_widget.py # Quick-complete popup
│   │   └── tray_icon.py       # System Tray integration
│   ├── utils/                 # --- The Helpers ---
│   │   ├── __init__.py
│   │   ├── clipboard.py       # Cross-platform Copy/Paste logic
│   │   └── config.py          # Config Loader Singleton
│   ├── workers/               # --- The Muscle ---
│   │   ├── __init__.py
│   │   └── generation_worker.py # Background Threading (Prevents UI Freeze)
│   ├── __init__.py
│   └── main.py                # Application Entry Point
├── .gitignore                 # Git exclusion rules
├── CHANGELOG.md               # Version history
├── LICENSE                    # Apache 2.0 License
├── README.md                  # Documentation
├── requirements.txt           # Python dependencies
├── run_inksage.py             # User Launcher script
├── setup.py                   # Packaging script
└── test_installation.py       # Environment Diagnostic tool
```

-----

## 🚑 Troubleshooting

**1. "DLL load failed while importing QtWidgets"**
This is a known conflict between System Python and Anaconda.

  * **Fix:** Close your terminal. Open a fresh one. Do **not** run `conda activate`. Only run `.\venv\Scripts\activate`. Then run the app.

**2. The window is invisible or transparent?**

  * **Fix:** InkSage runs in "Solid Mode" by default now. Ensure `src/ui/styles.py` has not been modified to use RGBA alpha channels.

**3. AI generation is slow?**

  * **Reason:** You are likely running on CPU.
  * **Fix:** If you have an NVIDIA GPU, uninstall torch and reinstall the CUDA version from [pytorch.org](https://pytorch.org/).

-----

## 🤝 Contributing

Contributions are welcome\! Please check `src/core/assistant.py` to understand how request routing works before adding new generation modes.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

-----

**Made with ❤️ by Arnav Chauhan, UG at Indian Institute of Technology, Kharagpur**

```
```
