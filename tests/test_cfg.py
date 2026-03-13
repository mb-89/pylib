"""Mainly used for debugging the config system."""

from pylib.lib.fns import getcfg

def test_basics():
    cfg = getcfg()
    dct = {"key1":"val1","key1a":"b"}
    cfg.set(dct)
    cfg.toxml(dst=None)
    cfg.set("key2", 2,parent="bla") 
    cfg.set({"nest1":{"nv1":10, "nv2":20},"v3":3}, parent="nested")
    cfg.print()

    cfg.get("key1")
    cfg.get("key2")
    cfg.get("bla/key2")
    cfg.get("doesnt_exist", -1)

if __name__ == "__main__":
    test_basics()