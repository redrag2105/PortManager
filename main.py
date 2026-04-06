from textual.app import App, ComposeResult
from textual import on
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, DataTable, Button
from textual.reactive import reactive
from textual.binding import Binding

from modals import ConfirmKillScreen, AddPortScreen, EditPortScreen
from forwarding_logic import PortForwardingMixin
from utils import get_target_ports, get_running_processes, kill_process, add_multiple_target_ports, remove_target_port, edit_target_port
from widgets import AppSidebar, AppTable, AppInspector

class PortManagerApp(PortForwardingMixin, App):
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

    
    def watch_forwarded_ports(self, old_val, new_val) -> None:
        self.update_table()
        self.update_inspector()

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

    def update_kill_button(self) -> None:
        try:
            proc = self._get_selected_process()
            self.query_one("#btn_kill_selected", Button).disabled = not proc or proc["status"] == "INACTIVE"
        except Exception:
            pass
                
        try:
            running_procs = sum(1 for p in self.processes_data if p["status"] == "RUNNING")
            self.query_one("#btn_kill_all", Button).disabled = (running_procs == 0)
        except Exception:
            pass

    def update_stats(self) -> None:
        try:
            self.query_one(AppSidebar).update_stats(self.processes_data, self.target_ports)
        except Exception:
            pass

    def update_table(self) -> None:
        try:
            self.query_one(AppTable).populate_table(self.processes_data, self.forwarded_ports)
        except Exception:
            pass

    @on(DataTable.RowSelected)
    async def handle_row_selection(self, event: DataTable.RowSelected) -> None:
        table = self.query_one(DataTable)
        column = table.cursor_coordinate.column if table.cursor_coordinate else None
        if column is None:
            return

        # Determine if click was on Edit or Untrack column
        if column == 4:
            self.action_edit_selected()
        elif column == 5:
            self.action_untrack_selected()
        elif column == 6:
            await self.action_toggle_forward()
    def _handle_edit_port(self, old_port: int, new_port_str: str | None) -> None:
        if new_port_str is not None and new_port_str.isdigit():
            new_port = int(new_port_str)
            if edit_target_port(old_port, new_port):
                self.notify(f"Port {old_port} changed to {new_port}.", severity="information")
                self.action_refresh_data()
            else:
                self.notify(f"Failed to edit port.", severity="error")

    def _handle_untrack_port(self, port: int) -> None:
        if remove_target_port(port):
            self.notify(f"Port {port} is no longer tracked.", severity="information")
            self.action_refresh_data()
        else:
            self.notify(f"Failed to remove port.", severity="error")

    def _is_forwarding_selected(self) -> bool:
        proc = self._get_selected_process()
        return bool(proc and self.forwarded_ports.get(proc['port']))

    def check_action_edit_selected(self) -> bool:
        return not self._is_forwarding_selected()

    def check_action_untrack_selected(self) -> bool:
        return not self._is_forwarding_selected()

    def action_edit_selected(self) -> None:
        if self._is_forwarding_selected():
            return
        proc = self._get_selected_process()
        if proc:
            self.clear_notifications()
            self.push_screen(
                EditPortScreen(self.target_ports, proc['port']),
                lambda new_port: self._handle_edit_port(proc['port'], new_port)
            )

    def action_untrack_selected(self) -> None:
        if self._is_forwarding_selected():
            return
        proc = self._get_selected_process()
        if proc:
            msg = f"Stop tracking port {proc['port']}?"
            self.clear_notifications()
            self.push_screen(
                ConfirmKillScreen(msg, is_untrack=True),
                lambda confirm: self._handle_untrack_port(proc['port']) if confirm else None
            )

    def action_kill_selected(self) -> None:
        proc = self._get_selected_process()
        if not proc or proc.get("pid") == "-" or not str(proc.get("pid")).isdigit():
            return
            
        msg = f"Terminate Process: {proc['name']}\nRunning on Port: {proc['port']} (PID: {proc['pid']})?"
        self.clear_notifications()
        self.push_screen(
            ConfirmKillScreen(msg), 
            lambda confirm: self._execute_kill([proc], f"Successfully killed {proc['name']}") if confirm else None
        )

    def action_kill_all(self) -> None:
        running_procs = [p for p in self.processes_data if p["pid"] != "-" and str(p["pid"]).isdigit()]
        
        if not running_procs:
            return

        msg = f"Proceed destroying ALL {len(running_procs)} processes?"
        self.clear_notifications()
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
            self.action_add_port()
        elif event.button.id == "btn_refresh":
            self.action_refresh_data()
        elif event.button.id == "btn_kill_selected":
            self.action_kill_selected()
        elif event.button.id == "btn_kill_all":
            self.action_kill_all()

    def action_add_port(self) -> None:
        self.clear_notifications()
        self.push_screen(AddPortScreen(self.target_ports), self._handle_add_port)
            
    def _handle_add_port(self, raw_input: str | None) -> None:
        if raw_input is None or not raw_input.strip():
            return
            
        result = add_multiple_target_ports(raw_input)
        
        if "error" in result:
            self.notify(f"Failed to save changes: {result['error']}", severity="error")
            return
            
        added = result.get("added", [])
        
        if added:
            msg = f"Successfully added {len(added)} port(s): {', '.join(added)}."
            self.notify(msg, title="Ports Added", severity="information", timeout=4)
        
        # Process and show failures
        failures = []
        if result.get("failed_exists"):
            failures.append(f"{', '.join(result['failed_exists'])} (Already monitored)")
        if result.get("failed_range"):
            failures.append(f"{', '.join(result['failed_range'])} (Out of 1-65535 range)")
        if result.get("failed_invalid"):
            failures.append(f"{', '.join(result['failed_invalid'])} (Not valid numbers)")
            
        if failures:
            fail_msg = "\n".join(failures)
            self.notify(fail_msg, title="Failed to Add", severity="warning", timeout=86400)
            
        if added:
            self.action_refresh_data()


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
