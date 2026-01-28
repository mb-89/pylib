"""Functions used to generate documentation"""
from pylib.lib.fns import getlogger
from pylib.lib.tools import mk_win_link
import subprocess
import sys
import re
from pathlib import Path
import shutil
import os

log = getlogger()
bookdirname="700_book"

def mk(modname, dst):
    """Generate all docu for given module into dst."""
    mk_doc_struct(dst)
    mk_setup_doc(modname,dst)
    mk_intro_doc(modname,dst)
    mk_cli_doc(modname,dst)
    mk_readme(modname,dst)
    mk_mdbook(modname,dst)

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
            "mdbook not found. Install via"
            "winget install Rustlang.Rustup"
            "cargo install mdbook"
        )
        exit(-1)
    mdbook_found = subprocess.run(["where", "mdbook-pdf"], capture_output=True).returncode == 0
    if not mdbook_found:
        log.warning(
            "mdbook-pdf not found. No pdf book will be generated.\n" \
            "Install via\n"
            "winget install Rustlang.Rustup"
            "cargo install mdbook-pdf"
        )
    root = dst
    dst = dst / bookdirname
    shutil.rmtree(dst,ignore_errors=True)
    cmd = ["mdbook", "init", dst.resolve(), "--force", "--title", modname]
    subprocess.run(cmd, capture_output=True)
    
    #modify build cfg
    toml = open(dst/"book.toml","rb").read().decode("utf-8")
    toml +=('\n[build]\nbuild-dir= "dist"')
    toml +=('\n[output.html]\n\n')
    toml +=('\n[output.pdf]\n\n')
    open(dst/"book.toml","w").write(toml)

    #copy and convert files
    nb_mds = convertnbs(root)
    createMd(root,dst)

    #cleanup
    for x in nb_mds: x.unlink()
    
    shutil.rmtree(dst/"book",ignore_errors=True)
    cmd = ["mdbook", "build", dst.resolve()]
    _ = subprocess.run(cmd, capture_output=True)    
    
    mk_win_link("book_html", dst/"dist"/"html"/"index.html",dst=dst)
    if mdbook_found:
        mk_win_link("book_pdf", dst/"dist"/"pdf"/"output.pdf",dst=dst)
    log.info(f"written mdbook -> {dst}.")


def mk_readme(modname, dst):
    dst = dst / "README.md"
    open(dst, "wb").write(("#TBD").encode("utf-8"))
    log.info(f"written readme -> {dst}.")

def convertnbs(root:Path)->list[Path]:
    exe_found = subprocess.run(["where", "jupyter"], capture_output=True).returncode == 0
    if not exe_found:
        log.warning(
            "jupyter not found. Notebooks will not be added to doc.\n" \
            "Install via\n"
            "uv add jupyter"
        )
        return []
    glob = root.rglob("**.ipynb")
    glob = [x for x in glob if not any(y.startswith(".") for y in x.parts)]
    cmd = ["jupyter", "nbocnvert", "--to=markdown"]
    cmd.extend([str(x.resolve()) for x in glob])
    subprocess.run(cmd, capture_output=True)   
    return [x.with_suffix(".md") for x in glob]

def createMd(root, dst):
    mddst = dst / "src" / "Summary.md"
    dct = {}

    special_case_mapping = {
        "README": ("Introduction", dct)
    }
    srcdir = dst / "src"
    files = root.rglob("*.md")
    for f in files:
        stem = f.stem
        sstem = stem.split("_")
        relpath = f.relative_to(root)
        try: 
            number = int(sstem[0])
        except BaseException:
            number = -10
        target = dct
        lvl = 0
        if any(x.startswith(".") or x.startswith("_") for x in relpath.parts):
            continue
        if bookdirname in relpath.parts:
            continue
        title = stem
        for x in relpath.parts[:-1]:
            lvl += 1
            spart = x.split("_")
            ptitle = "_".join(spart[1:])
            try:
                pno = int(ptitle[0])
            except BaseException:
                pno = -1
            target = dct.setdefault((pno,ptitle),{})
            if number >=0:
                title = "_".join(sstem[1:])
        title,target = special_case_mapping.get(title,(title,target))
        target[(number,title)] = (relpath,lvl)

    def addcontent(parent, dst):
        for k in sorted(parent.keys(),key=lambda x:x[0]):
            child = parent[k]
            if isinstance(child,dict):
                line = f"\n# {k[1]}\n"
                dst.append(line)
                addcontent(child,dst)
            else:
                file,lvl = child
                srcf = root / file
                dstflnk = "_".join(file.parts)
                dstf = srcdir / dstflnk
                shutil.copy(srcf,dstf)
                pref = "" if lvl == 0 else (""*lvl+" - ")
                line = f"{pref}[{k[1]}](./{dstflnk})"
                dst.append(line)

    mdlst = ["# Summary"]
    addcontent(dct,mdlst)

    open(mddst,"w").write("\n".join(mdlst))

        

