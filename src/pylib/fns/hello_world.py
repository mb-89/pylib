from pylib.lib.fns import getCLI
#part_of_template

cli = getCLI()
Tp,tp,ta,to,ant = cli.getTyperShortcuts()

@cli.cmd
def hello_world(
):
    """Print hello world. Minimal example of a command."""
    print("Hello world!")