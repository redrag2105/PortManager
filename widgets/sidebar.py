from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Label, Button
from .theme import ThemeColors

LOGO = r"""
 ╭─╮┌─╮┬─╮┌┬┐
 ├─╯│ │├┬╯ │ 
 ┴  └─╯┴└─ ┴ 
"""

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
            yield Button(" ⃠ Kill All", id="btn_kill_all")

    def update_sidebar(self, processes_data: list, target_ports: set, selected_proc: dict | None) -> None:
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
            
            # Update buttons state
            self.query_one("#btn_kill_selected", Button).disabled = not selected_proc or selected_proc.get("status") == "INACTIVE"
            self.query_one("#btn_kill_all", Button).disabled = (running == 0)
        except Exception:
            pass
