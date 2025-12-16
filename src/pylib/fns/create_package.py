from pathlib import Path
import shutil
import subprocess
import sys
import os


def create_package(dstdir: Path, imp: bool):
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
    # remove default test folder
    shutil.rmtree(dstdir / "src" / name)

    # replace $PKG$
    for x in dstdir.rglob("*"):
        if "__pycache__" in str(x):
            continue
        if x.is_file():
            print(x)
            data = open(x, "r", encoding="utf-8").read()
            if "$PKG$" in data:
                print(x)
                data = data.replace("$PKG$", name)
                open(x, "w", encoding="utf-8").write(data)
        if "$PKG$" not in x.stem:
            continue
        x.rename(x.with_stem(x.stem.replace("$PKG$", name)))

    # integrate lib
    from . import inject_lib as il

    il.inject_lib(dstdir)

    # test once using uv (displaying -x)
    # TODO
