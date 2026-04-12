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

from .base import BaseSharedModal

class BasePortScreen(BaseSharedModal[str | None]):
    """Base screen containing shared logic for Adding and Editing ports."""     

    def __init__(self, current_ports: set[int], old_port: int | None = None):   
        super().__init__()
        self.current_ports = current_ports
        self.old_port = old_port

    def action_dismiss_modal(self) -> None:
        audio.play("close")
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
        audio.play("error")
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
            audio.play("close")
            self.dismiss(None)
        else:
            audio.play("click")

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


