"""Test Application."""

import pytest

from henson.base import Application


def test_run_forever_consumer_is_none_typeerror():
    """Test that TypeError is raised when the consumer is None."""
    app = Application('testing', consumer=None)
    with pytest.raises(TypeError):
        app.run_forever()


@pytest.mark.parametrize('callback', (None, '', False, 10))
def test_run_forever_callback_not_callable_typerror(callback):
    """Test that TypeError is raised when callback isn't callable."""
    app = Application('testing', consumer=[], callback=callback)
    with pytest.raises(TypeError):
        app.run_forever()
