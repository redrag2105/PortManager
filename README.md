# PortManager TUI

A highly refined, modern Textual App for Port Management. This application provides a Terminal User Interface (TUI) to easily view and kill processes running on specific target ports.

## Prerequisites

- Python 3.10+
- A Virtual Environment (recommended)

## Setup and Installation

1. **Clone the repository** (or download the files).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the virtual environment**:
   - On Windows: `.\venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
4. **Install the requirements**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

You can start the application directly via Python (make sure your virtual environment is active):

```bash
python main.py
```

Alternatively, on Windows, you can double-click the `PortManager.bat` file, which will automatically use the `venv` if it exists.

## Managing the Ports

The application reads from a configuration file named `ports.txt` to know which ports to monitor.
- If `ports.txt` doesn't exist, it will be created automatically with default ports.
- You can add or remove ports manually by opening `ports.txt` in any text editor.
- Each port should be on a new line (e.g., `3000`). Comments using `#` are also supported.

## Building the Executable (.exe)

To package the application into a standalone `.exe` so that users don't need Python installed, use **PyInstaller**. 

**Important:** You must run PyInstaller *from within the virtual environment* where the dependencies are installed to prevent `ModuleNotFoundError`.

1. **Activate your virtual environment** (as shown above).
2. **Build the `.exe` using the spec file**:
   ```bash
   pyinstaller PortManager.spec
   ```

The successfully built `PortManager.exe` will appear in the `dist` folder.