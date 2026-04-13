from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual import work
from textual.worker import get_current_worker
import random
import string
import time
from audio import audio

ASCII_LOGO = r"""
██████╗  ██████╗ ██████╗ ████████╗
██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝
██████╔╝██║   ██║██████╔╝   ██║   
██╔═══╝ ██║   ██║██╔══██╗   ██║   
██║     ╚██████╔╝██║  ██║   ██║   
╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
             MANAGER               
"""

class StartupSplashScreen(ModalScreen):
    """The startup loading glitch animation modal."""
    
    CSS = """
    StartupSplashScreen {
        align: center middle;
    }
    #splash_main {
        width: 100%;
        height: 100%;
        border: round #cba6f7;
        background: #0f0f14;
        padding: 1 2;
    }
    #splash_header {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: #89b4fa;
        margin-bottom: 2;
        border-bottom: hkey #45475a;
        padding-bottom: 1;
    }
    #splash_content {
        height: 1fr;
    }
    #splash_left {
        width: 55%;
        align: center middle;
        content-align: center middle;
    }
    #splash_right {
        width: 45%;
        border-left: vkey #45475a;
        padding-left: 2;
        height: 100%;
    }
    #splash_logo {
        text-style: bold;
        color: #cba6f7;
        width: 100%;
        content-align: center middle;
    }
    #splash_logs {
        color: #a6e3a1;
        height: 100%;
        overflow: hidden;
    }
    #splash_footer {
        height: 5;
        border-top: hkey #45475a;
        padding-top: 1;
    }
    #splash_status {
        color: #f9e2af;
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #splash_progress {
        color: #94e2d5;
        width: 100%;
        content-align: center middle;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Skip", show=False),
        Binding("space", "dismiss_modal", "Skip", show=False),
        Binding("enter", "dismiss_modal", "Skip", show=False)
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="splash_main"):
            yield Label(" ▰▰▰  PORT MANAGER // NET-OS V2.4 ▰▰▰ ", id="splash_header", markup=False)
            
            with Horizontal(id="splash_content"):
                with Vertical(id="splash_left"):
                    yield Label("", id="splash_logo")
                with Vertical(id="splash_right"):
                    yield Label("", id="splash_logs")
            
            with Vertical(id="splash_footer"):
                yield Label("AWAITING INITIALIZATION...", id="splash_status")
                yield Label("░" * 50, id="splash_progress", markup=False)

    def on_mount(self) -> None:
        self.run_animation()

    def action_dismiss_modal(self) -> None:
        self.dismiss(True)

    @work(thread=True)
    def run_animation(self) -> None:
        worker = get_current_worker()
        
        def safe_update(node_id, text):
            if worker.is_cancelled or not self.is_mounted:
                return
            def _do_update():
                try:
                    self.query_one(node_id, Label).update(text)
                except Exception:
                    pass
            self.app.call_from_thread(_do_update)

        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        glitch_lines = ASCII_LOGO.strip("\n").split("\n")
        
        log_messages = [
            "Mounting kernel...",
            "Loading UI modules...",
            "Checking port bindings...",
            "Bypassing proxy security...",
            "Decrypting config...",
            "Validating checksums...",
            "Establishing secure uplink...",
            "Compiling terminal layout...",
            "Warming up local cache...",
            "Connecting to daemon...",
            "Ready."
        ]
        current_logs = []

        def add_log(msg):
            current_logs.append(f"> {msg}")
            if len(current_logs) > 10:
                current_logs.pop(0)
            safe_update("#splash_logs", "\n".join(current_logs))

        total_steps = 100 
        
        audio.play("splash", loop=True)
        
        for step in range(total_steps):
            if worker.is_cancelled or not self.is_mounted: 
                audio.stop()
                return
            
            # 1. The Cryptographic Decode Wave 
            if step < 85:
                glitch_text = ""
                wave_progress = step / 83.0 
                
                for r, line in enumerate(glitch_lines):
                    glitch_line = ""
                    for c, char in enumerate(line):
                        if char == " ":
                            glitch_line += " "
                            continue
                        
                        char_pos = (c / len(line)) * 0.8 + (r / len(glitch_lines)) * 0.2
                        if wave_progress + random.uniform(-0.15, 0.15) > char_pos:
                            glitch_line += char 
                        else:
                            glitch_line += random.choice(chars)
                    
                    glitch_text += glitch_line + "\n"
                safe_update("#splash_logo", glitch_text.strip("\n"))
                
            elif step == 85:
                safe_update("#splash_logo", ASCII_LOGO.strip("\n"))

            # 2. Logs update unpredictably
            if step % 4 == 0 and len(log_messages) > 0:
                add_log(log_messages.pop(0))
            elif step % 3 == 0:
                add_log(f"[0x{random.randint(1000,9999):04X}] OK")

            # 3. Progress bar update
            progress = int((step / (total_steps - 1)) * 50)
            bar = ("█" * progress) + ("░" * (50 - progress))
            percent = int((step / (total_steps - 1)) * 100)
            safe_update("#splash_progress", f"[{bar}] {percent:>3}%")
            
            # 4. Status update & Color Pop
            if step < 25:
                target = "STARTING CORE SERVICES..."
                chars_to_show = int((step / 24) * len(target))
                safe_update("#splash_status", f"{target[:chars_to_show]}█")
                
            elif step < 55:
                target = "BUILDING UI COMPONENTS..."
                chars_to_show = int(((step - 25) / 29) * len(target))
                safe_update("#splash_status", f"{target[:chars_to_show]}█")
                
            elif step < 95:
                target = "FINALIZING HANDSHAKE..."
                chars_to_show = int(((step - 55) / 29) * len(target))
                safe_update("#splash_status", f"{target[:chars_to_show]}█")
                
            else:
                safe_update("#splash_status", "[bold #a6e3a1]ACCESS GRANTED.[/]")

            time.sleep(0.04)
            if step == 85:
                time.sleep(0.2)

        audio.stop()
        audio.play("success")
        
        time.sleep(0.5)
        if not worker.is_cancelled and self.is_mounted:
            self.app.call_from_thread(self.dismiss, True)