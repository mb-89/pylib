import subprocess
import typer
from typing_extensions import Annotated as ant
from pathlib import Path
import sys
import json

rootdir = None
ta = typer.Argument
to = typer.Option

def getCMDs(rootdir_in):
    global rootdir
    rootdir=rootdir_in
    fndct = {}
    helpdct = {}

    helpdct = {"dev": "contains development subcommands"}
    fndct["dev/install"] = install
    fndct["dev/test"] = test
    fndct["dev/lint"] = lint
    fndct["dev/update"] = update
    fndct["dev/mkdoc"] = mkdoc

    return {"fns": fndct, "helps": helpdct}


def install():
    """Install development dependencies. Assumes a local git repo. Will not work with uvx."""
    subprocess.call(["uv", "sync", "--group", "dev"], cwd=rootdir)

def test(
    filt: ant[str, to("-f", "--filt", help="filter by test name")] = "",
    mark: ant[
        str,
        to(
            "-m",
            "--mark",
            help="filter by marker name. See pyproject.toml for avail. markers.",
        ),
    ] = "",
):
    """Run common test commands. Collection of useful tests, can also be done via pytest."""
    rd = (rootdir / ".." / "..").resolve()
    docdir = Path(__file__) / ".." / ".." / "doc"
    cmd = [Path(sys.executable) / ".." / "py.test", str(docdir).replace("\\", "/")]
    if filt:
        cmd.extend(["-k", filt])
    if mark:
        cmd.extend(["-m", mark])
    subprocess.call(cmd, cwd=rd)

def lint():
    """Run common linter commands. Collection of useful lints, can also be done via ruff."""
    rd = (rootdir / ".." / "..").resolve()
    subprocess.call(
        [
            Path(sys.executable) / ".." / "ruff",
            "check",
            "--output-format=concise",
            "--ignore-noqa",
        ],
        cwd=rd,
    )

def update():
    """update the pylib code used by this package. Pass the hidden --library-update flag to run it automatically."""
    libdir = Path(__file__) / ".." / ".."
    src = libdir / "src.json"
    if not src.is_file():
        pass  # this is for example the case for pylib itself. do nothing for now.
    else:
        srcdata = json.loads(open(src, "r").read())
        if srcdata["type"] == "editable":
            dstdir = libdir / ".." / ".." / ".."
            dstdir = dstdir.resolve()
            cmd = [
                sys.executable,
                "-m",
                "uv",
                "run",
                "pylib",
                "inject-lib",
                str(dstdir).replace("\\", "/"),
                "-f",
            ]

            subprocess.call(cmd, cwd=srcdata["path"])

def mkdoc():
    """create the documentation for the package."""
    import click

    parent = click.get_current_context(silent=True).parent
    while parent.parent is not None:
        parent = parent.parent
    modname = parent.info_name.split()[-1]

    from pylib.lib.fns import getlogger
    log = getlogger()
    log.info(f"creating doc for <{modname}>...")

    dst = (Path(__file__) / ".." / ".." / ".." / "doc").resolve()

    from pylib.lib.mkdoc import mk
    mk(modname, dst)
