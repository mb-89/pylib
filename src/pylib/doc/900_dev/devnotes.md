# ideas / usecases
the pylib shall provide commonly used code that can either be
- imported via "from pylib import api" or similar
- injected, in case the target project doesnt allow pylib as a dependency (standalone w/o access to repos, inner src, ...)
Pylib shall provide a function to create a pylib-based project from scratch.
Pylib itself shall be pylib-based and provide examples for all functions
Pylib shall be able to extract itself from a path that it was injected in, to get back changes that might be incorporated.

backlog:

- [TODO] tui / jumpmode ala posting (alt-based instead of ctrl+o)


archive:

- [DONE] add logging
- [DONE] test injection into existing project
- [DONE] add update fn for injected code (saves source and tries to pull again)
- [DONE] cli based on typer
- [DONE] example browser / tests based on ipython notebooks and jupyterlab
- [DONE] written docu generator: extract docstrings from cli
- [DONE] written docu generator: generate mdbook?
- [DONE] add imp from git mode -> moved to "notImplementedError"
- [DONE] tui / compact designs for inputs ala posting
- [DONE] implement [flags](feature_flags.md)