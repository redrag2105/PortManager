from typing import TYPE_CHECKING, Any
from textual import on
from textual.widgets import Button, DataTable
from modals import ConfirmKillScreen, AddPortScreen, EditPortScreen
from utils import kill_process, add_multiple_target_ports, remove_target_port, edit_target_port

if TYPE_CHECKING:
    from textual.app import App
    class MixinBase(App):
        target_ports: Any
        processes_data: Any
        forwarded_ports: Any
        def action_refresh_data(self) -> None: ...
        def _get_selected_process(self) -> dict | None: ...
        async def action_toggle_forward(self) -> None: ...
else:
    class MixinBase(object): pass

class AppActionsMixin(MixinBase):
    """Contains all the action handlers and callbacks for the main app."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_add_port":
            self.action_add_port()
        elif event.button.id == "btn_refresh":
            self.action_refresh_data()
        elif event.button.id == "btn_kill_selected":
            self.action_kill_selected()
        elif event.button.id == "btn_kill_all":
            self.action_kill_all()

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one(DataTable)
        if not table.cursor_coordinate:
            return
        column = table.cursor_coordinate.column 

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