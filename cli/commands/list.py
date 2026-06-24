import os
import csv
import json
from rich.console import Console
from rich.table import Table
from shared.utils import parse_github_url

BASE = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")


def list_apps():
    if not os.path.exists(CONFIG_PATH):
        return "No apps deployed."

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    dest = os.path.join(BASE, parse_github_url(config["repo_url"]).repo)
    manifest_path = os.path.join(dest, "manifest.csv")

    if not os.path.exists(manifest_path):
        return "No apps deployed."

    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return "No apps deployed."

    table = Table()
    for header in rows[0].keys():
        table.add_column(header)
    for r in rows:
        table.add_row(*r.values())

    console = Console()
    with console.capture() as capture:
        console.print(table)
    return capture.get()
