# Motivation / spec
- [TODO] we shall have a singleton cfg that allows loading files and reading values from everywhere
- [TODO] values can be found via paths. paths should be compatible with glob, regexes and xpath expressions.This implicitly means that a query can return multiple values.
- [TODO] reading the config shall be done via a .get() function
- [TODO] writing the config shall be done by multiple ways as below, in ascending order of prioirity
- [TODO] environment variables: env vars with a given prefix are loaded on startup, if we pass the prefix to the program.
- [TODO] cfg files: cfg files are loaded during startup of later by code. they can also be unloaded, except for the "default" cfg
- [TODO] commandline flags: commandline flags override the default config, but not later loaded cfgs
- [TODO] context managers: contexts can override values. on leaving the context, the override is cleared
- [TODO] manual override: mostly used for guis/editors: master override that has absolute priority. only one per value.
- [TODO] every value should know its overrides, and it should be possible to query them
- [TODO] we should be able to export / display the current state of the config, if possible with reasonable effort, in a tui-tab.
- [TODO] there should be a watch/callback system that triggers callbacks on cfg changes.

A different approach would have been to go with a sass / css like system. However, after some consideration, it seems that the combination
of the cascading / inherited values and overrides seems too unintuitive and generating a clean state of the cfg seems too convoluted. 
If at all possible, it should be intuitive for the user to understand which source of values is currently providing the cfg values.
We cannot assume that users know and understand cascading sheets and inheirtance, and even if they do, they will not know the 
details about class/implementation names in the code. Especially difficult seemed to be the decision wether overrides apply to classes
or instances, if we went with css. 
Clarity about the cfg behavior has been a painpoint in earlier cfg systems and will cause confusion and stall usage in the field if not done right.
Therefore, we dont go the css route, even though it has some niceties to it.

The mvp is file support. everything else can be added later.

# implementation
- the example usage shall be implemented in 100_interactive_docu/000_cfg.ipynb
- the functionality shall be implemented within the lib, likely lib/cfg, and easily importable outside

# tests / review
- [TODO] tests, insofar as they are not in the interactive docu, shall be in test_cfg.py