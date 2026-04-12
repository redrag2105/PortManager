# PortManager TUI 🛡️

A highly refined, modern Textual App for Port and Process Management. "Network Guardian" provides an intuitive Terminal User Interface (TUI) to easily view, track, and kill processes running on specific target ports.

## ✨ Features

- **Process Management**: View active processes on monitored ports. Seamlessly kill selected processes (`k`) or terminate all tracked processes at once (`Ctrl+K`).
- **Dynamic Port Tracking**: Add (`+`), Edit (`~`), and Untrack (`-`) ports directly within the app without manually editing config files.
- **Port Forwarding**: Built-in support for toggling Port Forwarding / Dev Tunnels (`f`).
- **Interactive Settings & Audio**: Custom UI sound effects (Splash, Scroll, Click, Close, Error, Success) powered by Pygame. Features an in-app Settings modal (`s`) for fine-tuning individual volume levels, updating text-box values, or muting entirely.
- **Modern Theming**: Fully responsive, flex-box based Textual UI with support for both Dark Mode and Light Mode (`n`).
- **Standalone Execution**: Packaged with a convenient `.bat` launcher and includes a PyInstaller `.spec` to build a portable Windows `.exe`.

## ⌨️ Keybindings

| Key | Action |
| :---: | --- |
| `+` / `=` | Add/Track a new port |
| `-` | Untrack selected port |
| `~` / `` ` `` | Edit selected port |
| `k` | Kill selected process |
| `Ctrl+K`| Kill all tracked processes |
| `f` | Toggle Port Forwarding |
| `r` | Refresh data |
| `n` | Toggle Dark/Light Theme |
| `s` | Open Settings (Audio Controls) |
| `q` | Quit application |

## 🛠️ Prerequisites

- Python 3.10+
- A Virtual Environment (recommended)

## 🚀 Setup and Installation

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

## 🎮 Running the Application

You can start the application directly via Python (make sure your virtual environment is active):

```bash
python main.py
```

Alternatively, on Windows, you can simply double-click the `PortManager.bat` file, which will automatically activate the `venv` if it exists and launch the app in a preconfigured window size.

## ⚙️ Managing the Ports Manually

The application reads from a configuration file named `ports.txt` to know which ports to initially monitor.
- If `ports.txt` doesn't exist, it will be automatically created with default ports.
- You can add or remove ports manually by opening `ports.txt` in any text editor.
- Each port should be on a new line (e.g., `3000`). Comments using `#` are also supported.

## 📦 Building the Executable (.exe)

To package the application into a standalone `.exe` so that users don't need Python installed, use **PyInstaller**. 

**Important:** You must run PyInstaller *from within the virtual environment* where the dependencies are installed.

1. **Activate your virtual environment**.
2. **Build the `.exe` using the spec file**:
   ```bash
   pyinstaller PortManager.spec
   ```

The finalized `PortManager.exe` will appear in the `dist` folder.# PortManager TUI 🛡️

A highly refined, modern Textual App for Port and Process Management. "Network Guardian" provides an intuitive Terminal User Interface (TUI) to easily view, track, and kill processes running on specific target ports.

## ✨ Features

- **Process Management**: View active processes on monitored ports. Seamlessly kill selected processes (k) or terminate all tracked processes at once (Ctrl+K).
- **Dynamic Port Tracking**: Add (+), Edit (~), and Untrack (-) ports directly within the app without manually editing config files.
- **Port Forwarding**: Built-in support for toggling Port Forwarding / Dev Tunnels ().
- **Interactive Settings & Audio**: Custom UI sound effects (Splash, Scroll, Click, Close, Error, Success) powered by Pygame. Features an in-app Settings modal (s) for fine-tuning individual volume levels, updating text-box values, or muting entirely.
- **Modern Theming**: Fully responsive, flex-box based Textual UI with support for both Dark Mode and Light Mode (
).
- **Standalone Execution**: Packaged with a convenient .bat launcher and includes a PyInstaller .spec to build a portable Windows .exe.

## ⌨️ Keybindings

| Key | Action |
| :---: | --- |
| + / = | Add/Track a new port |
| - | Untrack selected port |
| ~ / `  ` | Edit selected port |
| k | Kill selected process |
| Ctrl+K| Kill all tracked processes |
|  | Toggle Port Forwarding |
| 
 | Refresh data |
| 
 | Toggle Dark/Light Theme |
| s | Open Settings (Audio Controls) |
| q | Quit application |

## 🛠️ Prerequisites

- Python 3.10+
- A Virtual Environment (recommended)

## 🚀 Setup and Installation

1. **Clone the repository** (or download the files).
2. **Create a virtual environment**:
   `ash
   python -m venv venv
   `
3. **Activate the virtual environment**:
   - On Windows: .\venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate
4. **Install the requirements**:
   `ash
   pip install -r requirements.txt
   `

## 🎮 Running the Application

You can start the application directly via Python (make sure your virtual environment is active):

`ash
python main.py
`

Alternatively, on Windows, you can simply double-click the PortManager.bat file, which will automatically activate the env if it exists and launch the app in a preconfigured window size.

## ⚙️ Managing the Ports Manually

The application reads from a configuration file named ports.txt to know which ports to initially monitor.
- If ports.txt doesn't exist, it will be automatically created with default ports.
- You can add or remove ports manually by opening ports.txt in any text editor.
- Each port should be on a new line (e.g., 3000). Comments using # are also supported.

## 📦 Building the Executable (.exe)

To package the application into a standalone .exe so that users don't need Python installed, use **PyInstaller**. 

**Important:** You must run PyInstaller *from within the virtual environment* where the dependencies are installed.

1. **Activate your virtual environment**.
2. **Build the .exe using the spec file**:
   `ash
   pyinstaller PortManager.spec
   `

The finalized PortManager.exe will appear in the dist folder.
