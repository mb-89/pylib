from pylib.lib.fns import getCLI
from pathlib import Path
from pylib.lib.tui import cli_tui
cli = getCLI()

@cli.cmd
def tui():
    """Display the commandline interface inside a tui."""

    cli_tui.run()