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

class ConfirmStopForwardingScreen(ActionModalScreen):
    """Screen with a dialog to confirm stopping port forwarding."""
    def __init__(self, port: int):
        super().__init__(
            message=f"Are you sure you want to close the public tunnel for port {port}?",
            ok_text="Stop Forwarding",
            no_text="Cancel",
            ok_id="stop_forward",
            no_id="cancel"
        )

class ConfirmAppQuitScreen(ActionModalScreen):
    """Screen with a dialog to confirm quitting when ports are forwarded."""
    def __init__(self):
        super().__init__(
            message="Active forwarded ports exist! Are you sure you want to quit and close all tunnels?",
            ok_text="Force Quit",
            no_text="Cancel",
            ok_id="kill",
            no_id="cancel"
        )


