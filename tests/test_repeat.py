"""Run this as a debug-hook for tests. Skipped during non-debug testing."""
#part_of_template

import sys

import pytest

from pylib import cli


@pytest.mark.repeat
def test_repeat(pytestconfig):
    """Run this test via 'poe test -m repeat' to test the last command."""
    markers_arg = pytestconfig.getoption("-m")
    tr = sys.gettrace()  # if we have a tracer, assume that we are in debug mode and run
    isdebugger = tr is not None and "coverage" not in str(tr)
    if ("repeat" not in markers_arg) and not isdebugger:
        return
    cli.run(["history", "0"])
