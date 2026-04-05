from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input
from textual.binding import Binding

class ConfirmKillScreen(ModalScreen[bool]):
    """Screen with a dialog to confirm an action (process termination or untracking)."""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Cancel", show=False),
        Binding("left", "focus_previous", "Previous", show=False),
        Binding("right", "focus_next", "Next", show=False),
    ]

    def __init__(self, message: str, is_untrack: bool = False):
        super().__init__()
        self.message = message
        self.is_untrack = is_untrack

    def action_dismiss_modal(self) -> None:
        self.dismiss(False)

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Label(self.message, id="question")
            btn_text = "Untrack" if self.is_untrack else "Confirm Kill"
            yield Button(btn_text, id="kill")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "kill":
            self.dismiss(True)
        elif event.button.id == "cancel":
            self.dismiss(False)


class BasePortScreen(ModalScreen[str | None]):
    """Base screen containing shared logic for Adding and Editing ports."""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Cancel"),
        Binding("left", "focus_previous", "Previous", show=False),
        Binding("right", "focus_next", "Next", show=False),
    ]

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

    def validate_and_submit(self) -> None:
        input_widget = self.query_one("#port_input", Input)
        warning_label = self.query_one("#validation_warning", Label)

        value = input_widget.value.strip()

        if not value:
            warning_label.update("Input cannot be empty.")
            warning_label.classes = "warning_visible"
            return
            
        if self.is_edit:
            if not value.isdigit():
                warning_label.update("Port must be numeric.")
                warning_label.classes = "warning_visible"
                return

            port = int(value)
            if not (1 <= port <= 65535):
                warning_label.update("Port must be between 1 and 65535.")
                warning_label.classes = "warning_visible"
                return

            if port != self.old_port and port in self.current_ports:
                warning_label.update("Port is already being tracked.")
                warning_label.classes = "warning_visible"
                return
                
            self.dismiss(str(port))
        else:
            # Let main.py handle complex validation and reporting.
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
