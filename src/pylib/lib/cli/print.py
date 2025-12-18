from rich import print as rprint
from rich.panel import Panel

print = rprint


def panel(*args, **kwargs):
    """wrapper around rich.print(Panel(...))"""
    rprint(Panel(*args, **kwargs))
