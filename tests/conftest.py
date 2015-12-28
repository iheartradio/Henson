"""Test the application registry."""

import asyncio

import pytest

from henson import Application
from henson.exceptions import Abort


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

    def run_forever(self, num_workers=1):
        print('Run, Forrest, run!')


class MockConsumer:
    """A stub consumer that can be used for testing."""

    @asyncio.coroutine
    def read(self):
        """Return an item."""
        return 1


class MockAbortingConsumer:
    """A stub consumer that will raise Abort."""

    _run = False

    @asyncio.coroutine
    def read(self):
        """Return an item."""
        if self._run:
            raise Abort('testing', {})

        self._run = True
        return 1


@pytest.fixture
def cancelled_future(event_loop):
    """Return a Future that's been cancelled."""
    future = asyncio.Future(loop=event_loop)
    future.cancel()
    return future


@pytest.fixture
def coroutine():
    """Return a coroutine function."""
    @asyncio.coroutine
    def _inner(*args, **kwargs):
        pass
    return _inner


@pytest.fixture
def queue():
    """Return an asynchronous queue."""
    return asyncio.Queue()


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


@pytest.fixture
def test_consumer_with_abort():
    """Return a test consumer."""
    return MockAbortingConsumer()
