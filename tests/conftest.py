"""Test the application registry."""

import pytest

from click.testing import CliRunner


class Application:

    """A stub application that can be used for testing.

    Args:
        **settings: Keyword arguments that will be used as settings.
    """

    def __init__(self, **settings):
        """Initialize the instance."""
        self.name = 'testing'
        self.settings = settings


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
    return Application()


@pytest.fixture
def click_runner():
    """Return a click CLI runner."""
    return CliRunner()
