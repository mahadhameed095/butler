import functools
import click
from cli.config import ButlerConfig


def with_active_manifest(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        entry = ButlerConfig.load().get_active()
        return f(entry, *args, **kwargs)
    return wrapper

def handle_errors(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except click.ClickException:
            raise
        except Exception as e:
            raise click.ClickException(str(e))
    return wrapper