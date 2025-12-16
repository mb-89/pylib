from pathlib import Path


def create_package(dstdir: Path, imp: bool):
    from pylib.fns import create_package as cp

    cp.create_package(dstdir, imp)


def inject_lib(dstdir: Path, name: str):
    from pylib.fns import inject_lib as il

    il.inject_lib(dstdir, name)
