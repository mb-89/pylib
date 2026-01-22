import typer
import importlib.metadata
import sys
from pathlib import Path
from typing_extensions import Annotated as ant
import os
import subprocess
import site
from importlib import reload
import functools
from collections.abc import Callable
from pylib.lib.cli import history, dev

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
            if not history.history_was_called:
                history.history(add=True)

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
        
        history.packagename = packagename
        self.addCmd(history.history)
        self.addCmd(dev.getCMDs(rootdir),parent=self.tp)

    @staticmethod
    def addCmd(cmdfn: Callable | dict, parent = None):
        if parent is None:
            parent  = tp
        if callable(cmdfn):
            tp.command()(cmdfn)
        else:
            # construct command tree
            tree = {}
            for k,v in cmdfn["fns"].items():
                target = tree
                path = k.split("/")
                for p in path[:-1]:
                    target = target.setdefault(p,{})
                target[path[-1]] = v
            for k,v in cmdfn["helps"].items():
                target = tree
                path = k.split("/")
                for p in path:
                    target = target.setdefault(p,{})
                target["_help"] = v

            #walk tree, add cmds and subtypers
            def addsubtyper(parent,key,value):
                if key.startswith("_"):
                    return 
                if isinstance(value, dict): 
                    child = typer.Typer(no_args_is_help=True,help=value.get("_help",""))
                    for ck,cv in value.items():
                        addsubtyper(child,ck,cv)
                    parent.add_typer(child,name=key)
                else:
                    parent.command(key)(value)

            for k,v in tree.items():  
                addsubtyper(parent,k,v)

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