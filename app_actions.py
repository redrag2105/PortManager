from typing import TYPE_CHECKING, Any
from audio import audio
from textual.widgets import Button, DataTable
from modals import ConfirmKillScreen, AddPortScreen, EditPortScreen
from utils import kill_process, add_multiple_target_ports, remove_target_port, edit_target_port

if TYPE_CHECKING:
    from textual.app import App
    class MixinBase(App):
        target_ports: Any
        processes_data: Any
        forwarded_ports: Any
        def action_refresh_data(self, play_sound: bool = True) -> None: ...
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
        else:
            audio.play("click")

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one(DataTable)
        if not table.cursor_coordinate:
            return
        column = table.cursor_coordinate.column 

        # Determine if click was on an action column (Edit, Untrack, Fwd)
        if column in (4, 5, 6):
            setattr(self, "_highlight_cancel_scroll", True)
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
                audio.play("success")
                self.notify(f"Port {old_port} changed to {new_port}.", severity="information")
                self.action_refresh_data(play_sound=False)
            else:
                audio.play("error")
                self.notify("Failed to edit port.", severity="error")

    def _handle_untrack_port(self, port: int) -> None:
        if remove_target_port(port):
            audio.play("success")
            self.notify(f"Port {port} is no longer tracked.", severity="information")
            self.action_refresh_data(play_sound=False)
        else:
            audio.play("error")
            self.notify("Failed to remove port.", severity="error")

    def _is_forwarding_selected(self) -> bool:
        proc = self._get_selected_process()
        return bool(proc and self.forwarded_ports.get(proc['port']))

    def check_action_edit_selected(self) -> bool:
        return not self._is_forwarding_selected()

    def check_action_untrack_selected(self) -> bool:
        return not self._is_forwarding_selected()

    def check_action_toggle_forward(self) -> bool:
        proc = self._get_selected_process()
        if not proc or proc['status'] != 'RUNNING':
            return False
            
        fwd_status = self.forwarded_ports.get(proc['port'])
        if fwd_status == "loading":
            return False
            
        return True

    def action_edit_selected(self) -> None:
        audio.play("click")
        proc = self._get_selected_process()
        if not proc or self.forwarded_ports.get(proc['port']):
            return
            
        self.clear_notifications()
        self.push_screen(
            EditPortScreen(self.target_ports, proc['port']),
            lambda new_port: self._handle_edit_port(proc['port'], new_port)
        )

    def action_untrack_selected(self) -> None:
        audio.play("click")
        proc = self._get_selected_process()
        if not proc or self.forwarded_ports.get(proc['port']):
            return
            
        msg = f"Stop tracking port {proc['port']}?"
        self.clear_notifications()
        self.push_screen(
            ConfirmKillScreen(msg, is_untrack=True),
            lambda confirm: self._handle_untrack_port(proc['port']) if confirm else None
        )

    def action_kill_selected(self) -> None:
        audio.play("click")
        proc = self._get_selected_process()
        if not proc or not str(proc.get("pid", "")).isdigit():
            return
            
        msg = f"Terminate Process: {proc['name']}\nRunning on Port: {proc['port']} (PID: {proc['pid']})?"
        self.clear_notifications()
        self.push_screen(
            ConfirmKillScreen(msg), 
            lambda confirm: self._execute_kill([proc]) if confirm else None
        )

    def action_kill_all(self) -> None:
        audio.play("click")
        running_procs = [p for p in self.processes_data if str(p.get("pid", "")).isdigit()]
        
        if not running_procs:
            return

        msg = f"Proceed destroying ALL {len(running_procs)} processes?"
        self.clear_notifications()
        self.push_screen(
            ConfirmKillScreen(msg), 
            lambda confirm: self._execute_kill(running_procs) if confirm else None
        )

    def _execute_kill(self, procs: list[dict]) -> None:
        killed_count = sum(1 for proc in procs if kill_process(int(proc["pid"])))
        self.action_refresh_data(play_sound=False)
        
        if killed_count == len(procs) and killed_count > 0:
            audio.play("success")
            msg = f"Successfully killed {procs[0]['name']}" if len(procs) == 1 else f"Killed {killed_count} active process(es)"
            self.notify(msg, title="Terminated", severity="information", timeout=3)
        elif killed_count > 0:
            audio.play("success")
            self.notify(f"Killed {killed_count}/{len(procs)} processes", title="Partial Termination", severity="warning", timeout=4)
        else:
            audio.play("error")
            name = procs[0]['name'] if len(procs) == 1 else "any processes"
            self.notify(f"Failed to kill {name}", title="Error", severity="error", timeout=4)

    def action_add_port(self) -> None:
        audio.play("click")
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
        
        failures = []
        if result.get("failed_exists"):
            failures.append(f"{', '.join(result['failed_exists'])} (Already monitored)")
        if result.get("failed_range"):
            failures.append(f"{', '.join(result['failed_range'])} (Out of 1-65535 range)")
        if result.get("failed_invalid"):
            failures.append(f"{', '.join(result['failed_invalid'])} (Not valid numbers)")

        if failures:
            audio.play("error")
        elif added:
            audio.play("success")

        if added:
            msg = f"Successfully added {len(added)} port(s): {', '.join(added)}."
            self.notify(msg, title="Ports Added", severity="information", timeout=4)
            self.action_refresh_data(play_sound=False)
            
        if failures:
            fail_msg = "\n".join(failures)
            self.notify(fail_msg, title="Failed to Add", severity="warning", timeout=10)