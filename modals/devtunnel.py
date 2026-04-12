from typing import TypeVar
from textual import work
from textual.app import ComposeResult
from textual.containers import Grid, Vertical, VerticalScroll, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input, Switch
from modals.slider import CustomSlider as Slider
from textual.binding import Binding
from audio import audio

ResultType = TypeVar("ResultType")

from .base import ActionModalScreen

class DevTunnelInstallScreen(ActionModalScreen):
    """Screen to install Dev Tunnels CLI."""
    def __init__(self):
        super().__init__(
            message="Port forwarding requires the Microsoft Dev Tunnels CLI. Would you like PortManager to automatically download and configure it for your OS?",
            ok_text="Download & Install",
            no_text="Cancel",
            ok_id="add_port_confirm",
            no_id="add_port_cancel"
        )
        self._is_working = False

    def action_dismiss_modal(self) -> None:
        if getattr(self, "_is_working", False):
            return
        audio.play("close")
        super().action_dismiss_modal()

    def _handle_submit(self) -> None:
        from textual.widgets import ProgressBar
        self._is_working = True
        self.query_one("#question", Label).update("Downloading... Please wait.")
        for btn in self.query(Button):
            btn.remove()

        pb = ProgressBar(total=100, show_eta=False, id="download_progress")
        self.query_one("#dialog").mount(pb)
        self.start_download()

    def update_progress(self, current: int) -> None:
        from textual.widgets import ProgressBar
        try:
            pb = self.query_one("#download_progress", ProgressBar)
            pb.update(progress=current)
        except Exception:
            pass

    @work(thread=True)
    def start_download(self) -> None:
        import devtunnel_utils
        
        def _on_progress(percent: int):
            self.app.call_from_thread(self.update_progress, percent)
            
        success = devtunnel_utils.download_devtunnel_cli(progress_callback=_on_progress)
        self.app.call_from_thread(self.dismiss, success)


class DevTunnelAuthScreen(ActionModalScreen):
    """Screen to confirm browser login for Dev Tunnels."""
    def __init__(self, is_expired: bool = False):
        msg = (
            "Your Microsoft Dev Tunnels login token has expired. Please log in again to host public ports. Clicking Login will open your web browser."
            if is_expired else
            "You must log in to Microsoft Dev Tunnels to host public ports. Clicking Login will open your web browser."
        )
        super().__init__(
            message=msg,
            ok_text="Login",
            no_text="Cancel",
            ok_id="add_port_confirm",
            no_id="add_port_cancel"
        )

