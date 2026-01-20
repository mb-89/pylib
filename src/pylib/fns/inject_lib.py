from pathlib import Path
import shutil
import os
import re
import sys
import subprocess
import json
from pylib.lib.fns import getlogger, getCLI

log = getlogger()
cli = getCLI()
Tp,tp,ta,to,ant = cli.getTyperShortcuts()

@cli.cmd
def inject_lib(
        dst: ant[Path, ta(help="Path to inject into.")],
        force: ant[bool, to("-f", help="pass to skip confirmations")] = False,
        imp: ant[bool, to("-f", help="hidden flag, pass to import instead inject",hidden=True)] = False):

    """Injects the pylib code into the given path."""

    if not force:
        overwrite = Tp.confirm(
            f"integrating lib into @ {dst}, overriding contents. ok?"
        )
        if not overwrite:
            raise Tp.Abort()

    dstdir = dst
    log.info(f"injecting lib @ {dstdir}.")
    ignorelist = ["__pycache__", r"\."]
    name = dstdir.stem

    # check if the source is editable. if so, we are a local import
    cmd = [sys.executable, "-m", "uv", "pip", "show", "pylib"]
    fnd = subprocess.run(cmd, capture_output=True).stdout.decode("utf-8")
    epl = "Editable project location"
    if epl in fnd:
        epl = re.findall(f"{epl}:(.*?)\n", fnd)[0].strip()
    else:
        epl = None

    libsrc = Path(__file__) / ".." / ".." / "lib"
    libdst = dstdir / "src" / name / "lib"

    if imp:  # we import, no copying -------------------------------
        if epl is not None:
            cmd = [
                sys.executable,
                "-m",
                "uv",
                "add",
                "--editable",
                epl.replace("\\", "/"),
            ]
            subprocess.run(cmd, cwd=dstdir)
            for x in dstdir.rglob("*"):
                if any(y in str(x) for y in ignorelist):
                    continue
                if x.is_file():
                    data = open(x, "r", encoding="utf-8").read()
                    pat = f"{name}.lib."
                    if pat in data:
                        #print(x)
                        data = data.replace(pat, "pylib.lib.")
                        open(x, "w", encoding="utf-8").write(data)

    else:  # we copy/inject --------------------------------------------
        shutil.copytree(
            libsrc,
            libdst,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(*["__pycache__", ".ipynb_checkpoints"]),
        )

        # replace $PKG$ etc
        from pylib.lib.fns import getversion
        libversion = getversion()
        for x in dstdir.rglob("*"):
            if any(y in str(x) for y in ignorelist):
                continue
            if x.is_file():
                # print(x)
                data = open(x, "r", encoding="utf-8").read()
                if "$PKG$" in data:
                    # print(x)
                    data = data.replace("$PKG$", name)
                    open(x, "w", encoding="utf-8").write(data)
                if "from pylib.lib." in data:
                    # print(x)
                    data = data.replace("pylib.lib.", f"{name}.lib.")
                    open(x, "w", encoding="utf-8").write(data)
                if "$INJECTED_VERSION" in data:
                    data = data.replace("$INJECTED_VERSION", libversion)
                    open(x, "w", encoding="utf-8").write(data)                    
            if "$PKG$" not in x.stem:
                continue
            x.rename(x.with_stem(x.stem.replace("$PKG$", name)))

        # in this case, also store a ref to the source so we can update later.
        # in case of an import, we can easily update via uv.
        # in case of an injection, we need to do it ourselves.
        cmd = [
            sys.executable,
            "-m",
            "uv",
            "add",
            "uv",
        ]  # add uv, so we can update later
        subprocess.run(cmd, cwd=dstdir)
        if epl is None:
            pass  # TODO (how do we re-inject from a remote src?)
        else:
            open(libdst / "src.json", "w").write(
                json.dumps({"type": "editable", "path": epl})
            )

    try:
        os.symlink(dstdir / "src" / name / "doc" / "800_lib_docu", libdst / "doc")
    except WindowsError:
        log.warning(
            "symlink to lib docu couldnt be created. try running as admin. This only influences the documentation."
        )
