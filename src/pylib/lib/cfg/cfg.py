from pathlib import Path
from functools import cache
from lxml import etree as et

from pylib.lib.cfg.src import Sources
from pylib.lib.fns import getlogger
from pylib.lib.tools import get_type_by_name

from rich.tree import Tree
from rich import print as rprint

log = getlogger()

class Values():
    def __init__(self,cfg):
        self.cfg = cfg

    def print(self):
        tree = self.cfg.toRichTree()
        rprint(tree)



class Cfg():
    @staticmethod
    @cache
    def getSingleton():
        return Cfg()

    def __init__(self):
        self.clear()

    def clear(self):
        self.values = Values(self)
        self.sources = Sources()
        self.xmlroot = et.Element("cfg")
        self.xml = et.ElementTree(self.xmlroot)

    def set(self, key: Path | dict | str, val=None, parent: str = ""):
        """Set values in the config."""
        self.sources.mount(key, val, parent)
        self.buildxml()            

    def get(self, query:str, default = None):
        res = self.xmlroot.xpath(query)
        if not res:
            return default
        #TODO: value casting
        if len(res) == 1:
            return get_casted_val(res[0])
        if len(res) > 1:
            dct = {}
            for x in res:
                dct[self.xml.getpath(x)[1:]] = get_casted_val(x)
            return dct


    def toxml(self, dst = "cfg.xml"):
        et.indent(self.xml, space="\t")
        if dst == str:
            from pylib.lib.cli.print import print
            return et.tostring(self.xml).decode("utf-8")
        elif isinstance(dst, (str,Path)):
            dst = Path(dst)
            open(dst,"wb").write(et.tostring(self.xml))
            return dst
        else:
            return self.xmlroot

    def toRichTree(self):
        xml = self.xmlroot
        t = Tree(xml.tag)

        def recursive_resolve(xmlsrc,treedst):
            for x in xmlsrc.iterchildren():
                
                if len(x):
                    ch = treedst.add(x.tag)
                    recursive_resolve(x,ch)
                else:
                    ch = treedst.add(f"{x.tag}\t[red]{x.text}")
        
        recursive_resolve(xml,t)
        return t

    def print(self):
        self.sources.print()
        self.values.print()

    def buildxml(self):
        root = self.xmlroot
        root.clear()
        for src in self.sources.iter_by_prio():
            xmls = src.toxmls()
            for xml in xmls:
                #TODO: logic that doesnt re-create on every imput, but merges
                parent = xml.attrib["cfg_parent"]
                if not parent:
                    target = root
                else:
                    target = root.xpath(parent)
                    if not len(target):
                        target = root
                        for x in (y.strip() for y in parent.split("/")):
                            target = et.SubElement(target,x)

                target.append(xml)

def get_casted_val(x):
    tp = get_type_by_name(x.attrib["cfg_type"])
    val = x.text
    if tp is not None:
        val = tp(val)
    return val
