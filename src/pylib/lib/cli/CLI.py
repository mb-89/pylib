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
from importlib import reload
import functools
from collections.abc import Callable

# note: 
# for any imports from pylib:
# do them as late as possible, because the cli might patch it before running!
# (this means: import one line before using it)

ta = typer.Argument
to = typer.Option
tp = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
)
packagename = __package__.split(".")[0]

argbuf_fn = f"{packagename}_argbuf"
hist_len = 20
historic_Flag = False

examplePath = None
rootdir = None
flag_update_lib = False
flag_default = False
flag_default_done = False
cmd_default = None

cli_singleton = None


def cmd(fn):
    @functools.wraps(fn)
    def fnw(*args,**kwargs):
        return fn(*args,**kwargs)
    CLI.addCmd(fn)
    print(f"registered {fn}")
    return fnw

class CLI:
    tp = tp
    ta = ta
    to = to
    ant = ant
    Tp = typer
    cmd = cmd

    @staticmethod
    def getTyperShortcuts():
        return (CLI.Tp, tp, ta, to, ant)

    @staticmethod
    def run(argv=None):
        global cli_singleton
        if cli_singleton is None:
            cli_singleton = CLI()

        if argv is None:
            argv = [x for x in sys.argv[1:]]
        try:
            if "--library-update" in argv:
                library_update_callback()
                argv.remove("--library-update")

            if any(x in argv for x in ["-v", "--version"]):
                version_callback()
            elif any(x in argv for x in ["-x", "--examples"]):
                example_callback()
            else:
                try:
                    if flag_update_lib:
                        cli_singleton.dev_update()
                        from pylib.lib.cli.print import print
                        udl = []
                        for k,v in sys.modules.items():
                            if k.startswith("pylib.lib."):
                                print(f"reloading {k}")
                                udl.append(v)
                        from pylib.lib.fns import getversion
                        print(f"lib version before reload: {getversion()}")
                        del getversion
                        for x in udl:
                            reload(x)
                        from pylib.lib.fns import getversion
                        print(f"lib version after reload: {getversion()}")
                        del getversion

                    cli_singleton.tp(argv)             
                except SystemExit as _:
                    if flag_default: 
                        cli_singleton.default_fn()
                        return     
        finally:
            sys.argv = argv
            if not historic_Flag:
                cli_singleton.history(add=True)

    @staticmethod
    def setparams(name=None,exampledir=None,rootdir_path=None):
        global packagename
        global examplePath
        global rootdir

        if name:
            packagename = name
        if exampledir:
            examplePath = exampledir
        if rootdir_path:
            rootdir=rootdir_path

    @staticmethod
    def setDefaultCmd(cmd:list[str] | Callable):
        global cmd_default
        cmd_default = cmd

    @staticmethod
    def importcmds(fn_dir:Path):
        global cli_singleton
        if cli_singleton is None:
            cli_singleton = CLI()    

        #trivial logic first: check if getCLI is in file
        mods = tuple(x for x in fn_dir.rglob("*.py") if not x.stem.startswith("_") and "getCLI" in open(x,"r").read())
        #now, dynamically import and extract all cmd instances. add these as commands.
        for mod in mods:
            mname = ".".join(mod.resolve().parts[-3:]).replace(".py","")
            spec=importlib.util.spec_from_file_location(mname , mod)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[mname] = module

    def __init__(
        self, name: str = "", example_rel2root=None, rootdir_path=None
    ):
        if rootdir_path is None:
            rootdir_path = (
                Path(__file__) / ".." / ".." / ".."
            )  # TODO make this more portable.
        self.setparams(name=name,exampledir=example_rel2root,rootdir_path=rootdir_path)
        self.rootdir = rootdir
        
        self.addCmd(self.history)
        self._mk_cmd_dev()

    @staticmethod
    def addCmd(cmdfn):
        tp.command()(cmdfn)

    @staticmethod
    def default_fn():
        """
        This function is called when the package runs with no arguments. 
        Defaults to the --examples / -x behavior, but can be overridden by
        calling the "setDefaultCmd" function.
        """
        global flag_default_done
        if flag_default_done:
            return
        flag_default_done=True


        if cmd_default is None:
            example_callback()
        elif callable(cmd_default):
            cmd_default(cli_singleton)
        else:
            CLI.run(cmd_default)

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
        #TODO: rework this thing. doesnt work as intendend. new design: history should 
        #modify sys.argv before tp() gets called
        def pushfn():
            try:
                x = args_hist[n]
                args_hist.remove(x)
            except IndexError:
                return
            args_hist.appendleft(x)
            _set_cached_args(args_hist)
            return

        args_hist = _get_cache_args()
        global historic_Flag
        historic_Flag = True
        if add:
            args = sys.argv
            try:
                args_hist.remove(x)
            except:
                pass
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

        if n != -1:
            try:
                x = args_hist[n]
            except IndexError:
                return
            push = True #always push last cmd to top
            try:
                #print("running")
                self.run(x)
            finally:
                #print("pushing")
                pushfn()
        
        if push:
            pushfn()

        # if we are here, print history
        for idx, x in enumerate(args_hist):
            from pylib.lib.cli.print import print
            print(f"{idx:3d} / {' '.join(x)}")

    def _mk_cmd_dev(self):
        # TODO: add a subcommand feature for addcmd that can be used for this instead.
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
        """update the pylib code used by this package. Pass the hidden --library-update flag to run it automatically."""
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

        from pylib.lib.fns import getlogger
        log = getlogger()
        log.info(f"creating doc for <{modname}>...")

        dst = (Path(__file__) / ".." / ".." / ".." / "doc").resolve()

        from pylib.lib.mkdoc import mk
        mk(modname, dst)


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
    from pylib.lib.cli.print import print
    from pylib.lib.fns import getversion
    print(version)
    print(f"lib: {getversion()}")

def example_callback():
    try:
        p = (rootdir / examplePath).resolve()
    except BaseException:
        p = None

    if p is None:
        pnl = ["", "This module provides no examples. Abort."]
        from pylib.lib.cli.print import panel
        panel("\n".join(pnl), width=80, title="Examples", title_align="left")
        return

    try:
        import jupyterlab
    except ImportError:
        pnl = [
            "",
            "The example browser requires jupyterlab.",
            "If you see this message, jupyterlab was not found.",
            "you can install it by running the 'dev install' subcommand.",
            "",
            "in case you are running this script via uvx, replace",
            "'uvx'",
            "with",
            "'uvx --with jupyterlab'",
            "in the commandline call.",
            "",
            "Opening examples in explorer as backup...",
        ]
        from pylib.lib.cli.print import panel
        panel("\n".join(pnl), width=80, title="Examples", title_align="left")
        os.startfile(p)

    pnl = ["", "starting jupyter lab.", "press ctrl+c to abort."]
    from pylib.lib.cli.print import panel
    panel("\n".join(pnl), width=80, title="Jupyter lab", title_align="left")

    ju = Path(site.getsitepackages()[0]) / "Scripts" / "jupyter"
    index_path = p / "README.md"
    cmd = [
        f"{ju.resolve()}",
        "lab",
        str(index_path).replace("\\", "/"),
    ]
    subprocess.run(cmd)

def library_update_callback():
    global flag_update_lib
    flag_update_lib = True

def default_callback():
    global flag_default
    flag_default = True

def noop():
    pass


@tp.callback(invoke_without_command=True)
def cb(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=noop,
        is_eager=True,
        help="Show the version of this script",
    ),
    examples: bool = typer.Option(
        None,
        "--examples",
        "-x",
        callback=noop,
        is_eager=True,
        help="Shows examples",
    ),
    library_update: bool = typer.Option(
        None,
        "--library-update",
        callback=noop,
        is_eager=True,
        hidden = True,
        help="pass to update internal pylib before running commands",
    ),
):
    if len(sys.argv) == 1:
        default_callback()
    if len(sys.argv) == 3 and sys.argv[-2] == "history":
        try:
            default =  not bool(_get_cache_args()[int(sys.argv[-1])])
        except BaseException:
            default = False
        if default:   
            default_callback()