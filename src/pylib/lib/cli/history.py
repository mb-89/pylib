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
):
    """Recall cli history (mainly used for debugging)."""
    #TODO: rework this thing. doesnt work as intendend. new design: history should 
    #modify sys.argv before tp() gets called
    def pushfn():
        try:
            x = args_hist[n]
            args_hist.remove(x)
        except IndexError:
            return
        args_hist.appendleft(x)
        _set_cached_args(args_hist)
        return

    args_hist = _get_cache_args()
    global history_was_called
    history_was_called = True
    if add:
        args = sys.argv
        try:
            args_hist.remove(x)
        except:
            pass
        args_hist.appendleft(args)
        _set_cached_args(args_hist)

        return

    if clear:
        if n != -1:
            try:
                args_hist.remove(args_hist[n])
                x = args_hist
            except IndexError:
                return
        else:
            x = []
        _set_cached_args(x)
        return

    if n != -1:
        try:
            x = args_hist[n]
        except IndexError:
            return
        push = True #always push last cmd to top
        try:
            #print("running")
            #self.run(x)
            pass
        finally:
            #print("pushing")
            pushfn()
    
    if push:
        pushfn()

    # if we are here, print history
    for idx, x in enumerate(args_hist):
        from pylib.lib.cli.print import print
        print(f"{idx:3d} / {' '.join(x)}")

def _get_cache_args() -> deque:
    """Return the last cached cli calls."""
    path = Path(tempfile.gettempdir()) / argbuf_fn
    dq = deque(maxlen=hist_len)
    if not path.is_file():  # pragma: no cover
        return dq
    lst = json.loads(open(path, "r").read())
    for x in lst:
        dq.append(x)
    return dq


def _set_cached_args(args_dq: deque):
    """Cache this cli call."""
    path = Path(tempfile.gettempdir()) / argbuf_fn

    open(path, "w").write(json.dumps(list(args_dq)))

