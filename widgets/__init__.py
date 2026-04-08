from rich.text import Text
from textual.events import Mount
from textual.widgets._header import HeaderTitle
from textual.widgets._toast import Toast, ToastHolder

# --- Monkeypatch HeaderTitle to support dynamic subtitle colors ---
def custom_header_render(self) -> Text:
    text = Text(self.text, no_wrap=True, overflow="ellipsis")
    if self.sub_text:
        text.append(" — ")
        # Use different color based on theme
        color = "#48495C" if getattr(self.app, "dark", True) else "#d0d3d8"
        text.append(self.sub_text, style=f"italic {color}")
    return text

HeaderTitle.render = custom_header_render

# --- Monkeypatch Toast for "hard, creative" slide-in & slide-out animations ---
_original_toast_on_mount = Toast._on_mount

def custom_toast_on_mount(self, _: Mount) -> None:
    _original_toast_on_mount(self, _)
    # Add -loaded class on the next tick to trigger the CSS transition
    self.call_after_refresh(lambda: self.add_class("-loaded"))

_original_toastholder_remove = ToastHolder.remove

def custom_toastholder_remove(self, *args, **kwargs):
    if not self.has_class("toast--closing"):
        self.add_class("toast--closing")
        toast = self.children[0] if self.children else None
        if toast:
            toast.add_class("toast--closing")
            toast.remove_class("-loaded")
        self.set_timer(0.25, lambda: _original_toastholder_remove(self, *args, **kwargs))
        return None
    return _original_toastholder_remove(self, *args, **kwargs)

Toast._on_mount = custom_toast_on_mount  # type: ignore
ToastHolder.remove = custom_toastholder_remove  # type: ignore

from .sidebar import AppSidebar
from .table import AppTable
from .inspector import AppInspector
from .theme import ThemeColors

__all__ = ["AppSidebar", "AppTable", "AppInspector", "ThemeColors"]