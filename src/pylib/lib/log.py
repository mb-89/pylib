from functools import cache
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from pathlib import Path

custom_theme = Theme(
    {
        "logging.level.debug": "cyan",
        "logging.level.info": "green",
        "logging.level.warning": "yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold white on red",
        "logging.time": "magenta",
    }
)

logconsole = Console(theme=custom_theme)


@cache
def getFmtStrings(name):
    dct = {}

    if name == "log":
        sfmtstr = "%(message)s"
        ffmtstr = "%(levelname)s\t%(message)s @ %(module)s.py:%(lineno)d"

    else:
        sfmtstr = "%(name)s / %(message)s"
        ffmtstr = "%(levelname)s\t%(name)s / %(message)s @ %(module)s.py:%(lineno)d"

    dct["stream"] = sfmtstr
    dct["file"] = ffmtstr

    return dct


@cache
def getlogger(name="log"):
    log = logging.getLogger(name)
    hdl = RichHandler(console=logconsole)

    fmts = getFmtStrings(name)["stream"]
    fmt = logging.Formatter(fmts)

    hdl.setFormatter(fmt)
    log.addHandler(hdl)

    log.setLevel(logging.DEBUG)
    hdl.setLevel(logging.DEBUG)

    return log


@cache
def log2file(path: Path):
    fh = logging.FileHandler(path)
    log = getlogger()
    fmts = getFmtStrings(log.name)["file"]
    fmt = logging.Formatter(fmts)
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

class TextualHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
    def emit(self,record):
        try:
            msg = self.format(record)
            self.widget.write(msg)
        except Exception:
            self.handleError(record)


@cache
def get_textual_log():
    log = getlogger()

    try:
        import textual
    except BaseException:
        return
    from textual.widgets import RichLog
    w = RichLog()
    
    wh = TextualHandler(w)
    fmts=getFmtStrings(log.name)["file"]
    fmt = logging.Formatter(fmts)
    wh.setFormatter(fmt)
    wh.setLevel(logging.DEBUG)    
    log.addHandler(wh)


    return w