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
class BaseSharedModal(ModalScreen[ResultType]):
    """Base class for all modals to apply shared CSS, Bindings, and behaviors."""
    CSS_PATH = ["../styles/modals.tcss", "../styles/components.tcss"]

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
        audio.play("close")
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
            audio.play("close")
            self.dismiss(False)
        else:
            audio.play("click")

    def _handle_submit(self) -> None:
        """Override this method if additional logic (like downloading CLI) is needed."""
        self.dismiss(True)


