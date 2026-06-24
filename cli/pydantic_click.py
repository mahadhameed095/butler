import functools
from pydantic import BaseModel
import click
from pydantic import create_model
from typing import Optional

def make_optional(model: type[BaseModel]) -> type[BaseModel]:
    return create_model(
        f"Partial{model.__name__}",
        **{
            field_name: (Optional[field_info.annotation], None)
            for field_name, field_info in model.model_fields.items()
        }
    )

def pydantic_options(model: type[BaseModel]):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(**kwargs):
            mapped = {field: kwargs.get(field.lower()) for field in model.model_fields}
            return f(model(**mapped))

        for field_name in reversed(model.model_fields):
            cli_name = f"--{field_name.lower().replace('_', '-')}"
            wrapper = click.option(cli_name, field_name.lower(), default=None)(wrapper)

        return wrapper
    return decorator