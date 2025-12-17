# ideas / usecases
the pylib shall provide commonly used code that can either be
- imported via "from pylib import api" or similar
- injected, in case the target project doesnt allow pylib as a dependency (standalone w/o access to code.siemens, inner src, ...)
Pylib shall provide a function to create a pylib-based project from scratch.
Pylib itself shall be pylib-based and provide examples for all functions
Pylib shall be able to extract itself from a path that it was injected in, to get back changes that might be incorporated.

integrated features:
- [DONE] cli based on typer
- [DONE] example browser / tests based on ipython notebooks and jupyterlab
- [TODO] written docu generator: extract docstrings from cli
- [TODO] written docu generator: generate mdbook?
- [TODO] add imp from git mode -> later, after git access restore
- [TODO] add logging
- [DONE] test injection into existing project
- [TODO] add update fn for injected code (saves source and tries to pull again)