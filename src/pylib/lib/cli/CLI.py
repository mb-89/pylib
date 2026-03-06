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
cmd_default = None
fnpaths = []
flags = {}
unregistered_flags = {}

cli_singleton = None
def get_cli_singleton():
    global cli_singleton
    if cli_singleton is None:
        cli_singleton = CLI()

    return cli_singleton

def cmd(fn):
    @functools.wraps(fn)
    def fnw(*args,**kwargs):
        return fn(*args,**kwargs)
    CLI.addCmd(fn)
    return fnw

class CLI_Flag():
    def __init__(self,name,help="",type=None,default=None):
        self.name = name
        self.help = help
        self.type = type
        self.default = None
        self.val = None
        self._valSet = False

    def __str__(self):
        info = [self.name, self.help.replace("\n", " "), self.type.__name__ if self.type else "", str(self.default) if self.default else ""]
        info = [x for x in info if x]
        return " / ".join(info)

    def setVal(self, val):

        if self.type:
            tp = getattr(__builtins__,self.type,None)
            if tp is None:
                tp = globals().get(tp,None)
            if tp is not None:
                try:
                    val = tp(val)
                except BaseException:
                    pass

        self.val = val
        self._valSet =True

    def getVal(self):
        if self._valSet:
            return self.val
        else:
            return self.default


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
        cli_singleton = get_cli_singleton()
        if argv:
            sys.argv = ["api"] + argv
        elif argv is None:
            argv = sys.argv

        done,argv = preprocess_sys_argv()
        if not done:
            for p in fnpaths:
                cli_singleton.importcmds(p)      

            if len(argv) == 1: #default if empty
                cli_singleton.default_fn()
            else:
                cli_singleton.tp(argv[1:])  

    @staticmethod
    def addFlag(flagname, help = "", type=None, default=None):
        global flags
        flagname = flagname.lower()
        flags[flagname] = CLI_Flag(flagname,help,type,default)

    def getFlag(flagname:str="", default = None):
        flagname = flagname.lower()
        if not flagname:
            dct = {}
            for k,v in flags.items():
                dct[k] = v.getVal()
            unknowns = {}
            dct["_"] = unknowns
            for k,v in unregistered_flags.items():
                unknowns[k] = v.getVal()
            return dct
        if flagname in flags:
            return flags[flagname].getVal()
        if flagname in unregistered_flags:
            return unregistered_flags[flagname].getVal()
        return default


    @staticmethod
    def setparams(name=None,exampledir=None,rootdir_path=None,fndirs= None):
        global packagename
        global examplePath
        global rootdir
        global fnpaths

        if name:
            packagename = name
        if exampledir:
            examplePath = exampledir
        if rootdir_path:
            rootdir=rootdir_path
        if fndirs:
            fnpaths = fndirs

    @staticmethod
    def setDefaultCmd(cmd:list[str] | Callable):
        global cmd_default
        cmd_default = cmd

    @staticmethod
    def importcmds(fn_dir:Path):

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
        Defaults to the --docu behavior, but can be overridden by
        calling the "setDefaultCmd" function.
        """
        global cmd_default
        if cmd_default is None:
            CLI.run(["tui"])
        elif callable(cmd_default):
            cmd_default(cli_singleton)
        else:
            CLI.run(cmd_default)

def print_version():
    version = importlib.metadata.version(packagename)
    from pylib.lib.cli.print import print
    from pylib.lib.fns import getversion
    print(version)
    print(f"lib: {getversion()}")

def show_docu():
    try:
        p = (rootdir / examplePath).resolve()
    except BaseException:
        p = None

    if p is None:
        pnl = ["", "This module provides no docu. Abort."]
        from pylib.lib.cli.print import panel
        panel("\n".join(pnl), width=80, title="docu", title_align="left")
        return

    ju_found = subprocess.run(["where", "jupyter"], capture_output=True).returncode == 0

    if not ju_found:
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
            "Opening docu in explorer as backup...",
        ]
        from pylib.lib.cli.print import panel
        panel("\n".join(pnl), width=80, title="Docu", title_align="left")
        os.startfile(p)
        return

    pnl = ["", "starting jupyter lab.", "This may take a moment.", "press ctrl+c to abort."]
    from pylib.lib.cli.print import panel
    panel("\n".join(pnl), width=80, title="Jupyter lab", title_align="left")

    ju = Path(site.getsitepackages()[0]) / "Scripts" / "jupyter"
    index_path = p / "README.md"
    cmd = [
        f"{ju.resolve()}",
        "lab",
        str(index_path).replace("\\", "/"),
    ]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

def library_update():
    from pylib.lib.fns import getversion
    print(f"lib version before reload: {getversion()}")

    dev.update()

    #we need to save some globals
    global packagename
    global examplePath
    global rootdir
    global fnpaths
    global cmd_default
    global flags

    buf_packagename = packagename
    buf_examplePath = examplePath
    buf_rootdir = rootdir
    buf_fnpaths = fnpaths
    buf_cmd_default = cmd_default
    buf_flags = flags


    udl = []
    for k,v in sys.modules.items():
        if k.startswith("pylib.lib."):
            print(f"reloading {k}")
            udl.append(v)
    for x in udl:
        reload(x)     

    from pylib.lib.fns import getversion
    packagename = buf_packagename
    examplePath = buf_examplePath
    rootdir = buf_rootdir
    fnpaths = buf_fnpaths
    cmd_default = buf_cmd_default
    flags = buf_flags

    print(f"lib version after reload: {getversion()}")   

def print_flag_help():
    global flags
    if not flags:
        return
    from pylib.lib.cli.print import print
    print("Registered commandline flags:")
    for x in sorted(flags.keys()):
        print("-- " + str(flags[x]))


def preprocess_sys_argv():
    done = False
    argv = sys.argv

    #if help is requested, abort and pass to typer.
    if "-h" in argv or "--help" in argv:
        if "--flag" in argv:
            print_flag_help()
            done=True
        return done, argv
    
    #call history
    argv_mod = history.history(stub=False)
    if argv_mod is None:
        done = True
    else:
        argv = argv_mod

    if not done: #update lib, if prompted, before executing rest
        if "--library-update" in argv:
            argv.remove("--library-update")    
            library_update()

    #display version, if prompted
    if not done:
        if "-v" in argv or "--version" in argv:
            print_version()
            done = True

    #display docu, if prompted
    if not done:
        if"--docu" in argv:
            show_docu()
            done = True

    return done, argv

def noop():
    pass

def process_flag_vals(flagvals):
    global flags
    global unregistered_flags
    for val in flagvals:
        if "=" in val:
            name,val = (x.strip() for x in val.split("="))
        else:
            name = val
            val = True
        name = name.lower()
        if name in flags:
            flags[name].setVal(val)
        else:
            f = CLI_Flag(name)
            f.setVal(val)
            unregistered_flags[name] = f


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
    docu: bool = typer.Option(
        None,
        "--docu",
        callback=noop,
        is_eager=True,
        help="Show docu",
    ),
    library_update: bool = typer.Option(
        None,
        "--library-update",
        callback=noop,
        is_eager=True,
        hidden = True,
        help="pass to update internal pylib before running commands",
    ),
    flag: ant[list[str],typer.Option(help="Flag(s) that are available in code via lib.getFlags(). See --flag --help for list of availables. Pass multiple times for multiple flags.")] = []
):
    process_flag_vals(flag)