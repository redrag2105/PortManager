from textual.widgets import Label

from textual.message import Message
from textual.events import Click, MouseDown, MouseMove, MouseUp

class CustomSlider(Label):
    """Custom slider implementation replacing standard Textual slider."""
    
    class Changed(Message):
        def __init__(self, slider: "CustomSlider", value: int) -> None:
            self.slider = slider
            self.value = value
            super().__init__()

    def __init__(self, min_val: int = 0, max_val: int = 100, value: int = 50, step: int = 1, id: str | None = None, classes: str | None = None):
        super().__init__(id=id)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self._value = value
        self._dragging = False
        if classes:
            self.classes = classes

    @property
    def value(self) -> int:
        return self._value
        
    @value.setter
    def value(self, new_val: int) -> None:
        new_val = max(self.min_val, min(self.max_val, new_val))
        if self._value != new_val:
            self._value = new_val
            self.refresh()
            self.post_message(self.Changed(self, self.value))

    def render(self) -> str:
        width = 20
        percent = (self.value - self.min_val) / (self.max_val - self.min_val) if self.max_val > self.min_val else 0
        filled = int(percent * width)
        empty = width - filled
        circle = "○" if (self.disabled or self.has_class("muted")) else "●"
        return f"{'━' * filled}{circle}{'─' * empty}"

    def update_from_x(self, x: int) -> None:
        if self.has_class("muted"):
            return
        width = 20
        try:
            widget_width = self.size.width
        except Exception:
            widget_width = 25
            
        offset = max(0, (widget_width - 21) // 2)
        adjusted_x = x - offset
        
        percent = max(0, min(1, adjusted_x / width))
        new_val = int(percent * (self.max_val - self.min_val) + self.min_val)
        new_val = round(new_val / self.step) * self.step
        self.value = new_val

    def on_mouse_down(self, event: MouseDown) -> None:
        if self.has_class("muted"):
            return
        self._dragging = True
        self.capture_mouse()
        self.update_from_x(event.x)
        
    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging:
            self.update_from_x(event.x)
            
    def on_mouse_up(self, event: MouseUp) -> None:
        self._dragging = False
        self.release_mouse()

    def on_click(self, event: Click) -> None:
        # Click handled by mouse_down
        pass