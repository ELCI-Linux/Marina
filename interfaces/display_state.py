import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

MEMORY_PATH = Path("~/Marina/brain/memory/latest.json").expanduser()
console = Console()

def render_context():
    if not MEMORY_PATH.exists():
        console.print("[bold red]No context file found.[/bold red]")
        return

    with open(MEMORY_PATH) as f:
        data = json.load(f)

    console.print("[bold cyan]System Overview[/bold cyan]")
    console.print(data.get("system", "Unknown"))

    scan = data.get("scan", {})
    table = Table(title="Contextual Scan Summary")
    table.add_column("Path")
    table.add_column("# Files/Desc")
    table.add_column("# Dirs/Desc")

    for path, meta in list(scan.items())[:15]:
        table.add_row(str(path), str(meta.get("files", "-")), str(meta.get("dirs", "-")))

    console.print(table)# display_state.py - Scaffold placeholder
