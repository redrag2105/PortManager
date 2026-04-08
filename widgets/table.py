from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import DataTable
from rich.text import Text
from .theme import ThemeColors

class AppTable(Container):
    """Wrapper for the dynamic data table displaying port configurations."""
    
    def compose(self) -> ComposeResult:
        yield DataTable(id="ports_table")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.cursor_foreground_priority = "renderable"
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

            if fwd_status == "loading":
                fwd_cell = Text("?", style=f"blink {c['edit']}", justify="center")
            elif fwd_status:
                fwd_cell = Text("✓", style=c["active"], justify="center")
            else:
                fwd_cell = Text("✕", style=c["inactive"], justify="center")
                
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
                fwd_cell,
                key=str(idx)
            )