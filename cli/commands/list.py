from rich.console import Console
from rich.table import Table
from shared.models import App
from cli.shared import with_manifest


@with_manifest
def list_apps(apps):
    if not apps:
        return "No apps deployed."
    table = Table()
    for header in App.model_fields.keys():
        table.add_column(header)
    for a in apps:
        table.add_row(*[str(getattr(a, f)) for f in App.model_fields.keys()])
    console = Console()
    with console.capture() as capture:
        console.print(table)
    return capture.get()
