import typer
import sys
from typing_extensions import Annotated as ant
import tempfile
from collections import deque
from pathlib import Path
import json

packagename = __package__.split(".")[0]
argbuf_fn = f"{packagename}_argbuf"
ta = typer.Argument
to = typer.Option
hist_len = 20
history_was_called = False

def history(
    n: ant[int, ta(help="selected history entry")] = -1,
    push: ant[
        bool, to("-p", "--push", help="push the selected entry to the top")
    ] = False,
    clear: ant[
        bool, to("-c", "--clear", help="clear (if n not provided, clear all)")
    ] = False,
    add: ant[
        bool,
        to("-a", "--add", help="add current sys.argv to hist. used internally"),
    ] = False,
    stub: ant[bool,to("--stub",hidden=True,help ="only used internally")] = True
):
    """Recall cli history (mainly used for debugging)."""
    
    if stub:
        return
    
    done = False
    argv = sys.argv

    if done:
        argv = None

    return argv