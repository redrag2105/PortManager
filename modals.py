from typing import TypeVar
from textual import work
from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input
from textual.binding import Binding

ResultType = TypeVar("ResultType")

class BaseSharedModal(ModalScreen[ResultType]):
    """Base class for all modals to apply shared CSS, Bindings, and behaviors."""
    CSS_PATH = ["styles/modals.tcss", "styles/components.tcss"]

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Cancel", show=False),
        Binding("left", "focus_previous", "Previous", show=False),
        Binding("right", "focus_next", "Next", show=False),
    ]

class ActionModalScreen(BaseSharedModal[bool]):
    """A generic two-button confirmation screen to keep code DRY."""
    def __init__(self, message: str, ok_text: str, no_text: str, ok_id: str, no_id: str):
        super().__init__()
        self.message = message
        self.ok_text = ok_text
        self.no_text = no_text
        self.ok_id = ok_id
        self.no_id = no_id

    def action_dismiss_modal(self) -> None:
        self.dismiss(False)

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Label(self.message, id="question")
            yield Button(self.ok_text, id=self.ok_id)
            yield Button(self.no_text, id=self.no_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == self.ok_id:
            self._handle_submit()
        elif event.button.id == self.no_id:
            self.dismiss(False)

    def _handle_submit(self) -> None:
        """Override this method if additional logic (like downloading CLI) is needed."""
        self.dismiss(True)


class ConfirmKillScreen(ActionModalScreen):
    """Screen with a dialog to confirm an action (process termination or untracking)."""
    def __init__(self, message: str, is_untrack: bool = False):
        super().__init__(
            message=message,
            ok_text="Untrack" if is_untrack else "Confirm Kill",
            no_text="Cancel",
            ok_id="kill",
            no_id="cancel"
        )


class BasePortScreen(BaseSharedModal[str | None]):
    """Base screen containing shared logic for Adding and Editing ports."""     

    def __init__(self, current_ports: set[int], old_port: int | None = None):   
        super().__init__()
        self.current_ports = current_ports
        self.old_port = old_port

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

    @property
    def is_edit(self) -> bool:
        return self.old_port is not None

    def compose(self) -> ComposeResult:
        with Vertical(id="add_port_dialog"):
            title = f"Edit Port {self.old_port}" if self.is_edit else "Add New Port(s)"
            yield Label(title, id="add_port_title")

            value = str(self.old_port) if self.is_edit else ""
            placeholder = "Enter new port" if self.is_edit else "e.g. 3000 3001 (space separated)"

            restrict_pattern = r"^[0-9]*$" if self.is_edit else r"^[0-9 ]*$"    
            yield Input(value=value, placeholder=placeholder, id="port_input", restrict=restrict_pattern)
            yield Label("", id="validation_warning", classes="warning_hidden")  

            with Grid(id="add_port_buttons"):
                btn_text = "Save Edit" if self.is_edit else "Add Port(s)"       
                yield Button(btn_text, id="add_port_confirm")
                yield Button("Cancel", id="add_port_cancel")

    def _show_warning(self, label: Label, msg: str) -> None:
        label.update(msg)
        label.classes = "warning_visible"

    def validate_and_submit(self) -> None:
        input_widget = self.query_one("#port_input", Input)
        warning_label = self.query_one("#validation_warning", Label)

        value = input_widget.value.strip()

        if not value:
            self._show_warning(warning_label, "Input cannot be empty.")
            return

        if self.is_edit:
            if not value.isdigit():
                self._show_warning(warning_label, "Port must be numeric.")
                return

            port = int(value)
            if not (1 <= port <= 65535):
                self._show_warning(warning_label, "Port must be between 1 and 65535.")       
                return

            if port != self.old_port and port in self.current_ports:
                self._show_warning(warning_label, "Port is already being tracked.")
                return

            self.dismiss(str(port))
        else:
            self.dismiss(value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_port_confirm":
            self.validate_and_submit()
        elif event.button.id == "add_port_cancel":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "port_input":
            self.validate_and_submit()


class AddPortScreen(BasePortScreen):
    """Screen to add a new port."""
    def __init__(self, current_ports: set[int]):
        super().__init__(current_ports, old_port=None)


class EditPortScreen(BasePortScreen):
    """Screen to edit an existing port."""
    def __init__(self, current_ports: set[int], old_port: int):
        super().__init__(current_ports, old_port=old_port)


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
        super().action_dismiss_modal()

    def _handle_submit(self) -> None:
        self._is_working = True
        self.query_one("#question", Label).update("Downloading... Please wait.")
        for btn in self.query(Button):
            btn.disabled = True
        self.download_cli()

    @work(thread=True)
    def download_cli(self) -> None:
        import devtunnel_utils
        success = devtunnel_utils.download_devtunnel_cli()
        self.app.call_from_thread(self.dismiss, success)


class DevTunnelAuthScreen(ActionModalScreen):
    """Screen to confirm browser login for Dev Tunnels."""
    def __init__(self):
        super().__init__(
            message="You must log in to Microsoft Dev Tunnels to host public ports. Clicking Login will open your web browser.",
            ok_text="Login",
            no_text="Cancel",
            ok_id="add_port_confirm",
            no_id="add_port_cancel"
        )
