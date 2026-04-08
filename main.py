from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, DataTable
from textual.reactive import reactive
from textual.binding import Binding

from forwarding_logic import PortForwardingMixin
from app_actions import AppActionsMixin
from utils import get_target_ports, get_running_processes
from widgets import AppSidebar, AppTable, AppInspector

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
        Binding("-", "untrack_selected", "Untrack"),
        Binding("k", "kill_selected", "Kill Selected"),
        Binding("K", "kill_selected", "Kill Selected", show=False),
        Binding("ctrl+k", "kill_all", "Kill ALL"),
        Binding("n", "toggle_dark", "Toggle Theme"),
        Binding("N", "toggle_dark", "Toggle Theme", show=False),
        Binding("f", "toggle_forward", "Toggle FWD"),
        Binding("F", "toggle_forward", "Toggle FWD", show=False)
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
        
        self.action_refresh_data()
        
        # Trigger CSS mount animation and focus the table
        table_wrapper = self.query_one("#table_wrapper")
        self.set_timer(0.05, lambda: table_wrapper.add_class("-loaded"))
        self.set_timer(0.1, lambda: self.query_one("#sidebar").add_class("-loaded"))
        self.set_timer(0.15, lambda: self.query_one("#process_details_panel").add_class("-loaded"))
        
        table = self.query_one(DataTable)
        table.focus()

        def _fix_table_render():
            if hasattr(table, "_clear_caches"):
                table._clear_caches()
            table.refresh()
        self.set_timer(0.27, _fix_table_render)


    async def action_quit(self) -> None:
        """Override quit app to include confirmation if ports are forwarded."""
        if self.forwarded_ports:
            from modals import ConfirmAppQuitScreen
            def _handle_quit_confirm(confirm: bool):
                if confirm:
                    self.exit()
            
            self.push_screen(ConfirmAppQuitScreen(), _handle_quit_confirm)
        else:
            self.exit()

    def watch_forwarded_ports(self, old_val, new_val) -> None:
        self.update_table()
        self.update_inspector()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
        self.update_table()
        self.update_sidebar()

    def action_refresh_data(self) -> None:
        self.target_ports = get_target_ports()
        self.processes_data = get_running_processes(self.target_ports)
        self.update_table()
        self.update_sidebar()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.update_sidebar()
        self.update_inspector()

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
            self.query_one(AppTable).populate_table(self.processes_data, self.forwarded_ports)
        except Exception:
            pass

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
