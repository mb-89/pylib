from pylib.lib.cli import CLI as _CLI
from pathlib import Path
import sys

name = "pylib"
URL = "https://code.siemens.com/shs-te-mp-plm-varc/pylib"
examples = "doc"

tp = _CLI.tp
ta = _CLI.ta
to = _CLI.to
ant = _CLI.ant


class CLI(_CLI):
    def __init__(self):
        super().__init__(name, URL, examples)

        self.addCmd(self.create_package)
        self.addCmd(self.inject_lib)
        self.addCmd(self.extract_lib)

    def create_package(
        self,
        dst: ant[Path, ta(help="Path where the new package shall be created")],
        name: ant[str, ta(help="Name of the new package")],
        imp: ant[bool, to("-imp", help="import from pylib instead of inject.")] = False,
    ):
        """Create a package that contains all the boilerplate provided by pylib.

        By default, this function injects a copy of pylib into the package.
        Pass the -imp flag to import instead.
        """

        # TODO

        print(f"created package @ {dst / name}.")
        print(f"use:\n'cd {dst / name}'\n'uv run {name}'\nto run it.")

    def inject_lib(
        self,
        dst: ant[Path, ta(help="Path to inject into.")],
    ):
        """Injects the pylib code into the given path."""

        # TODO
        pass

    def extract_lib(
        self,
        src: ant[Path, ta(help="Path to extract from.")],
        dst: ant[Path, ta(help="Path to extract into.")] = (
            Path(__file__) / ".." / "lib"
        ).resolve(),
    ):
        """Injects the pylib code into the given path."""

        # TODO
        pass


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
