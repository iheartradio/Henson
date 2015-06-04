"""Test the application registry."""

import pytest

import henson.base
from henson.registry import Registry


@pytest.fixture
def mock_registry(request):
    """Create a new application registry and restore the old one."""
    original = henson.base.registry._applications

    def teardown():
        henson.base.registry._applications = original
    request.addfinalizer(teardown)

    henson.base.registry._applications = []

    return registry


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
