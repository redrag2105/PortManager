from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input

class ConfirmKillScreen(ModalScreen[bool]):
    """Screen with a dialog to confirm an action (process termination or untracking)."""

    CSS_PATH = "styles.tcss"

    def __init__(self, message: str, is_untrack: bool = False):
        super().__init__()
        self.message = message
        self.is_untrack = is_untrack

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


class AddPortScreen(ModalScreen[int | None]):
    """Screen to add a new port."""

    CSS_PATH = "styles.tcss"

    def __init__(self, current_ports: set[int]):
        super().__init__()
        self.current_ports = current_ports

    def compose(self) -> ComposeResult:
        with Vertical(id="add_port_dialog"):
            yield Label("Add New Port to Monitor", id="add_port_title")
            yield Input(placeholder="Enter port (1-65535)", id="port_input", type="integer")
            yield Label("", id="validation_warning", classes="warning_hidden")
            with Grid(id="add_port_buttons"):
                yield Button("Add Port", id="add_port_confirm")
                yield Button("Cancel", id="add_port_cancel")

    def validate_and_submit(self) -> None:
        input_widget = self.query_one("#port_input", Input)
        warning_label = self.query_one("#validation_warning", Label)
        
        value = input_widget.value.strip()
        
        if not value:
            warning_label.update("Port cannot be empty.")
            warning_label.classes = "warning_visible"
            return
            
        if not value.isdigit():
            warning_label.update("Port must be numeric.")
            warning_label.classes = "warning_visible"
            return
            
        port = int(value)
        if not (1 <= port <= 65535):
            warning_label.update("Port must be between 1 and 65535.")
            warning_label.classes = "warning_visible"
            return
            
        if port in self.current_ports:
            warning_label.update("Port is already being tracked.")
            warning_label.classes = "warning_visible"
            return
            
        # Validation passed
        self.dismiss(port)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_port_confirm":
            self.validate_and_submit()
        elif event.button.id == "add_port_cancel":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "port_input":
            self.validate_and_submit()

class EditPortScreen(ModalScreen[int | None]):
    """Screen to edit an existing port."""

    CSS_PATH = "styles.tcss"

    def __init__(self, current_ports: set[int], old_port: int):
        super().__init__()
        self.current_ports = current_ports
        self.old_port = old_port

    def compose(self) -> ComposeResult:
        with Vertical(id="add_port_dialog"):
            yield Label(f"Edit Port {self.old_port}", id="add_port_title")
            yield Input(value=str(self.old_port), placeholder="Enter port (1-65535)", id="port_input", type="integer")
            yield Label("", id="validation_warning", classes="warning_hidden")
            with Grid(id="add_port_buttons"):
                yield Button("Save Edit", id="add_port_confirm")
                yield Button("Cancel", id="add_port_cancel")

    def validate_and_submit(self) -> None:
        input_widget = self.query_one("#port_input", Input)
        warning_label = self.query_one("#validation_warning", Label)
        
        value = input_widget.value.strip()
        
        if not value:
            warning_label.update("Port cannot be empty.")
            warning_label.classes = "warning_visible"
            return
            
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
            
        # Validation passed
        self.dismiss(port)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_port_confirm":
            self.validate_and_submit()
        elif event.button.id == "add_port_cancel":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "port_input":
            self.validate_and_submit()
