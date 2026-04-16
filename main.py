import sys
import os

if sys.platform == "win32":
    # Activate ANSI escape sequences in Windows
    os.system("") 
    if sys.stdout and getattr(sys.stdout, 'isatty', lambda: False)():
        # Custom Colored ASCII Logo (Green and Cyan)
        import shutil
        GREEN = "\033[92m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
        PORT = r"""               ██████╗  ██████╗ ██████╗ ████████╗
               ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝
               ██████╔╝██║   ██║██████╔╝   ██║   
               ██╔═══╝ ██║   ██║██╔══██╗   ██║   
               ██║     ╚██████╔╝██║  ██║   ██║   
               ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝"""
        MANAGER = r"""███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ 
████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝"""
        
        term_width, term_height = shutil.get_terminal_size((80, 24))
        
        # Calculate max width of the block to center it as a whole
        port_lines = PORT.split('\n')
        manager_lines = MANAGER.split('\n')
        all_lines = port_lines + manager_lines
        max_width = max(len(line) for line in all_lines)
        
        left_padding = max(0, (term_width - max_width) // 2)
        pad_str = " " * left_padding
        
        # Apply padding and colors
        logo_lines = [GREEN + pad_str + line for line in port_lines] + \
                     [CYAN + pad_str + line for line in manager_lines]
        
        # Center vertically
        top_padding = max(0, (term_height - len(logo_lines)) // 2 - 2)
        
        ascii_logo = ('\n' * top_padding) + '\n'.join(logo_lines) + f"\n{RESET}\n"
        
        # Clear screen first to ensure centering works properly
        os.system("cls" if os.name == "nt" else "clear")
        sys.stdout.write(ascii_logo)
        sys.stdout.flush()

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, DataTable
from textual.reactive import reactive
from textual.binding import Binding

from forwarding_logic import PortForwardingMixin
from app_actions import AppActionsMixin
from utils import get_target_ports, get_running_processes
from widgets import AppSidebar, AppTable, AppInspector
from audio import audio

class PortManagerApp(PortForwardingMixin, AppActionsMixin, App):
    """A highly refined, modern Textual App for Port Management."""
    
    CSS_PATH = ["styles/layout.tcss", "styles/components.tcss", "styles/table.tcss", "styles/inspector.tcss", "styles/modals.tcss"]

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("Q", "quit", "Quit", show=False),
        Binding("r", "refresh_data", "Refresh"),
        Binding("R", "refresh_data", "Refresh", show=False),
        Binding("+", "add_port", "Add"),
        Binding("=", "add_port", "Add", show=False),
        Binding("~", "edit_selected", "Edit"),
        Binding("`", "edit_selected", "Edit", show=False),
        Binding("-", "untrack_selected", "Untrack"),
        Binding("k", "kill_selected", "Kill Selected"),
        Binding("K", "kill_selected", "Kill Selected", show=False),
        Binding("ctrl+k", "kill_all", "Kill All"),
        Binding("n", "toggle_dark", "Toggle Theme"),
        Binding("N", "toggle_dark", "Toggle Theme", show=False),
        Binding("f", "toggle_forward", "Toggle FWD"),
        Binding("F", "toggle_forward", "Toggle FWD", show=False),
        Binding("s", "open_settings", "Settings", show=False),
        Binding("S", "open_settings", "Settings", show=False)
    ]

    target_ports = reactive(set())
    processes_data = reactive([])
    forwarded_ports = reactive({})

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="root_layout"):
            yield AppSidebar(id="sidebar")
            
            with Container(id="main_content"):
                with Horizontal(id="main_split"):
                    yield AppTable(id="table_wrapper")
                    yield AppInspector(id="process_details_panel")
                    
        yield Footer()

    def on_mount(self) -> None:
        import os
        if os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW('PortManager TUI')
            
        self.title = "PORT MANAGER"
        self.sub_title = "Network Guardian"
        
        self.action_refresh_data(play_sound=False)
        
        table = self.query_one(DataTable)
        table.focus()
        
        from splash import StartupSplashScreen
        
        def _on_splash_dismissed(_=None):
            # Trigger CSS mount animation
            table_wrapper = self.query_one("#table_wrapper")
            self.set_timer(0.05, lambda: table_wrapper.add_class("-loaded"))
            self.set_timer(0.1, lambda: self.query_one("#sidebar").add_class("-loaded"))
            self.set_timer(0.15, lambda: self.query_one("#process_details_panel").add_class("-loaded"))
            
            def _fix_table_render():
                if hasattr(table, "_clear_caches"):
                    table._clear_caches()
                table.refresh()
                self.update_table()
            self.set_timer(0.27, _fix_table_render)

        self.push_screen(StartupSplashScreen(), _on_splash_dismissed)


    async def action_quit(self) -> None:
        """Override quit app to include confirmation if ports are forwarded."""
        from audio import audio
        import devtunnel_utils
        audio.play("click")
        if self.forwarded_ports:
            from modals import ConfirmAppQuitScreen
            async def _handle_quit_confirm(confirm: bool):
                if confirm:
                    await devtunnel_utils.cleanup_all_tunnels()
                    self.exit()
            
            self.push_screen(ConfirmAppQuitScreen(), _handle_quit_confirm)
        else:
            await devtunnel_utils.cleanup_all_tunnels()
            self.exit()

    def watch_forwarded_ports(self, old_val, new_val) -> None:
        self.update_table()
        self.update_inspector()

    def action_toggle_dark(self) -> None:
        audio.play("click")
        self.dark = not self.dark
        self.update_table()
        self.update_sidebar()

    def action_refresh_data(self, play_sound: bool = True) -> None:
        if play_sound:
            audio.play("click")
        self.target_ports = get_target_ports()
        self.processes_data = get_running_processes(self.target_ports)
        self.update_table()
        self.update_sidebar()

    def action_command_palette(self) -> None:
        """Override default red circle behavior in Header to open settings."""
        self.action_open_settings()

    def action_open_settings(self) -> None:
        audio.play("click")
        from modals import SettingsScreen
        self.push_screen(SettingsScreen())

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        try:
            table = self.query_one(DataTable)
            row_idx = table.cursor_coordinate.row if table.cursor_coordinate else None
        except Exception:
            row_idx = None
        
        if getattr(self, "_last_highlighted_row", None) == row_idx:
            return
            
        self._last_highlighted_row = row_idx
        
        if not getattr(self, "_is_refreshing", False):
            # Check if triggered by instant row click
            self.set_timer(0.05, self._play_scroll_if_valid)
            setattr(self, "_highlight_cancel_scroll", False)
        self.update_sidebar()
        self.update_inspector()

    def _play_scroll_if_valid(self):
        if not getattr(self, "_highlight_cancel_scroll", False):
            audio.play("scroll")

    def _get_selected_process(self) -> dict | None:
        """Helper to fetch the currently selected process struct from the DataTable."""
        try:
            table = self.query_one(DataTable)
            if not table.cursor_coordinate:
                return None
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key.value is None:
                return None
            idx = int(str(row_key.value))
            return self.processes_data[idx]
        except Exception:
            return None

    def update_sidebar(self) -> None:
        try:
            val = self._get_selected_process()
            self.query_one(AppSidebar).update_sidebar(self.processes_data, self.target_ports, val)
        except Exception:
            pass

    def update_table(self) -> None:
        try:
            self._is_refreshing = True
            app_table_matches = self.query(AppTable)
            if app_table_matches:
                app_table_matches.first().populate_table(self.processes_data, self.forwarded_ports)
            self.set_timer(0.45, lambda: setattr(self, "_is_refreshing", False))
        except Exception:
            self.log.exception("Failed to update table")
            self._is_refreshing = False

    def update_inspector(self) -> None:
        try:
            proc = self._get_selected_process()
            url = self.forwarded_ports.get(proc['port']) if proc else None
            self.query_one(AppInspector).update_inspector(proc, url)
        except Exception:
            pass

if __name__ == "__main__":
    app = PortManagerApp()
    app.run()
