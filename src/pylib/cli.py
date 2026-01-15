from pylib.lib.fns import getCLIclass
from pathlib import Path


name = "pylib"
URL = "https://<URL>/pylib"
examples = "doc"


clic = getCLIclass()
tp = clic.tp
ta = clic.ta
to = clic.to
ant = clic.ant
Tp = clic.Tp

from pylib.lib.fns import getlogger
log = getlogger()


class CLI(clic):
    def __init__(self):
        super().__init__(name, URL, examples, rootdir_path=Path(__file__) / "..")

        self.addCmd(self.create_package)
        self.addCmd(self.inject_lib)
        self.addCmd(self.extract_lib)

    def create_package(
        self,
        dst: ant[Path, ta(help="Path where the new package shall be created")],
        name: ant[str, ta(help="Name of the new package")],
        imp: ant[bool, to("-imp", help="import from pylib instead of inject.")] = False,
        force: ant[bool, to("-f", help="pass to skip confirmations")] = False,
        run: ant[bool, to("-r", help="run the package via uv after creation")] = False,
    ):
        """Create a package that contains all the boilerplate provided by pylib.

        By default, this function injects a copy of pylib into the package.
        Pass the -imp flag to import instead.
        """

        dstdir = dst / name
        if not force:
            overwrite = Tp.confirm(
                f"creating package @ {dstdir}, overriding contents. ok?"
            )
            if not overwrite:
                raise Tp.Abort()

        from pylib import api

        api.create_package(dstdir, imp, run)
        if not run:
            log.info(f"created package @ {dst / name}.")
        else:
            log.info(f"created package @ {dst / name}. Running it in separate process.")

    def inject_lib(
        self,
        dst: ant[Path, ta(help="Path to inject into.")],
        force: ant[bool, to("-f", help="pass to skip confirmations")] = False,
    ):
        """Injects the pylib code into the given path."""

        if not force:
            overwrite = Tp.confirm(
                f"integrating lib into @ {dst}, overriding contents. ok?"
            )
            if not overwrite:
                raise Tp.Abort()

        from pylib import api

        api.inject_lib(dst)

        log.info(f"injected lib @ {dst}.")

    def extract_lib(
        self,
        src: ant[Path, ta(help="Path to extract from.")],
        dst: ant[Path, ta(help="Path to extract into.")] = (
            Path(__file__) / ".." / "lib"
        ).resolve(),
        force: ant[bool, to("-f", help="pass to skip confirmations")] = False,
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


if __name__ == "__main__":
    run()
