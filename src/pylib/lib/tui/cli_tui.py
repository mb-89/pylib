from textual.app import App, ComposeResult, Binding
from textual.widgets import Footer, Header
from textual.widgets import Tree
from textual.widgets import HelpPanel
import click
from textual.widgets import RichLog,Label, Input, Switch, Button,TabbedContent, TabPane,Markdown
from textual.containers import Vertical, Horizontal,VerticalScroll
from textual.message import Message
from textual import on
from pathlib import Path
from textual import events
import os
import tomllib  

from pylib.lib.fns import getlogger
from pylib.lib.tools import run_detached
log = getlogger()


def run():
    app = CLI_TUI()
    app.run()
pkg =__package__.split(".")[0]

rootpath = Path(__file__).parent.parent.parent.parent.parent
pkgdescr = tomllib.load(open(rootpath/"pyproject.toml","rb"))["project"]["description"]
HOME_MD = f"""
# {pkg}

## package info

{pkgdescr}

## further reading

- press [f1](app:action_help_toggle) to show the help sidebar.
- see the [CLI](tab:clitab) tab for all commandline functions.
- call [{pkg} --help](cmd:--help) for the commandline help.
- call [{pkg} --docu](cmd:--docu) for specs and interactive docu.
- see [README](path:$root/README.md) for setup information.

"""


class Cmdtree(Tree):

    def __init__(self):
        super().__init__("cli commands")
        ctx = click.get_current_context(silent=True).parent

        def cmd2tree(treeparent,cmd,storage,prefix=""):
            treeparent.expand()
            for k in cmd.commands:
                storagekey = prefix+"_"+k
                v = cmd.commands[k]
                if hasattr(v,"commands"):
                    child=treeparent.add(k)
                    child.data = v
                    cmd2tree(child,v,storage,storagekey)
                    storage[storagekey] = child
                    child.storagekey = storagekey
                else:
                    child=treeparent.add_leaf(k)
                    child.data = v
                    child.storagekey = storagekey
                    storage[storagekey] = child
        self.cmds = {}
        cmd2tree(self.root, ctx.command,self.cmds)

    def generate_subwidgets(self):
        ctx = click.get_current_context(silent=True).parent
        for k,v in self.cmds.items():
            w = CMDdetails(k,v,ctx)
            cmd = CMDline()
            cont =  Vertical(w,cmd)
            cont.display=False
            v.widget = cont
            yield cont

class Mk_curr_cmdline(Message):
    pass

class Argument_switch(Switch):
    def on_switch_changed(self,_):
        self.post_message(Mk_curr_cmdline())

class Argument_Input(Input):
    def on_input_changed(self,_):
        self.post_message(Mk_curr_cmdline())

class ArgumentInput(Horizontal):
    def __init__(self, arg, detail: str):
        super().__init__()
        self.arg = arg
        self.detail_text = detail 

    def compose(self) -> ComposeResult:
        arg = self.arg
        yield Label(arg["name"], id="li-label")
        yield Label(self.detail_text, id="li-label-detail")
        yield Label(f"[@click=app.display_help()](?)[/]", id="li-label-more")

        tpname = arg["type"]["name"] 
        placeholder = tpname + ("" if not arg["default"] else " [" + str(arg["default"] )+"]")
        placeholder = "$" + placeholder + "$"
        match tpname:
            case "boolean":
                self.val = Argument_switch(value = arg["default"])
                yield self.val
            #case "path":
            # there is no good/quick way to implement a filepicker. leave it for now.
            #        yield Button("Browse")
            #        yield Input(placeholder=placeholder,id="li-input")
                    
            case _:
                tp = "text"
                if tpname == "integer":
                    tp = "integer"
                elif tpname == "float":
                    tp = "number"
                self.val = Argument_Input(placeholder=placeholder,id="li-input",type=tp)
                yield self.val

class CMDInput(Input):
    pass

class CMDline(Horizontal):

    def __init__(self):
        inp = CMDInput("")
        inp.styles.max_width="80%"

        but = Button("run",variant="success")
        but.can_focus=False

        lbl = Label("\nCLI command:")
        lbl.styles.align_vertical = "middle"
        lines = [
            lbl,
            inp,
            but
        ]
        
        super().__init__(*lines)
        self.styles.max_height=3

    def on_button_pressed(self):
        self.app.query_one(CLI_pane).action_run()
       
class CMDdetails(Vertical):

    def __init__(self, name, node, ctx):
        info = node.data.to_info_dict(ctx)
        helpstr = Label(info["help"],expand=True)

        children = []

        for idx,x in enumerate(info["params"]):
            try:
                helprecord = node.data.params[idx].get_help_record(ctx)
                if helprecord is None:
                    helprecord = x.get("help","")
                else:
                    helprecord = " | ".join(helprecord)
            except IndexError as ie:
                if x["name"] == "help":
                    continue
                else:
                    raise(ie)
            helprecord = helprecord.replace("\t"," ")
            line = ArgumentInput(x,helprecord)
            children.append(line)

        if children:
            pcont = VerticalScroll(*children)
            lines = [helpstr]+[Label("\nArguments (click (?) for more):\n")]+[pcont]
        else:
            lines = [helpstr]

        super().__init__(*lines)
        #self.display = False

class Home(Markdown):
    def on_markdown_link_clicked(self, event):
        lnk = event.href
        lnktype, lnkbody = lnk.split(":")
        match lnktype:
            case "cmd":
                cmd = f"uv run {pkg} "+lnkbody
                run_detached(cmd)
                self.app.notify("executed command in detached shell.")
            case "app":
                app = self.app
                getattr(app,lnkbody)()
            case "tab":
                app=self.app
                w = app.query_one(TabbedContent)
                w.active=lnkbody
                w.focus()
            case "path":
                path = Path(lnkbody.replace("$root",str(rootpath))).resolve()
                if not path.is_file():
                    self.app.notify(f"{path} not found. try --docu instead.",Severity="warning")
                else:
                    os.startfile(path)
                    self.app.notify(f"{path} opened in editor.")



async def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "close":
        await self.app.pop_screen()

async def on_key(self, event: events.Key) -> None:
    # Close on Escape
    if event.key == "escape":
        await self.app.pop_screen()

class LogWidget(RichLog):
    can_focus=False

    def __init__(self, log, *args, **kwargs):
        super().__init__(*args,**kwargs)
        log.connect_textual_widget(self)

class CLI_pane(TabPane):
    BINDINGS = [
            Binding("f5", "run", "Run",priority=True),
    ]


    def action_run(self):
        ac = self.app.active_cmd
        if not ac:
            return
        cmd = ac.widget.query_one(CMDInput).value
        run_detached(cmd)
        self.app.notify("executed command in detached shell.")

class CLI_TUI(App):
    """A Textual app that displays cli functions."""
    CSS_PATH = "cli_tui.tcss"
    BINDINGS = [
            Binding("f1", "help_toggle", "Help", priority=True),
            Binding("ctrl+l", "log_toggle", "log",show=True)
        ]

    @on(Mk_curr_cmdline)
    def mk_cmd_callback(self):
        ac =  self.active_cmd
        if ac is None:
            return
        

        cmd = ac.storagekey.replace("_"," ").strip()
        input = ac.widget.query_one(CMDInput)

        args = []
        for arg in tuple(ac.widget.query(ArgumentInput)):
            aname = arg.arg["opts"][0]
            atype = arg.arg["param_type_name"]
            default = str(arg.arg["default"])
            val = arg.val.value
            if arg.arg["required"] and not val:
                val = arg.val.placeholder
            if atype == "argument":
                args.append(str(val))
            elif atype == "option":
                if arg.arg["type"]["name"] == "boolean":
                    if val:
                        args.append(aname)
                else:
                    if val:
                        args.append(aname)
                        args.append(val)


        input.value = f"uv run {pkg} {cmd} " + " ".join(args)

    async def on_mount(self) -> None:
        # show the built‑in help screen immediately at startup
        #self.action_show_help_panel()
        log.info("mounted tui")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        
        #yield Header()
        yield LogWidget(log, classes="-hidden",wrap=False, highlight=True, markup=True) 
        with TabbedContent():
            with TabPane("Home"):
                yield Home(HOME_MD,open_links=False)
            with CLI_pane("CLI",id="clitab"):
                yield (t := Cmdtree())
                yield from t.generate_subwidgets()

        #with Horizontal(id="footer-outer"):
        #    with Horizontal(id="footer-inner"):
        yield Footer()
        #   yield Label("| ^l log [000 msgs]", id="right-label")



    def on_tree_node_highlighted(self,msg):
        node = msg.node
        tree = self.query_one(Cmdtree)
        self.active_cmd = None
        for cmd in tree.cmds.values():
            cmd.widget.display=False
        if node.data:
            node.widget.display=True
            self.active_cmd = node
            self.post_message(Mk_curr_cmdline())

    def action_log_toggle(self,msg=None,setval_hide : bool | None = None):

        rl = self.query_one(LogWidget)
        if setval_hide is None:
            setval_hide = not rl.has_class("-hidden")
        if setval_hide:
            rl.add_class("-hidden")
        else:
            rl.remove_class("-hidden")

    def action_help_toggle(self,msg=None):
        try:
            hlpv = self.query_one(HelpPanel).visible
        except BaseException:
            hlpv=None
        if hlpv: 
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()