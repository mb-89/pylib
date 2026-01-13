import typer
import importlib.metadata
import sys
from pathlib import Path
import json
import tempfile
from collections import deque
from typing_extensions import Annotated as ant
import os
import subprocess
import site
from pylib.lib.cli.print import print, panel
from pylib.lib.log import getlogger
import re

log = getlogger()

ta = typer.Argument
to = typer.Option
tp = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
cmd = tp.command
packagename = __package__.split(".")[0]
packageurl = "<??>"

argbuf_fn = f"{packagename}_argbuf"
hist_len = 20
historic_Flag = False

examplePath = None
rootdir = None


class CLI:
    tp = tp
    ta = ta
    to = to
    ant = ant
    Tp = typer

    def __init__(
        self, name: str = "", url: str = "", example_rel2root=None, rootdir_path=None
    ):
        global tp
        global packagename
        global packageurl
        global examplePath
        global rootdir

        if rootdir_path is None:
            rootdir_path = (
                Path(__file__) / ".." / ".." / ".."
            )  # TODO make this more portable.
        rootdir = rootdir_path
        self.rootdir = rootdir
        examplePath = example_rel2root
        if name:
            packagename = name
        if url:
            packageurl = url
        self.addCmd(self.history)
        self._mk_cmd_dev()

    def addCmd(self, cmdfn):
        cmd()(cmdfn)

    def run(self, argv=None):
        if argv is None:
            argv = [x for x in sys.argv[1:]]
        try:
            if any(x in argv for x in ["-v", "--version"]):
                version_callback()
            elif any(x in argv for x in ["-i", "--install-help"]):
                install_callback()
            elif any(x in argv for x in ["-x", "--examples"]):
                example_callback()
            else:
                try:
                    self.tp(argv)
                except SystemExit as _:
                    pass
        finally:
            sys.argv = argv
            if not historic_Flag:
                self.history(add=True)

    def history(
        self,
        n: ant[int, ta(help="selected history entry")] = -1,
        push: ant[
            bool, to("-p", "--push", help="push the selected entry to the top")
        ] = False,
        clear: ant[
            bool, to("-c", "--clear", help="clear (if n not provided, clear all)")
        ] = False,
        add: ant[
            bool,
            to("-a", "--add", help="add current sys.argv to hist. used internally"),
        ] = False,
    ):
        """Recall cli history (mainly used for debugging)."""
        args_hist = _get_cache_args()
        global historic_Flag
        historic_Flag = True
        if add:
            args = sys.argv
            if args not in args_hist:
                args_hist.appendleft(args)
                _set_cached_args(args_hist)
            return

        if clear:
            if n != -1:
                try:
                    args_hist.remove(args_hist[n])
                    x = args_hist
                except IndexError:
                    return
            else:
                x = []
            _set_cached_args(x)
            return

        if push:
            try:
                x = args_hist[n]
                args_hist.remove(x)
            except IndexError:
                return
            args_hist.appendleft(x)
            _set_cached_args(args_hist)
            return

        if n != -1:
            try:
                x = args_hist[n]
            except IndexError:
                return
            self.run(x)
            return

        # if we are here, print history
        for idx, x in enumerate(args_hist):
            print(f"{idx:3d} / {' '.join(x)}")

    def _mk_cmd_dev(self):
        stp = typer.Typer(
            help="contains development subcommands",
            no_args_is_help=True,
        )
        scmd = stp.command
        scmd("setup")(self.dev_install)
        scmd("test")(self.dev_test)
        scmd("lint")(self.dev_lint)
        scmd("lib_update")(self.dev_update)
        scmd("mkdoc")(self.dev_mkdoc)

        self.tp.add_typer(stp, name="dev")

    def dev_install(self):
        """Install development dependencies. Assumes a local git repo. Will not work with uvx."""
        subprocess.call(["uv", "sync", "--group", "dev"], cwd=rootdir)

    def dev_test(
        self,
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

    def dev_lint(self):
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

    def dev_update(self):
        """update the pylib code used by this package."""
        libdir = Path(__file__) / ".." / ".."
        src = libdir / "src.json"
        if not src.is_file():
            pass  # TODO: what do we do here?
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

    def dev_mkdoc(self):
        """create the documentation for the package."""
        import click

        parent = click.get_current_context(silent=True).parent
        while parent.parent is not None:
            parent = parent.parent
        modname = parent.info_name.split()[-1]

        log.info(f"creating doc for <{modname}>...")

        targets = [[modname]]
        results = {}
        while targets:
            target = targets.pop(0)

            res = subprocess.run(
                [sys.executable, "-m", "uv", "run"] + target + ["-h"],
                capture_output=True,
            )
            resstr = res.stdout.decode("utf-8")
            reserr = res.stderr.decode("utf-8")

            Errpatterns = ["+- Error", "┌─  Error"]
            cmdpatterns = ["+- Commands", "┌─  Commands"]

            for x in Errpatterns:
                if x not in reserr:
                    results[" ".join(target)] = resstr
                    log.info(f"found <{target}>...")
                else:
                    continue
            for cmdp in cmdpatterns:
                if cmdp in resstr:
                    cmds = resstr.split(cmdp)[-1]
                    subcmds = re.findall(r"\r\n\|\s+(.*?)\s", cmds)
                    for sc in subcmds:
                        targets.append(target + [sc])

        md = [f"# {modname} commandline interface"]

        for k in sorted(results.keys()):
            v = results[k]
            lvl = len(k.split()) + 1
            md.append("#" * lvl + f" {k}")
            md.append(f"```\n{v.replace('\r\n', '\n').replace('\n\n', '\n')}\n```")

        dst = (Path(__file__) / ".." / ".." / ".." / "doc").resolve()

        if not dst.is_dir():
            log.error(f"dst folder ({dst}) does not exist. Abort.")
            exit(1)
        dst = dst / "001_cmd.md"
        open(dst, "wb").write(("\n".join(md)).encode("utf-8"))
        log.info(f"written cmdline docu -> {dst}.")

        try:
            subprocess.run(["mdbook", "-V"], capture_output=True)
        except BaseException:
            log.error(
                "mdbook not found. Install via <winget install --id=Rustlang.mdBook -e>"
            )
            exit(-1)


def _get_cache_args() -> deque:
    """Return the last cached cli calls."""
    path = Path(tempfile.gettempdir()) / argbuf_fn
    dq = deque(maxlen=hist_len)
    if not path.is_file():  # pragma: no cover
        return dq
    lst = json.loads(open(path, "r").read())
    for x in lst:
        dq.append(x)
    return dq


def _set_cached_args(args_dq: deque):
    """Cache this cli call."""
    path = Path(tempfile.gettempdir()) / argbuf_fn

    open(path, "w").write(json.dumps(list(args_dq)))


def version_callback():
    version = importlib.metadata.version(packagename)
    print(version)


def install_callback():
    txt = [
        "",
        "There are multiple ways to install this script on your local machine:",
        "",
        "To install and run it it as an os-wide tool:",
        f"uv tool install git+{packageurl} {packagename}",
        f"uvx {packagename} # or only '{packagename}'",
        "",
        "To clone the code and work on it locally:",
        f"git clone git+{packageurl}",
        f"cd {packagename}",
        f"uv run {packagename}",
        "",
        "Some subfunctions might require more setup. These functions will prompt for it on first use.",
        "For example, run 'uv run $PKG$ dev install' to install dev dependencies.",
        "",
        "See uv docu (https://docs.astral.sh/uv/guides) for further options"
        " like running specific versions, branches, updating installations, etc...",
    ]
    panel(
        "\n".join(txt),
        title="Installing this script locally",
        title_align="left",
        width=80,
    )


def example_callback():
    try:
        p = (rootdir / examplePath).resolve()
    except BaseException:
        p = None

    if p is None:
        pnl = ["", "This module provides no examples. Abort."]
        panel("\n".join(pnl), width=80, title="Examples", title_align="left")
        return

    try:
        import jupyterlab
    except ImportError:
        pnl = [
            "",
            "The example browser requires jupyterlab.",
            "If you see this message, jupyterlab was not found.",
            "you can install it by running uv $PKG$ dev install",
            "",
            "in case you are running this script via uvx, replace",
            "'uvx'",
            "with",
            "'uvx --with jupyterlab'",
            "in the commandline call.",
            "",
            "Opening examples in explorer as backup...",
        ]

        panel("\n".join(pnl), width=80, title="Examples", title_align="left")
        os.startfile(p)

    pnl = ["", "starting jupyter lab.", "press ctrl+c to abort."]
    panel("\n".join(pnl), width=80, title="Jupyter lab", title_align="left")

    ju = Path(site.getsitepackages()[0]) / "Scripts" / "jupyter"
    index_path = p / "000_index.md"
    cmd = [
        f"{ju.resolve()}",
        "lab",
        str(index_path).replace("\\", "/"),
    ]
    subprocess.run(cmd)


def noop():
    pass


@tp.callback()
def cb(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=noop,
        is_eager=True,
        help="Show the version of this script",
    ),
    install: bool = typer.Option(
        None,
        "--install-help",
        "-i",
        callback=noop,
        is_eager=True,
        help="Show help on local installation",
    ),
    examples: bool = typer.Option(
        None,
        "--examples",
        "-x",
        callback=noop,
        is_eager=True,
        help="Shows examples",
    ),
):
    pass
