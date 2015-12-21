"""Test the application registry."""

import asyncio

import pytest

from henson import Application


class MockApplication(Application):
    """A stub application that can be used for testing.

    Args:
        **settings: Keyword arguments that will be used as settings.
    """

    def __init__(self, **settings):
        """Initialize the instance."""
        self.name = 'testing'
        self.settings = settings

        self.error_callbacks = []

    def run_forever(self):
        print('Run, Forrest, run!')


class MockConsumer:
    """A stub consumer that can be used for testing."""

    @asyncio.coroutine
    def read(self):
        """Return an item."""
        return 1


@pytest.fixture
def coroutine():
    """Return a coroutine function."""
    @asyncio.coroutine
    def _inner(*args, **kwargs):
        pass
    return _inner


@pytest.fixture
def settings():
    """Create a configuration object."""
    class Config:
        A = 1
        B = 2

    return Config


@pytest.fixture
def test_app():
    """Return a test application."""
    return MockApplication()


@pytest.fixture
def test_consumer():
    """Return a test consumer."""
    return MockConsumer()
