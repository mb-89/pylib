from pathlib import Path
import shutil
import subprocess
import sys

from pylib.lib.fns import getlogger, getCLI

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

    if not force:
        overwrite = Tp.confirm(
            f"creating package @ {dstdir}, overriding contents. ok?"
        )
        if not overwrite:
            raise Tp.Abort()

    dstdir = dst / name
    
    if dstdir.is_dir():
        shutil.rmtree(dstdir)
    dstdir.mkdir(parents=True, exist_ok=True)
    dst = dstdir.parent
    name = dstdir.stem

    # set up baseline using uv
    cmd = [sys.executable, "-m", "uv", "init", name, "--package"]
    subprocess.run(cmd, cwd=dst)

    # copy packagetemplate
    # TODO: remove packagetemplate. reverse-construct from pylib instead.
    tplsrc = Path(__file__) / ".." / ".." / "packagetemplate"
    shutil.copytree(tplsrc, dstdir, dirs_exist_ok=True)

    # remove default
    shutil.rmtree(dstdir / "src" / name)

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

    from . import inject_lib as il

    il.inject_lib(dstdir, imp)

    if run:
        log.info(f"created package @ {dst / name}. Running it in separate process.")
        cmd = ["cmd.exe", "/c", "start", "", "py", "-m", "uv", "run", name]

        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_CONSOLE = 0x00000010
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        flags = CREATE_NEW_CONSOLE

        # works when not debugging. doesnt work when debugging
        subprocess.Popen(
            cmd,
            cwd=dstdir,
            creationflags=flags,
        )
    else:
        log.info(f"created package @ {dst / name}.")