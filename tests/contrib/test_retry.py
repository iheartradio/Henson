"""Test for henson.contrib.retry."""

import time

import pytest

from henson.contrib import retry


@pytest.fixture
def callback():
    """Return a stubbed callback function."""
    def _inner(*args):
        pass
    return _inner


@pytest.mark.parametrize('number_of_retries, threshold, expected', [
    # Retry forever.
    (0, None, False),
    (1, None, False),
    # Don't retry.
    (0, 0, True),
    (1, 0, True),
    # Rrtry.
    (0, 1, False),
    (1, 2, False),
])
def test_exceeded_threshold(number_of_retries, threshold, expected):
    """Test _exceeded_threshold."""
    actual = retry._exceeded_threshold(number_of_retries, threshold)
    assert actual == expected


@pytest.mark.parametrize('offset, duration, expected', [
    # Retry forever.
    (0, None, False),  # now
    (10000, None, False),  # 10 seconds ago
    # Don't retry.
    (0, 0, True),
    (10000, 0, True),
    # Retry.
    (1000, 10, False),
    (10000, 20, False),
])
def test_exceeded_timeout(offset, duration, expected):
    """Test _exceeded_timeout."""
    start_time = int(time.time()) - offset
    actual = retry._exceeded_timeout(start_time, duration)
    assert actual == expected


def test_callback_insertion(test_app, callback):
    """Test that the callback is properly registered."""
    # Add an error callback before registering Retry.
    def original_callback(*args):
        pass
    test_app.error_callbacks.append(original_callback)

    # Register Retry.
    test_app.settings['RETRY_CALLBACK'] = callback
    retry.Retry(test_app)

    assert test_app.error_callbacks[0] is retry._retry


def test_callback_exceeds_threshold(test_app, callback):
    """Test that callback doesn't run when the threshold is exceeded."""
    # Create a function that sets a flag indicating it's been called.
    original_callback_called = False

    def original_callback(*args):
        nonlocal original_callback_called
        original_callback_called = True

    test_app.error_callbacks.append(original_callback)

    test_app.settings['RETRY_CALLBACK'] = callback
    test_app.settings['RETRY_THRESHOLD'] = 0

    for cb in test_app.error_callbacks:
        cb(test_app, {}, retry.RetryableException())

    assert original_callback_called


def test_callback_exceeds_timeout(test_app, callback):
    """Test that callback doesn't run when the timeout is exceeded."""
    # Create a function that sets a flag indicating it's been called.
    original_callback_called = False

    def original_callback(*args):
        nonlocal original_callback_called
        original_callback_called = True

    test_app.error_callbacks.append(original_callback)

    test_app.settings['RETRY_CALLBACK'] = callback
    test_app.settings['RETRY_TIMEOUT'] = 0

    for cb in test_app.error_callbacks:
        cb(test_app, {}, retry.RetryableException())

    assert original_callback_called


def test_callback_prevents_others(test_app, callback):
    """Test that the callback blocks other callbacks."""
    test_app.settings['RETRY_CALLBACK'] = callback
    retry.Retry(test_app)

    with pytest.raises(StopIteration):
        for cb in test_app.error_callbacks:
            cb(test_app, {}, retry.RetryableException())
