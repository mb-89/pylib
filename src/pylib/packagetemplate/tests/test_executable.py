"""Test if the cli is executable at all or if dependencies are missing"""

import pytest
from $PKG$ import cli


@pytest.mark.smoke
def test_runnable():
    cli.run([])
