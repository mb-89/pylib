from pathlib import Path


def create_package(dstdir: Path, imp: bool, run: bool = False):
    from pylib.fns import create_package as cp

    cp.create_package(dstdir, imp, run)


def inject_lib(dstdir: Path):
    from pylib.fns import inject_lib as il

    il.inject_lib(dstdir)
