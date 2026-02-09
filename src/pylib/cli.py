#part_of_template
from pylib.lib.fns import getCLI
from pathlib import Path

example_dir = "doc"
fn_dir = "fns"

cli = getCLI()
cli.setparams(name=__package__,exampledir = example_dir,fndirs=[Path(__file__) / ".." / fn_dir])
run = cli.run

if __name__ == "__main__":
    run()
