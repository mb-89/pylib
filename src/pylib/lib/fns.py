import importlib
def getversion():
    try:
        version = importlib.metadata.version("pylib")
    except ModuleNotFoundError:
        version = "$INJECTED_VERSION"
    return version