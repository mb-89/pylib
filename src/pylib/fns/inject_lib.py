from pathlib import Path
import shutil
import os


def inject_lib(dstdir: Path):
    name = dstdir.stem
    libsrc = Path(__file__) / ".." / ".." / "lib"
    libdst = dstdir / "src" / name / "lib"
    shutil.copytree(
        libsrc,
        libdst,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*["__pycache__", ".ipynb_checkpoints"]),
    )

    try:
        os.symlink(dstdir / "src" / name / "doc" / "lib_doc", libdst / "doc")
    except WindowsError:
        print(
            "[WARNING] symlink to lib docu couldnt be created. try running as admin. This only influences the documentation."
        )
