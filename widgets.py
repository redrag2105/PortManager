from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import DataTable, Button, Static, Label
from textual.widgets._header import HeaderTitle
from textual.widgets._toast import Toast, ToastHolder
from textual.events import Mount
from utils import get_process_details
import datetime

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

LOGO = r"""
 ╭─╮┌─╮┬─╮┌┬┐
 ├─╯│ │├┬╯ │ 
 ┴  └─╯┴└─ ┴ 
"""

class ThemeColors:
    """Helper to extract and DRY up theme colors."""
    @staticmethod
    def get(is_dark: bool) -> dict:
        return {
            "active": "#a6e3a1" if is_dark else "#40a02b",
            "inactive": "#585b70" if is_dark else "#9ca0b0",
            "port": "bold #cba6f7" if is_dark else "bold #1e66f5",
            "pid": "#89b4fa" if is_dark else "#209fb5",
            "name": "bold" if is_dark else "bold #4c4f69",
            "edit": "#fab387" if is_dark else "#df8e1d",
            "delete": "#f38ba8" if is_dark else "#d20f39",
            "accent": "#cba6f7" if is_dark else "#1e66f5"
        }

class AppSidebar(Vertical):
    """The sidebar containing the logo, connection stats, and primary action buttons."""
    
    def compose(self) -> ComposeResult:
        with Container(id="logo_box"):
            yield Static(LOGO, id="logo")
            yield Static("M A N A G E R", id="logo_manager")
        with Container(id="stats_box"):
            yield Label("Loading stats...", id="stats")
        with Vertical(id="button_group"):
            yield Button("+ Add Port", id="btn_add_port")
            yield Button("↻ Refresh", id="btn_refresh")
            yield Button("✕ Kill Selected", id="btn_kill_selected")
            yield Button("⚠ Kill All", id="btn_kill_all")

    def update_stats(self, processes_data: list, target_ports: set) -> None:
        running = sum(1 for p in processes_data if p['status'] == 'RUNNING')
        total = len(target_ports)
        is_dark = getattr(self.app, "dark", True)
        
        active_color = ThemeColors.get(is_dark)["active"]
        stats_msg = (
            f"Total tracked: [bold]{total}[/]\n"
            f"Active ports : [bold {active_color}]{running}[/]"
        )
        try:
            self.query_one("#stats", Label).update(stats_msg)
        except Exception:
            pass

class AppTable(Container):
    """Wrapper for the dynamic data table displaying port configurations."""
    
    def compose(self) -> ComposeResult:
        yield DataTable(id="ports_table")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        table.add_columns(
            Text("STATUS", justify="center"),
            Text("PORT", justify="center"),
            Text("PID", justify="center"),
        )

        table.add_column(Text("PROCESS", justify="center"), width=15)
        
        table.add_columns(
            Text("MOD", justify="center"),
            Text("DEL", justify="center"),
            Text("FWD", justify="center"),
        )

    def populate_table(self, processes_data: list, forwarded_ports: dict | None = None) -> None:
        if forwarded_ports is None:
            forwarded_ports = {}
        table = self.query_one(DataTable)
        table.clear()
        
        is_dark = getattr(self.app, "dark", True)
        c = ThemeColors.get(is_dark)

        for idx, proc in enumerate(processes_data):
            is_run = proc['status'] == 'RUNNING'
            fwd_status = forwarded_ports.get(proc['port'])

            fwd_text = "[ ]"
            fwd_style = c["inactive"]
            if fwd_status == "loading":
                fwd_text = "[?]"
                fwd_style = c["edit"]
            elif fwd_status:
                fwd_text = "[x]"
                fwd_style = c["active"]
                
            is_forwarding = bool(fwd_status)
            edit_text_col = c["inactive"] if is_forwarding else c["edit"]
            delete_text_col = c["inactive"] if is_forwarding else c["delete"]

            table.add_row(
                Text("●" if is_run else "○", style=c["active"] if is_run else c["inactive"], justify="center"),
                Text(str(proc['port']), style=c["port"] if is_run else c["inactive"], justify="center"),
                Text(str(proc['pid']), style=c["pid"] if is_run else c["inactive"], justify="center"),
                Text(str(proc['name']), style=c["name"] if is_run else c["inactive"], justify="center"),
                Text("~", style=edit_text_col, justify="center"),
                Text("-", style=delete_text_col, justify="center"),
                Text(fwd_text, style=fwd_style, justify="center"),
                key=str(idx)
            )

class AppInspector(Vertical):
    """The side panel for displaying highly detailed OS-level metrics per port/PID."""
    
    def compose(self) -> ComposeResult:
        yield Label("PROCESS INSPECTOR", id="details_title")
        with Container(id="details_content_box"):
            yield Label("Select a process to view details.", id="details_content")

    def update_inspector(self, proc: dict | None, public_url: str | tuple[str, str] | None = None) -> None:
        if not proc:
            return
            
        try:
            lbl = self.query_one("#details_content", Label)
            is_dark = getattr(self.app, "dark", True)
            c = ThemeColors.get(is_dark)
            
            if proc["pid"] == "-" or not str(proc["pid"]).isdigit():
                lbl.update(f"\n[bold {c['delete']}]PORT {proc['port']} IS INACTIVE[/]\n\nNo process is currently listening on this port.")
                return
                
            details = get_process_details(proc["pid"])
            if not details:
                lbl.update(f"\n[bold {c['edit']}]ACCESS DENIED[/]\n\nUnable to fetch detailed information for PID {proc['pid']}.")
                return
                
            dt = datetime.datetime.fromtimestamp(details['created']).strftime("%Y-%m-%d %H:%M:%S")
            mem = f"{details['memory']:.1f} MB"
            cpu = f"{details['cpu']:.1f}%"
            
            accent = c['accent']
            content = (
                f"[{accent} bold]Name:[/] {details['name']}\n"
                f"[{accent} bold]PID:[/] {proc['pid']}\n"
                f"[{accent} bold]Port:[/] {proc['port']}\n"
                f"[{accent} bold]User:[/] {details.get('username', 'N/A')}\n"
                f"[{accent} bold]Status:[/] {details.get('status', 'running').upper()}\n\n"
                f"[{accent} bold]Memory:[/] {mem}\n"
                f"[{accent} bold]CPU:[/] {cpu}\n"
                f"[{accent} bold]Started:[/] \n{dt}\n\n"
                f"[{accent} bold]Path:[/] \n{details.get('exe', 'Unknown')}"
            )
            if public_url and public_url != "loading":
                if isinstance(public_url, tuple):
                    content += f"\n\n[{accent} bold]Public URL:[/] \n[link={public_url[0]}]{public_url[0]}[/link]"
                    if len(public_url) > 1:
                        content += f"\n\n[{accent} bold]Inspect URL:[/] \n[link={public_url[1]}]{public_url[1]}[/link]"
                else:
                    content += f"\n\n[{accent} bold]Public URL:[/] \n[link={public_url}]{public_url}[/link]"
            lbl.update(content)
        except Exception:
            pass