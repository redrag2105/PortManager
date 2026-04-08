from textual import work
import devtunnel_utils
import time
import threading

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from textual.app import App
    class _BaseApp(App):
        forwarded_ports: dict
        def _get_selected_process(self) -> Any: ...
        def update_inspector(self) -> None: ...
        def clear_notifications(self) -> None: ...
else:
    _BaseApp = object

class PortForwardingMixin(_BaseApp):
    async def action_toggle_forward(self) -> None:
        proc = self._get_selected_process()
        if not proc or proc['status'] != 'RUNNING':
            return

        port = proc['port']
        fwd_status = self.forwarded_ports.get(port)

        if fwd_status:
            # Stop port forwarding
            if await devtunnel_utils.stop_port_forward(port):
                fwd = dict(self.forwarded_ports)
                fwd.pop(port, None)
                self.forwarded_ports = fwd
                self.notify(f"Port {port} forwarding stopped.", severity="information")
            return

        # Not forwarded yet. Start DevTunnel logic
        # Check limit
        if len(self.forwarded_ports) >= 5:
            self.notify("Maximum of 5 forwarded ports reached.", severity="error")
            return

        self._start_devtunnel_flow(port)

    @work(thread=True)
    def _start_devtunnel_flow(self, port: int) -> None:
        if devtunnel_utils.check_devtunnel_cli():
            self._start_devtunnel_auth_and_run(port)
            return

        from modals import DevTunnelInstallScreen
        def handle_install(success: bool):
            if success:
                self._start_devtunnel_auth_and_run(port)
            else:
                self.notify("Dev Tunnels CLI installation failed or was cancelled.", severity="error")
        self.app.call_from_thread(self.clear_notifications)
        self.app.call_from_thread(self.push_screen, DevTunnelInstallScreen(), handle_install)

    def _start_devtunnel_auth_and_run(self, port: int) -> None:
        def _check_and_auth():
            status = devtunnel_utils.check_login_status()
            if status == 'logged_in':
                self.app.call_from_thread(self._run_port_forward, port)
                return

            from modals import DevTunnelAuthScreen
            def handle_auth(confirm: bool):
                if confirm:
                    self.notify("Waiting for browser authentication...", severity="information", timeout=60)
                    self._trigger_login_and_wait(port)
            self.app.call_from_thread(self.clear_notifications)
            self.app.call_from_thread(self.push_screen, DevTunnelAuthScreen(is_expired=(status == 'expired')), handle_auth)
            
        threading.Thread(target=_check_and_auth, daemon=True).start()

    @work(thread=True)
    def _trigger_login_and_wait(self, port: int) -> None:
        if devtunnel_utils.trigger_login():
            for _ in range(60):
                time.sleep(2)
                if devtunnel_utils.check_login_status() == 'logged_in':
                    self.app.call_from_thread(self.clear_notifications)
                    self.app.call_from_thread(self.notify, "Authentication successful!", severity="information")
                    self.app.call_from_thread(self._run_port_forward, port)
                    return
            self.app.call_from_thread(self.notify, "Authentication timed out.", severity="error")
        else:
            self.app.call_from_thread(self.notify, "Failed to open login.", severity="error")

    def _update_fwd_state(self, port: int, state: str | tuple[str, str] | None) -> None:
        fwd = dict(self.forwarded_ports)
        if state is None:
            fwd.pop(port, None)
        else:
            fwd[port] = state
        self.forwarded_ports = fwd

    @work
    async def _run_port_forward(self, port: int) -> None:
        self._update_fwd_state(port, "loading")
        url = await devtunnel_utils.start_port_forward(port)
        if url:
            self._update_fwd_state(port, url)
            self._notify_forward_success(port, url)
        else:
            self._update_fwd_state(port, None)
            self.notify(f"Failed to forward port {port}.", severity="error")

    def _notify_forward_success(self, port: int, url: str | tuple[str, str]) -> None:
        self.notify(f"Port {port} is now public!", severity="information", timeout=5)
        self.update_inspector()
