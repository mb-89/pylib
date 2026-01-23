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
    select: ant[
        bool, to("-s", "--select", help="interactively select a history entry and repeat it.")
    ] = False,
    stub: ant[bool,to("--stub",hidden=True,help ="only used internally")] = True
):
    """Recall cli history (mainly used for debugging)."""
    
    if stub:
        return
    
    done = False
    argv = sys.argv

    # if we are here, we are called during preprocessing. we need to extract the flags manually
    push = "-p" in argv or "--push" in argv
    clear = "-c" in argv or "--clear" in argv
    select = "-s" in argv or "--select" in argv

    if "history" in argv:
        hist_idx = argv.index("history")
        try:
            n = int(argv[hist_idx+1])
        except BaseException:
            if push or clear:
                try:
                    n = int(argv[hist_idx+2])    
                except BaseException:
                    n = -1
    else:
        add_argv(argv)
        return argv

    if clear:
        clear_hist(n)
        done=True
    elif push:
        push_hist(n)
        done=True
    elif select:
        print_hist()
        argv = ["history"] + select_argv()
    else:
        if n == -1:
            print_hist()
            done = True
        else:
            # if we are here, we have a valid n to execute
            argv = ["history"] + get_argv()[n]

    if done:
        argv = None

    return argv

def clear_hist(n):
    if n != -1:
        try:
            h = get_argv()
            h.remove(h[n])
        except IndexError:
            print_hist()
            return
    else:
        h = []
    set_argv(h)
    print_hist()

def push_hist(n, silent=False):
    h = get_argv()
    try:
        x = h[n]
        h.remove(x)
    except IndexError:
        return
    h.appendleft(x)
    set_argv(h)
    if not silent:
        print_hist()
    return

def add_argv(argv):
    h = get_argv()
    argv = argv[1:]
    try: 
        n = h.index(argv)
    except BaseException:
        n = -1

    if n != -1:
        push_hist(n,silent=True)
    else:
        h.appendleft(argv)
        set_argv(h)

def print_hist():
    h = get_argv()
    from pylib.lib.cli.print import print
    if not h:
        print("<history empty>")
        return
    for idx, x in enumerate(h):
        print(f"{idx:3d} / {' '.join(x)}")

def select_argv():
    n = input("please select the entry number to repeat.\n>>> ")
    try:
        argv = get_argv()[int(n)]
    except BaseException:
        print("invalid entry. abort")
        exit(-1)
    return argv


def get_argv() -> deque:
    """Return the last cached cli calls."""
    path = Path(tempfile.gettempdir()) / argbuf_fn
    dq = deque(maxlen=hist_len)
    if not path.is_file():  # pragma: no cover
        return dq
    data = open(path, "r").read()
    if data:
        lst = json.loads(data)
    else:
        lst = []
    
    for x in lst:
        dq.append(x)
    return dq

def set_argv(argv):
    path = Path(tempfile.gettempdir()) / argbuf_fn

    open(path, "w").write(json.dumps(list(argv)))