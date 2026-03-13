import tempfile
from pathlib import Path
import json
from enum import Enum
from pylib.lib.tools import get_temp_dir, iter_nested_dict
import hashlib
from operator import itemgetter
from lxml import etree as et
from rich.table import Table
from rich import print as rprint


class SRC_MODE_PRIO(Enum):
    OVERRIDE = 0
    DEFAULT = 1

class SRC_TYPE_PRIO(Enum):
    MANUAL = 0
    CONTEXT = 1
    CMDLINE = 2
    ENV = 3
    FILE = 4

class Sources():
    def __init__(self):
        self.sources = {}

    def mount(self,key: Path | dict | str, val = None, parent: str = ""):
        src = Source(self, key, val ,parent)
        src.prio = self.prioritize(src)
        self.sources[src.prio] = src
    
    def unmount(self, key):
        if isinstance(key,int):
            src= list(self.iter_by_prio())[key]
            self.sources.pop(src.prio)
            return
        #TODO: we can make this smarter.
        src = [v for k,v in self.sources.items() if v.srcfile.stem.startswith(key)][0]
        self.sources.pop(src.prio)


    def print(self):

        table = Table(title="Config sources")
        table.add_column("#",justify="left")
        table.add_column("title",justify="left")
        table.add_column("prio",justify="right")
        for idx,x in enumerate(self.iter_by_prio()):
            table.add_row(str(idx),str(x.srcfile.stem),str(x.prio))
        rprint(table)

    def iter_by_prio(self):
        for x in sorted(self.sources,key=itemgetter(0,1,2),reverse=True):
            yield self.sources[x]

    def prioritize(self, src) -> tuple:
        """Prioritize source. Lower prios override higher prios (prio 0 = highest)"""

        # TODO: for now, lets implement only default files. rest can come later
        # TODO: also, missing is: remove existing on override
        # TODO: this will have to be made much smarter in the future.

        mode = SRC_MODE_PRIO.DEFAULT if not self.sources else SRC_MODE_PRIO.OVERRIDE
        type = SRC_TYPE_PRIO.FILE

        prio = (mode.value,type.value,-len(self.sources))
        
        return prio

class Source():
    def __init__(self, source_container, key: Path | dict | str, val = None, parent: str = ""):

        self.prio = tuple()

        # we want to be able to unmount sources. this means every input
        # is transformed into a file, even a string or dict
        if isinstance(key, str):
            key = {key: val}
        if isinstance(key,dict):
            td = get_temp_dir()
            #TODO: maybe add mount-time to filename?
            fname = f"cfg_{hashlib.sha1("".join(key.keys()).encode()).hexdigest()[:9]}.json"
            jsonstr = json.dumps(key,indent=4)
            key = td / fname
            open(key,"w").write(jsonstr)    
        
        self.srcfile = key
        self.parent = parent
        self.source_container = source_container

    def toxmls(self):
        #TODO: for now, only support json. might add xml support later
        data = json.loads(open(self.srcfile,"rb").read().decode("utf-8"))

        tmp_root = et.Element("tmp_root")
        for k,v in iter_nested_dict(data):
            
            target = tmp_root
            sks = k.split("/")
            for idx,sk in enumerate(k.split("/")[:-1]):
                sk = sk.strip()
                buf = target.find(sk)
                if buf is not None:
                    target = buf
                else:
                    target = et.SubElement(target,sk)
                if idx == 0:
                    target.attrib["cfg_parent"] = self.parent

            sk = sks[-1]
            target = et.SubElement(target,sk)
            if len(sks)==1:
                target.attrib["cfg_parent"] = self.parent
            target.text = str(v)
            target.attrib["cfg_type"] = v.__class__.__name__

            #note: a source doesnt know about potential other sources.
            #merging sources needs to happen higher up in the stack.
            src_id = list(self.source_container.iter_by_prio()).index(self)
            target.attrib["cfg_source"] = str(src_id)
        for ch in tmp_root.iterchildren():
            ch.getparent().remove(ch)
            yield ch
