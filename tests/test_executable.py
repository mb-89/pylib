"""Test if the cli is executable at all or if dependencies are missing"""
#part_of_template

import pytest
from pylib import cli


@pytest.mark.smoke
def test_runnable():
    cli.run([])
