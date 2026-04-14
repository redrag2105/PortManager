from typing import TypeVar
from textual.app import ComposeResult
from textual.containers import Grid, Vertical, VerticalScroll, Horizontal
from textual.widgets import Button, Label, Input, Switch
from modals.slider import CustomSlider as Slider
from audio import audio

ResultType = TypeVar("ResultType")

from .base import BaseSharedModal

class VolumeControl(Horizontal):
    def __init__(self, sound_name: str, initial_value: int) -> None:
        super().__init__()
        self.sound_name = sound_name
        self.initial_value = initial_value
        self.classes = "volume-control-row"

    def compose(self) -> ComposeResult:
        yield Label(f"{self.sound_name.capitalize()}", classes="volume-label")
        yield Slider(min_val=0, max_val=100, value=self.initial_value, step=1, id=f"slider_{self.sound_name}", classes="volume-slider")
        yield Input(value=str(self.initial_value), restrict=r"^[0-9]{0,3}$", id=f"input_{self.sound_name}", classes="volume-input")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == f"input_{self.sound_name}":
            try:
                val = int(event.input.value) if event.input.value else 0
                val = min(100, max(0, val))
                self.query_one(Slider).value = val
            except ValueError:
                pass
            event.stop()

    def on_custom_slider_changed(self, event: Slider.Changed) -> None:
        if event.slider.id == f"slider_{self.sound_name}":
            self.query_one(Input).value = str(int(event.value))
            event.stop()


class SettingsScreen(BaseSharedModal[None]):
    """Modern Settings modal configuration."""
    CSS_PATH = ["../styles/settings.tcss", "../styles/components.tcss"]
    
    def action_dismiss_modal(self) -> None:
        audio.play("close")
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        with Vertical(id="settings_dialog"):
            yield Label("Audio Settings", id="add_port_title")
            
            with Horizontal(id="mute-container", classes="settings-row"):
                yield Label("Mute All Sounds")
                yield Switch(value=audio.is_muted, id="settings_mute")

            self.controls_container = VerticalScroll(id="volume-controls-container")
            with self.controls_container:
                for sound_name, volume in audio.volumes.items():
                    yield VolumeControl(sound_name, int(volume * 100))
            
            with Grid(id="add_port_buttons"):
                yield Button("Save", id="settings_save")
                yield Button("Cancel", id="add_port_cancel")

    def on_mount(self) -> None:
        self.update_controls_state(audio.is_muted)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "settings_mute":
            audio.play("click")
            self.update_controls_state(event.value)

    def update_controls_state(self, is_muted: bool) -> None:
        if is_muted:
            self.controls_container.add_class("disabled")
        else:
            self.controls_container.remove_class("disabled")
        
        for slider in self.query(Slider):
            if is_muted:
                slider.add_class("muted")
            else:
                slider.remove_class("muted")
            slider.refresh()

        for inp in self.query(Input):
            inp.can_focus = not is_muted
            if is_muted:
                inp.add_class("muted")
                if inp.has_focus:
                    self.set_focus(None)
            else:
                inp.remove_class("muted")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings_save":
            from utils import get_settings, save_settings
            settings = get_settings()
            
            is_muted = self.query_one("#settings_mute", Switch).value
            audio.set_mute(is_muted)
            
            for vc in self.query(VolumeControl):
                inp = vc.query_one(Input)
                if inp.value.isdigit():
                    vol = min(100, max(0, int(inp.value))) / 100.0
                    name = vc.sound_name
                    audio.volumes[name] = vol
                    if name in audio.sounds and not audio.is_muted:
                        audio.sounds[name].set_volume(vol)
            
            settings["sounds"] = {
                "mute": is_muted,
                "volumes": audio.volumes
            }
            if save_settings(settings):
                audio.play("success")
                self.dismiss(None)
            else:
                audio.play("error")
                self.app.notify("Failed to save audio settings to file.", severity="error")
        elif event.button.id == "add_port_cancel":
            audio.play("close")
            self.dismiss(None)
        else:
            audio.play("click")
