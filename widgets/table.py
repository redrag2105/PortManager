from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import DataTable
from textual import events
from rich.text import Text
from .theme import ThemeColors

class AppTable(Container):
    """Wrapper for the dynamic data table displaying port configurations."""
    
    # Layout constants mirroring styles.tcss
    SIDEBAR_AND_PADDING_WIDTH = 34
    TABLE_WIDTH_PERCENTAGE = 0.65
    TABLE_RIGHT_MARGIN = 1
    
    def compose(self) -> ComposeResult:
        yield DataTable(id="ports_table")

    def on_resize(self, event: events.Resize) -> None:
        try:
            if hasattr(self.app, "processes_data"):
                self.populate_table(
                    getattr(self.app, "processes_data", []), 
                    getattr(self.app, "forwarded_ports", {})
                )
        except Exception as e:
            self.app.log.error(f"Table resize failed: {e}")

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

        table.add_column(Text("PROCESS", justify="center"), key="process")
        
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

        term_width = getattr(self.app, "size", self.size).width
        if term_width == 0:
            term_width = 120
            
        main_content_w = max(10, term_width - self.SIDEBAR_AND_PADDING_WIDTH)
        table_wrapper_w = int(main_content_w * self.TABLE_WIDTH_PERCENTAGE) - self.TABLE_RIGHT_MARGIN
        
        fixed_col_width = 3
        for col_key, col in table.columns.items():
            if str(col_key.value) != "process":
                fixed_col_width += len(col.label.plain) + 2
                
        target_process_width = max(15, table_wrapper_w - fixed_col_width)
        
        for col_key, col in table.columns.items():
            if str(col_key.value) == "process":
                col.width = target_process_width
                col.auto_width = False
                break

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

            proc_name = str(proc['name'])
            if len(proc_name) > target_process_width:
                proc_name = proc_name[:target_process_width-3] + "..."

            table.add_row(
                Text("●" if is_run else "○", style=c["active"] if is_run else c["inactive"], justify="center"),
                Text(str(proc['port']), style=c["port"] if is_run else c["inactive"], justify="center"),
                Text(str(proc['pid']), style=c["pid"] if is_run else c["inactive"], justify="center"),
                Text(proc_name, style=c["name"] if is_run else c["inactive"], justify="center"),
                Text("~", style=edit_text_col, justify="center"),
                Text("-", style=delete_text_col, justify="center"),
                fwd_cell,
                key=str(idx)
            )