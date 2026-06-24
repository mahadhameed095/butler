from rich.console import Console
from rich.table import Table
from shared.models import App
from cli.lib import with_manifest


@with_manifest
def list_apps(ctx):
    if not ctx.apps:
        return "No apps deployed."
    table = Table()
    for header in App.model_fields.keys():
        table.add_column(header)
    for a in ctx.apps:
        table.add_row(*[str(getattr(a, f)) for f in App.model_fields.keys()])
    console = Console()
    with console.capture() as capture:
        console.print(table)
    return capture.get()


# problem: every crud command interacts with the manifest repo, so ensuring that it exists, and is valid is very important
# check if config.json exists. if it doesnt then tell them to init.
# validate config.json, if its not valid, tell them to init again.
# a valid config.json exists from this point onward
# based on config.json, check if the correct repo exists locally. if it doesnt, tell them to init again.
# from this point onward the repo exists too, but existence doesnt mean its valid. we cant trust it.
# validate the repo { manifest.csv should exist, and .github/workflows/sync.yaml should exist }
# if manifest.csv does not exist, then create an empty one with just the header based on App model.
# if manifest.csv exists, but when validated, it fails then throw warning, and halt. let the user inspect it.
# if yaml doesnt exist, copy from cli/sample-sync.yaml
# if yaml exists, but its content dont exactly match, then copy over from cli/sample-sync.yaml, but warn the user, infact prompt them if they want to continue. with the action.
# at this point when we finally reach the actual command, we will always have a valid manifest repo to work with.