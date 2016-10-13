"""Test for henson.contrib.retry."""

from contextlib import suppress
import time

import pytest

from henson.contrib import retry
from henson.exceptions import Abort


@pytest.mark.parametrize('delay, backoff, count, expected', (
    (1, 1, 0, 1),
    (1, 1, 1, 1),
    (1, 1, 4, 1),
    (1, 2, 0, 1),
    (1, 2, 1, 2),
    (1, 2, 4, 16),
    (10, 1.5, 0, 10),
    (10, 1.5, 1, 15),
    (10, 1.5, 4, 50.625),
))
def test_calculate_delay(delay, backoff, count, expected):
    """Test _calculcate_delay."""
    actual = retry._calculate_delay(delay, backoff, count)
    assert actual == expected


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
    @test_app.error
    def original_callback(*args):
        pass

    # Register Retry.
    test_app.settings['RETRY_CALLBACK'] = callback
    retry.Retry(test_app)

    assert test_app._callbacks['error'][0] is retry._retry


def test_callback_exceeds_threshold(test_app, callback):
    """Test that callback doesn't run when the threshold is exceeded."""
    # Create a function that sets a flag indicating it's been called.
    original_callback_called = False

    @test_app.error
    def original_callback(*args):
        nonlocal original_callback_called
        original_callback_called = True

    test_app.settings['RETRY_CALLBACK'] = callback
    test_app.settings['RETRY_THRESHOLD'] = 0

    for cb in test_app._callbacks['error']:
        cb(test_app, {}, retry.RetryableException())

    assert original_callback_called


def test_callback_exceeds_timeout(test_app, callback):
    """Test that callback doesn't run when the timeout is exceeded."""
    # Create a function that sets a flag indicating it's been called.
    original_callback_called = False

    @test_app.error
    def original_callback(*args):
        nonlocal original_callback_called
        original_callback_called = True

    test_app.settings['RETRY_CALLBACK'] = callback
    test_app.settings['RETRY_TIMEOUT'] = 0

    for cb in test_app._callbacks['error']:
        cb(test_app, {}, retry.RetryableException())

    assert original_callback_called


def test_callback_prevents_others(test_app, callback):
    """Test that the callback blocks other callbacks."""
    test_app.settings['RETRY_CALLBACK'] = callback
    retry.Retry(test_app)

    with pytest.raises(Abort):
        for cb in test_app._callbacks['error']:
            cb(test_app, {}, retry.RetryableException())


@pytest.mark.skip(reason='delay not implemented')
def test_delay(monkeypatch, test_app, callback):
    """Test that retry delays."""
    sleep_called = False

    test_app.settings['RETRY_CALLBACK'] = callback
    test_app.settings['RETRY_DELAY'] = 1
    retry.Retry(test_app)

    with suppress(Abort):
        retry._retry(test_app, {}, retry.RetryableException())

    assert sleep_called
