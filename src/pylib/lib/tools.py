import asyncio
import functools
import subprocess
import os
from pathlib import Path

def maybe_async(func):
    """Allow a function to be either awaited or called.

    There is some overhead in the sync-path for every call.
    Dont use for small, often called syn fns.

    Define:
    @maybe_async
    async def my_function(x):
        return 1

    Call:
    result = my_function(10)       # sync
    result = await my_function(10) # async
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            asyncio.get_running_loop()
            sync = False
        except RuntimeError:
            sync = True
        if not sync:
            return func(*args, **kwargs)
        else:

            async def asynciowrap():
                coro = func(*args, **kwargs)
                res = await coro
                return res

            return asyncio.run(asynciowrap())

    return wrapper


def run_detached(cmd,cwd = None):
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_CONSOLE = 0x00000010
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    flags = CREATE_NEW_CONSOLE

    # works when not debugging. doesnt work when debugging
    subprocess.Popen(
        cmd,
        cwd=cwd,
        creationflags=flags,
    )

def mk_win_link(linkname, target, dst=None):
    if dst is None: 
        dst = Path(os.getcwd())
    lnkstr=str(dst/f"{linkname}.lnk").replace("/","\\")
    targetstr=str(target).replace("/","\\")
    subprocess.run(["powershell", "-Command", f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnkstr}'); $s.TargetPath='{targetstr}'; $s.Save();"], capture_output=True)  