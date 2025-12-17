from $PKG$.lib.cli import CLI as _CLI
from pathlib import Path

name = "$PKG$"
URL = "$TODO$"
examples = "doc"

tp = _CLI.tp
ta = _CLI.ta
to = _CLI.to
ant = _CLI.ant
Tp = _CLI.Tp


class CLI(_CLI):
    def __init__(self):
        super().__init__(name, URL, examples,rootdir_path=Path(__file__)/ "..")

        self.addCmd(self.echo)

    def echo(self):
        """Echo sys.argv."""
        import sys

        print(sys.argv)


def run(args=None):
    """Run the given arguments.

    This is equivalent to running commands via the shell, but easier to integrate in python code.
    For example:
    uv run <module_name> <function_name> -h
    in the shell equals
    run(["<function-name>","-h"])
    in the module cli. Note that "_" needs to replaced with "-" there.

    """
    CLI().run(args)


if __name__ == "__main__":
    run()
