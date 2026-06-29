import click
from cli.config import ManifestRepo
from cli.utils import with_active_manifest, handle_errors


@click.command("edit")
@handle_errors
@with_active_manifest
def edit(entry: ManifestRepo):
    manifest_path = entry.manifest_file_path
    if not manifest_path.exists():
        raise click.ClickException(
            f"manifest.yaml not found at {manifest_path}. "
            "Try running 'butler manifest setup' again."
        )
    click.echo(f"Opening {manifest_path}...")
    click.edit(filename=str(manifest_path))
    click.echo("Done. Run 'butler manifest commit' to deploy your changes.")
