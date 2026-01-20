from pylib.lib.fns import getCLI
from pathlib import Path

name = "pylib"
URL = "https://<URL>/pylib" #TODO: see if we actually need this.
example_dir = "doc"
fn_dir = "fns"

cli = getCLI()
cli.setparams(name=name,url=URL,exampledir = example_dir)
cli.importcmds(Path(__file__) / ".." / fn_dir)
run = cli.run

if __name__ == "__main__":
    run()
