"""CLI Common module."""
from typing import Dict, List, Union

import io
import json
import ruamel.yaml

import click


def serialize(data: Union[Dict, List], format: str='json') -> str:
    """Serializes data in the specified format.

    Args:
        data (Dict, List): Data dictionary or list.
        format (str): Serialization format (default = `json`)

    Returns:
        Serialized data (str).

    Raises:
        ValueError("Invalid format."): if serialization format is invalid.
    """
    if format == 'json':
        out = json.dumps(data, indent=2)

    elif format == 'yaml':
        yaml = ruamel.yaml.YAML()
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)

        with io.StringIO() as stream:
            yaml.dump(data, stream)
            out = stream.getvalue()

    else:
        raise ValueError("Invalid format.", format)

    return out


def format_option(func):
    """Output format option."""
    return click.option(
        '--format',
        type=click.Choice(['text', 'json', 'yaml'], case_sensitive=False),
        default='text',
        show_default=True,
        help="Output format.",
    )(func)


def custom_options(opts):
    """Decorator factory to add options dynamically."""
    def decorator(func):
        for name, desc in opts.items():
            func = click.option(f"--{name}", help=desc)(func)
        return func
        
    return decorator