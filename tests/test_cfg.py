"""Mainly used for debugging the config system."""

from pylib.lib.fns import getcfg

def test_basics():
    cfg = getcfg()
    dct = {"key1":"val1"}
    cfg.set(dct)
    cfg.toxml(dst=None)
    cfg.set("key2", 2,parent="bla") 
    cfg.print()
    cfg.get("key1")
    cfg.get("key2")
    cfg.get("bla/key2")
    cfg.get("doesnt_exist", -1)
    