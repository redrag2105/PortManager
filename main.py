import sys
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Button, Static, Label
from textual.widgets._header import HeaderTitle
from textual.reactive import reactive
from textual.binding import Binding

from modals import ConfirmKillScreen, AddPortScreen
from utils import get_target_ports, get_running_processes, kill_process, add_target_port

# --- Monkeypatch HeaderTitle to support dynamic subtitle colors ---
def custom_header_render(self) -> Text:
    text = Text(self.text, no_wrap=True, overflow="ellipsis")
    if self.sub_text:
        text.append(" — ")
        # Use different color based on theme
        color = "#48495C" if self.app.dark else "#d0d3d8"
        text.append(self.sub_text, style=f"italic {color}")
    return text

HeaderTitle.render = custom_header_render
# ------------------------------------------------------------------

LOGO = r"""
 ╭─╮┌─╮┬─╮┌┬┐
 ├─╯│ │├┬╯ │ 
 ┴  └─╯┴└─ ┴ 
"""

class PortManagerApp(App):
    """A highly refined, modern Textual App for Port Management."""
    
    CSS_PATH = 'styles.tcss'

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh_data", "Refresh", show=True),
        Binding("k", "kill_selected", "Kill Selected", show=True),
        Binding("K", "kill_all", "Kill ALL", show=True, key_display="Shift+K"),
        Binding("d", "toggle_dark", "Toggle Theme", show=True),
    ]

    target_ports = reactive(set())
    processes_data = reactive([])

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="root_layout"):
            
            # SIDEBAR
            with Vertical(id="sidebar"):
                with Container(id="logo_box"):
                    yield Static(LOGO, id="logo")
                    yield Static("M A N A G E R", id="logo_manager")
                with Container(id="stats_box"):
                    yield Label("Loading stats...", id="stats")
                with Vertical(id="button_group"):
                    yield Button("+ Add Port", id="btn_add_port")
                    yield Button("↻ Refresh", id="btn_refresh")
                    yield Button("✕ Kill Selected", id="btn_kill_selected")
                    yield Button("⚠ Kill All", id="btn_kill_all")
            
            # MAIN CONTENT
            with Container(id="main_content"):
                with Container(id="table_wrapper"):
                    yield DataTable(id="ports_table")
                    
        yield Footer()

    def on_mount(self) -> None:
        import os
        if os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW('PortManager TUI')
            
        self.title = "PORT MANAGER"
        self.sub_title = "Network Guardian"
        
        # Configure Table
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Center align headers
        table.add_columns(
            Text("STATUS", justify="center"),
            Text("PORT", justify="center"),
            Text("PID", justify="center"),
            Text("PROCESS", justify="center"),
        )

        self.action_refresh_data()
        
        # Trigger CSS mount animation and focus the table
        self.set_timer(0.05, lambda: table.add_class("-loaded"))
        self.set_timer(0.1, lambda: self.query_one("#sidebar").add_class("-loaded"))
        table.focus()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
        self.update_table()
        self.update_stats()

    def action_refresh_data(self) -> None:
        self.target_ports = get_target_ports()
        self.processes_data = get_running_processes(self.target_ports)
        self.update_table()
        self.update_stats()
        self.update_kill_button()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.update_kill_button()

    def update_kill_button(self) -> None:
        try:
            table = self.query_one(DataTable)
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key.value is None:
                return
            idx = int(str(row_key.value))
            proc = self.processes_data[idx]
            
            btn_kill = self.query_one("#btn_kill_selected", Button)
            btn_kill.disabled = (proc["status"] == "INACTIVE")
        except Exception:
            try:
                self.query_one("#btn_kill_selected", Button).disabled = True
            except:
                pass
                
        try:
            running_procs = sum(1 for p in self.processes_data if p["status"] == "RUNNING")
            self.query_one("#btn_kill_all", Button).disabled = (running_procs == 0)
        except Exception:
            try:
                self.query_one("#btn_kill_all", Button).disabled = True
            except:
                pass

    def update_stats(self) -> None:
        running = sum(1 for p in self.processes_data if p['status'] == 'RUNNING')
        total = len(self.target_ports)
        
        active_color = "#a6e3a1" if self.app.dark else "#40a02b"
        
        stats_msg = (
            f"Total tracked: [bold]{total}[/]\n"
            f"Active ports : [bold {active_color}]{running}[/]"
        )
        try:
            self.query_one("#stats", Label).update(stats_msg)
        except Exception:
            pass

    def update_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        
        is_dark = self.app.dark
        active_col = "#a6e3a1" if is_dark else "#40a02b"
        inactive_col = "#585b70" if is_dark else "#9ca0b0"
        port_col = "bold #cba6f7" if is_dark else "bold #1e66f5"
        pid_col = "#89b4fa" if is_dark else "#209fb5"
        name_col = "bold" if is_dark else "bold #4c4f69"

        for idx, proc in enumerate(self.processes_data):
            # Clean, DRY rendering for active vs inactive ports
            is_run = proc['status'] == 'RUNNING'
            
            table.add_row(
                Text("●" if is_run else "○", style=active_col if is_run else inactive_col, justify="center"),
                Text(str(proc['port']), style=port_col if is_run else inactive_col, justify="center"),
                Text(str(proc['pid']), style=pid_col if is_run else inactive_col, justify="center"),
                Text(str(proc['name']), style=name_col if is_run else inactive_col, justify="center"),
                key=str(idx)
            )

    def action_kill_selected(self) -> None:
        table = self.query_one(DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key.value is None:
                return
            proc = self.processes_data[int(str(row_key.value))]
            
            if proc["pid"] == "-" or not str(proc["pid"]).isdigit():
                return
                
            msg = f"Terminate Process: {proc['name']}\nRunning on Port: {proc['port']} (PID: {proc['pid']})?"
            self.push_screen(
                ConfirmKillScreen(msg), 
                lambda confirm: self._execute_kill([proc], f"Successfully killed {proc['name']}") if confirm else None
            )
        except Exception:
            pass

    def action_kill_all(self) -> None:
        running_procs = [p for p in self.processes_data if p["pid"] != "-" and str(p["pid"]).isdigit()]
        
        if not running_procs:
            return

        msg = f"Proceed destroying ALL {len(running_procs)} processes?"
        self.push_screen(
            ConfirmKillScreen(msg), 
            lambda confirm: self._execute_kill(running_procs, "Killed {} active process(es)") if confirm else None
        )

    def _execute_kill(self, procs: list[dict], success_msg: str) -> None:
        killed_count = sum(1 for proc in procs if kill_process(int(proc["pid"])))
        self.action_refresh_data()
        
        if len(procs) == 1:
            if killed_count == 1:
                self.notify(success_msg, title="Terminated", severity="information", timeout=3)
            else:
                self.notify(f"Failed to kill {procs[0]['name']}", title="Error", severity="error", timeout=4)
        else:
            self.notify(success_msg.format(killed_count), title="Mass Termination", severity="warning", timeout=4)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_add_port":
            self.push_screen(AddPortScreen(self.target_ports), self._handle_add_port)
        elif event.button.id == "btn_refresh":
            self.action_refresh_data()
        elif event.button.id == "btn_kill_selected":
            self.action_kill_selected()
        elif event.button.id == "btn_kill_all":
            self.action_kill_all()
            
    def _handle_add_port(self, port: int | None) -> None:
        if port is not None:
            if add_target_port(port):
                self.notify(f"Port {port} added!", severity="information")
                self.action_refresh_data()
            else:
                self.notify(f"Could not add port {port}.", severity="error")

if __name__ == "__main__":
    app = PortManagerApp()
    app.run()
