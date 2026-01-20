import importlib
def getversion():
    try:
        version = importlib.metadata.version("pylib")
    except ModuleNotFoundError:
        version = "$INJECTED_VERSION"
    return version

def getlogger():
    from pylib.lib.log import getlogger as gl
    return gl()

def getCLI():
    from pylib.lib.cli.CLI import CLI
    return CLI