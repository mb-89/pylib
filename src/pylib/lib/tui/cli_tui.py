from textual.app import App, ComposeResult, Binding
from textual.widgets import Footer, Header
from textual.widgets import Tree
from textual.widgets import HelpPanel
from textual.widgets import TabbedContent, TabPane
from textual.containers import Vertical
import click
from textual.widgets import RichLog

from pylib.lib.fns import getlogger, get_textual_log
log = getlogger()


def run():
    app = CLI_TUI()
    app.run()


class Cmdtree(Tree):
    def __init__(self):
        super().__init__("cli commands")
        ctx = click.get_current_context(silent=True).parent

        def cmd2tree(treeparent,cmd):
            treeparent.expand()
            for k in cmd.commands:
                v = cmd.commands[k]
                if hasattr(v,"commands"):
                    child=treeparent.add(k)
                    child.data = v
                    cmd2tree(child,v)
                else:
                    child=treeparent.add_leaf(k)
                    child.data = v

        cmd2tree(self.root, ctx.command)

class CMDdetails(RichLog):
    pass

class CLI_TUI(App):
    """A Textual app that displays cli functions."""

    BINDINGS = [
            Binding("f1", "help_toggle", "Help", priority=True)
        ]

    async def on_mount(self) -> None:
        # show the built‑in help screen immediately at startup
        self.action_show_help_panel()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()    
        with TabbedContent(initial="cmd"):
            with TabPane("CMD",id="cmd"):
                yield Cmdtree()
                with Vertical():
                    yield CMDdetails(name="Details",markup=False)
            with TabPane("log"):
                yield get_textual_log()

    def on_tree_node_highlighted(self,msg):
        #log.info(f"<{msg.node.label.plain}> selected")
        d = self.query_one(CMDdetails)
        d.clear()
        data = msg.node.data

        if data:
            ctx = click.get_current_context(silent=True).parent
            info = data.to_info_dict(ctx)
            
            txt = ["Help:\n"]
            txt.append(info["help"])
            txt.append("\nArguments:\n")
            for idx,x in enumerate(info["params"]):
                try:
                    helprecord = data.params[idx].get_help_record(ctx)
                    if helprecord is None:
                        helprecord = x.get("help","")
                    else:
                        helprecord = "\t".join(helprecord)
                except IndexError as ie:
                    if x["name"] == "help":
                        continue
                    else:
                        raise(ie)
                # TODO instead of displaying text, display a widget where we can enter commands.
                # might require pre-constructing all widgets
                txt.append(x["name"]+"\t"+x["type"]["name"]+"\t" + helprecord)

            d.write("\n".join(txt))

    def action_help_toggle(self,msg=None):
        try:
            hlpv = self.query_one(HelpPanel).visible
        except BaseException:
            hlpv=None
        if hlpv: 
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()