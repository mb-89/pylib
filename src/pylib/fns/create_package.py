from pathlib import Path
import shutil
import subprocess
import sys
import re

from pylib.lib.fns import getlogger, getCLI
from pylib.lib.tools import run_detached

log = getlogger()
cli = getCLI()
Tp,tp,ta,to,ant = cli.getTyperShortcuts()

@cli.cmd
def create_package(        
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

    from . import inject_lib as il

    create_boilerplate_code(dstdir)
    il.inject_lib(dstdir, imp=imp, force=True)
    replace_default_references(dstdir,name)
    dst_package_self_prune(dstdir, name)

    if run:
        log.info(f"created package @ {dst / name}. Running it in separate process.")
        cmd = ["cmd.exe", "/c", "start", "", "py", "-m", "uv", "run", name]
        run_detached(cmd,dstdir)
    else:
        log.info(f"created package @ {dst / name}.")

def dst_package_self_prune(dstdir, name):
    cmd = [sys.executable, "-m", "uv", "run", name, "history", "-c"] #clear history (in case there is an old install)
    subprocess.run(cmd, cwd=dstdir)   
    cmd = [sys.executable, "-m", "uv", "run", name, "dev", "mkdoc"] #create docu
    subprocess.run(cmd, cwd=dstdir)    

def create_boilerplate_code(dstdir:Path):
    if dstdir.is_dir():
        shutil.rmtree(dstdir)
    dstdir.mkdir(parents=True, exist_ok=True)
    dst = dstdir.parent
    name = dstdir.stem

    # set up baseline using uv
    cmd = [sys.executable, "-m", "uv", "init", name, "--package"]
    subprocess.run(cmd, cwd=dst)

    #copy stuff from self to dst
    src_root = (Path(__file__) / ".." / ".."/ ".." / ".." ).resolve()
    dst_root = dst / name

    paths = [src_root / x for x in ("Readme.md", "pyproject.toml")]
    searchglobs = [".vscode/**.*", "tests/**.*", "src/pylib/*.*"]

    for x in searchglobs:
        fn = src_root.rglob if "**" in x else src_root.glob
        paths.extend(y for y in fn(x) if "#part_of_template" in open(y,"rb").read().decode("utf-8"))
    
    copiedfiles = []
    for src in paths:
        srcrel = src.relative_to(src_root)
        dst = dst_root / Path(str(srcrel).replace("pylib",name))
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy(src,dst)
        copiedfiles.append(dst)
    
    #walk over all copied files and make content replacements
    for f in copiedfiles:
        data = open(f,"rb").read().decode("utf-8")
        
        if f.suffix == "md" and "# brief" in data:
            for x in re.findall(r"^# brief\s+(.*?)\s+^#",data,re.DOTALL+re.MULTILINE):
                data = data.replace(x,"#TBD")

        data = data.replace("pylib", name)

        open(f,"wb").write(data.encode("utf-8"))



def replace_default_references(dstdir,name):
    ignorelist = ["__pycache__", r"\."]
    # replace $PKG$
    def repl(file):
        if file.is_file():
            data = open(file, "r", encoding="utf-8").read()
            if "$PKG$" in data:
                data = data.replace("$PKG$", name)
                open(file, "w", encoding="utf-8").write(data)
        if "$PKG$" not in file.stem:
            return
        file.rename(file.with_stem(file.stem.replace("$PKG$", name)))

    for x in dstdir.rglob("*"):
        if any(y in str(x) for y in ignorelist):
            continue
        repl(x)

    for x in (dstdir/".vscode").rglob("*"):
        repl(x)