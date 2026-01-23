from pylib.lib.fns import getCLI
from pathlib import Path

cli = getCLI()
Tp,tp,ta,to,ant = cli.getTyperShortcuts()

@cli.cmd
def extract_lib(
    src: ant[Path, ta(help="Path to extract from.")],
    dst: ant[Path, ta(help="Path to extract into.")] = (
        Path(__file__) / ".." / "lib"
    ).resolve(),
    force: ant[bool, to("-f", help="pass to skip confirmations")] = False,
):
    """Extract the pylib code from the given path."""

    # TODO
    pass