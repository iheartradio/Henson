"""Test the application registry."""

import pytest

from henson.registry import Registry


@pytest.fixture
def registry():
    """Create an application registry."""
    return Registry()


@pytest.fixture
def settings():
    """Create a configuration object."""
    class Config:
        A = 1
        B = 2

    return Config
