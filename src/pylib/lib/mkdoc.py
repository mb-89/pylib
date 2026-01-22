"""Functions used to generate documentation"""
from pylib.lib.fns import getlogger
import subprocess
import sys
import re
from pathlib import Path

log = getlogger()


def mk(modname, dst):
    """Generate all docu for given module into dst."""
    mk_doc_struct(dst)
    mk_setup_doc(modname,dst)
    mk_intro_doc(modname,dst)
    mk_cli_doc(modname,dst)
    mk_mdbook(modname,dst)
    mk_readme(modname,dst)



def mk_doc_struct(dst:Path):
    (dst / "000_specs").mkdir(exist_ok=True,parents=True)
    (dst / "100_interactive_doc").mkdir(exist_ok=True)
    (dst / "900_dev").mkdir(exist_ok=True)
    

def mk_intro_doc(modname,dst):
    dst = dst / "000_specs" / "000_motivation.md"
    if dst.is_file():
        return
    open(dst, "wb").write(("# Motivation\n#TBD").encode("utf-8"))
    log.info(f"written motivation -> {dst}.")    

def mk_setup_doc(modname,dst):
    dst = dst / "000_specs" / "001_setup.md"
    open(dst, "wb").write(("#TBD").encode("utf-8"))
    log.info(f"written setup docu -> {dst}.")    

def mk_cli_doc(modname,dst):
    """Generate the cli docu."""
    
    targets = [[modname]]
    results = {}

    while targets:
        target = targets.pop(0)
        if "library-update" in target:
            continue

        res = subprocess.run(
            [sys.executable, "-m", "uv", "run"] + target + ["-h"],
            capture_output=True,
        )
        resstr = res.stdout.decode("utf-8")
        reserr = res.stderr.decode("utf-8")

        Errpatterns = ["+- Error", "┌─  Error","┌─ Error"]
        cmdpatterns = ["+- Commands", "┌─  Commands", "┌─ Commands"]

        for x in Errpatterns:
            if x not in reserr:
                results[" ".join(target)] = resstr
            else:
                continue
        for cmdp in cmdpatterns:
            if cmdp in resstr:
                cmds = resstr.split(cmdp)[-1]
                subcmds = re.findall(r"\r\n(\│|\|)\s(.*?)\s", cmds)
                subcmds = [x for x in subcmds if x[1]]

                if subcmds:
                    log.info(f"found <{target}>...")    
                for sc in subcmds:
                    sc = sc[1]
                    targets.append(target + [sc])

    md = [f"# {modname} commandline interface"]

    for k in sorted(results.keys()):
        v = results[k]
        if not v:
            continue
        lvl = len(k.split()) + 1
        md.append("#" * lvl + f" {k}")
        md.append(f"```\n{v.replace('\r\n', '\n').replace('\n\n', '\n')}\n```")

    if not dst.is_dir():
        log.error(f"dst folder ({dst}) does not exist. Abort.")
        exit(1)
    dst = dst / "000_specs" / "002_cmd.md"
    open(dst, "wb").write(("\n".join(md)).encode("utf-8"))
    log.info(f"written cmdline docu -> {dst}.")

def mk_mdbook(modname, dst):
    try:
        subprocess.run(["mdbook", "-V"], capture_output=True)
    except BaseException:
        log.error(
            "mdbook not found. Install via <winget install --id=Rustlang.mdBook -e>"
        )
        exit(-1)
    dst = dst / "000_specs" / "003_book"
    open(dst, "wb").write(("#TBD").encode("utf-8"))
    log.info(f"written mdbook -> {dst}.")


def mk_readme(modname, dst):
    dst = dst / "README.md"
    open(dst, "wb").write(("#TBD").encode("utf-8"))
    log.info(f"written readme -> {dst}.")