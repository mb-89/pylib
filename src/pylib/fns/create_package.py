from pathlib import Path
import shutil
import subprocess
import sys


def create_package(dstdir: Path, imp: bool, run: bool = False):
    if dstdir.is_dir():
        shutil.rmtree(dstdir)
    dstdir.mkdir(parents=True, exist_ok=True)
    dst = dstdir.parent
    name = dstdir.stem

    # set up baseline using uv
    cmd = [sys.executable, "-m", "uv", "init", name, "--package"]
    subprocess.run(cmd, cwd=dst)

    # copy packagetemplate
    tplsrc = Path(__file__) / ".." / ".." / "packagetemplate"
    shutil.copytree(tplsrc, dstdir, dirs_exist_ok=True)

    # remove default
    shutil.rmtree(dstdir / "src" / name)

    ignorelist = ["__pycache__", r"\."]
    # replace $PKG$
    for x in dstdir.rglob("*"):
        if any(y in str(x) for y in ignorelist):
            continue
        if x.is_file():
            data = open(x, "r", encoding="utf-8").read()
            if "$PKG$" in data:
                data = data.replace("$PKG$", name)
                open(x, "w", encoding="utf-8").write(data)
        if "$PKG$" not in x.stem:
            continue
        x.rename(x.with_stem(x.stem.replace("$PKG$", name)))

    from . import inject_lib as il

    il.inject_lib(dstdir, imp)

    # test once using uv (displaying -x)
    if run:
        cmd = ["cmd.exe", "/c", "start", "", "py", "-m", "uv", "run", name, "-x"]

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
