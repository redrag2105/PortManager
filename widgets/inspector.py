import os
import subprocess
import platform
import datetime
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Label
from utils import get_process_details
from .theme import ThemeColors

class AppInspector(Vertical):
    """The side panel for displaying highly detailed OS-level metrics per port/PID."""

    _inspect_text_path: str | None = None
    _inspect_text_public_url: str | None = None
    _inspect_text_inspect_url: str | None = None

    def compose(self) -> ComposeResult:
        yield Label("PROCESS INSPECTOR", id="details_title")
        with Container(id="details_content_box"):
            yield Label("Select a process to view details.", id="details_content")
            
            with Horizontal(id="path_horizontal", classes="url-horizontal"):
                yield Label("Path:", id="path_header", classes="url-header")
                yield Button("❐", id="btn_copy_path", classes="btn_copy compact-btn pt-right")
            yield Label("", id="path_text")

            with Horizontal(id="public_url_horizontal", classes="url-horizontal"):
                yield Label("Public URL:", id="public_url_header", classes="url-header")
                yield Button("❐", id="btn_copy_public_url", classes="btn_copy compact-btn pt-right")
            yield Label("", id="public_url_text")

            with Horizontal(id="inspect_url_horizontal", classes="url-horizontal"):
                yield Label("Inspect URL:", id="inspect_url_header", classes="url-header")
                yield Button("❐", id="btn_copy_inspect_url", classes="btn_copy compact-btn pt-right")
            yield Label("", id="inspect_url_text")

    def on_mount(self):
        for _id in ["#path", "#public_url", "#inspect_url"]:
            self.query_one(f"{_id}_horizontal").styles.display = "none"
            self.query_one(f"{_id}_text").styles.display = "none"
        
        for btn in self.query(".btn_copy"):
            btn.tooltip = "Copy"

    @on(Button.Pressed, ".btn_copy")
    def on_copy_button_pressed(self, event: Button.Pressed) -> None:
        self.action_copy_text(event.button.id)

    def _toggle_section(self, prefix: str, show: bool):
        self.query_one(f"#{prefix}_horizontal").styles.display = "block" if show else "none"
        self.query_one(f"#{prefix}_text").styles.display = "block" if show else "none"

    def _set_section_data(self, prefix: str, title: str, copy_val: str | None, text_val: Text | None):
        setattr(self, f"_inspect_text_{prefix}", copy_val)
        if text_val:
            self._toggle_section(prefix, True)
            self.query_one(f"#{prefix}_header", Label).update(f"[{self._accent} bold]{title}[/]")
            btn = self.query_one(f"#btn_copy_{prefix}", Button)
            btn.styles.display = "block" if copy_val else "none"
            self.query_one(f"#{prefix}_text", Label).update(text_val)
        else:
            self._toggle_section(prefix, False)

    def update_inspector(self, proc: dict | None, public_url: str | tuple[str, str] | None = None) -> None:
        if not proc:
            return
            
        try:
            lbl = self.query_one("#details_content", Label)
            is_dark = getattr(self.app, "dark", True)
            c = ThemeColors.get(is_dark)
            self._accent = c['accent']
            self._edit_color = c['edit']

            def hide_all():
                for _id in ["path", "public_url", "inspect_url"]:
                    self._toggle_section(_id, False)

            if proc["pid"] == "-" or not str(proc["pid"]).isdigit():
                lbl.update(f"\n[bold {c['delete']}]PORT {proc['port']} IS INACTIVE[/]\n\nNo process is currently listening on this port.")
                hide_all()
                return
                
            details = get_process_details(proc["pid"])
            if not details:
                lbl.update(f"\n[bold {c['edit']}]ACCESS DENIED[/]\n\nUnable to fetch detailed information for PID {proc['pid']}.")
                hide_all()
                return
                
            dt = datetime.datetime.fromtimestamp(details['created']).strftime("%Y-%m-%d %H:%M:%S")
            mem = f"{details['memory']:.1f} MB"
            cpu = f"{details['cpu']:.1f}%"
            
            top_content = (
                f"[{self._accent} bold]Name:[/] {details['name']}\n"
                f"[{self._accent} bold]PID:[/] {proc['pid']}\n"
                f"[{self._accent} bold]Port:[/] {proc['port']}\n"
                f"[{self._accent} bold]User:[/] {details.get('username', 'N/A')}\n"
                f"[{self._accent} bold]Status:[/] {details.get('status', 'running').upper()}\n\n"
                f"[{self._accent} bold]Memory:[/] {mem}\n"
                f"[{self._accent} bold]CPU:[/] {cpu}\n"
                f"[{self._accent} bold]Started:[/] \n{dt}\n"
            )
            lbl.update(top_content)

            # --- Path ---
            path_display = details.get('exe', 'Unknown')
            path_val = os.path.dirname(path_display) if path_display and path_display != "Unknown" else None
            self._set_section_data("path", "Path:", path_val, Text(str(path_display), overflow="fold"))

            # --- URLs ---
            pub_url, ins_url = None, None
            if public_url and public_url != "loading":
                if isinstance(public_url, tuple):
                    pub_url = public_url[0]
                    if len(public_url) > 1:
                        ins_url = public_url[1]
                else:
                    pub_url = public_url

            pub_txt = Text.from_markup(f"[link={pub_url}]{pub_url}[/link]", overflow="fold") if pub_url else None
            self._set_section_data("public_url", "Public URL:", pub_url, pub_txt)

            ins_txt = Text.from_markup(f"[link={ins_url}]{ins_url}[/link]", overflow="fold") if ins_url else None
            self._set_section_data("inspect_url", "Inspect URL:", ins_url, ins_txt)

        except Exception:
            pass

    def action_copy_text(self, btn_id: str | None) -> None:
        if not btn_id:
            return
            
        attr_map = {
            "btn_copy_path": "_inspect_text_path",
            "btn_copy_public_url": "_inspect_text_public_url",
            "btn_copy_inspect_url": "_inspect_text_inspect_url"
        }
        
        attr_name = attr_map.get(btn_id)
        if not attr_name:
            return
            
        text_to_copy = getattr(self, attr_name, None)
        if text_to_copy:
            try:
                if platform.system() == "Windows":
                    subprocess.run('clip', input=text_to_copy.encode('utf-16le'), shell=True)
                else:
                    self.app.copy_to_clipboard(text_to_copy)  # type: ignore
                btn = self.query_one(f"#{btn_id}", Button)
                btn.tooltip = "Copied!"
                self.set_timer(2.0, lambda b=btn: setattr(b, "tooltip", "Copy"))
            except Exception as e:
                self.app.notify(f"Failed to copy: {e}", severity="error")