"""Test for henson.contrib.retry."""

import asyncio
from contextlib import suppress
import time
from typing import Coroutine, Sequence

import pytest

from henson import Application
from henson.contrib import retry
from henson.exceptions import Abort


class TestRetryParentException(Exception):
    # Avoid PytestCollection Warning
    # https://github.com/pytest-dev/pytest/issues/6154#issuecomment-684769524
    __test__ = False
class TestRetryChildAException(TestRetryParentException):
    pass
class TestRetryChildBException(TestRetryParentException):
    pass
class TestRetryGrandchildException(TestRetryChildAException):
    pass

class TestRetryRedHerringException(Exception):
    # Avoid PytestCollection Warning
    # https://github.com/pytest-dev/pytest/issues/6154#issuecomment-684769524
    __test__ = False


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
    (10, None, False),  # 10 seconds ago
    # Don't retry.
    (0, 0, True),
    (10, 0, True),
    # Retry.
    (1, 10, False),
    (10, 20, False),
])
def test_exceeded_timeout(offset, duration, expected):
    """Test _exceeded_timeout."""
    start_time = int(time.time()) - offset
    actual = retry._exceeded_timeout(start_time, duration)
    assert actual == expected


def test_callback_insertion(test_app, coroutine):
    """Test that the callback is properly registered."""
    # Add an error callback before registering Retry.
    @test_app.error
    async def original_callback(*args):
        pass

    # Register Retry.
    test_app.settings['RETRY_CALLBACK'] = coroutine
    retry.Retry(test_app)

    assert test_app._callbacks['error'][0] is retry._retry


@pytest.mark.asyncio
async def test_callback_exceeds_threshold(test_app, coroutine):
    """Test that callback doesn't run when the threshold is exceeded."""
    # Create a function that sets a flag indicating it's been called.
    original_callback_called = False

    @test_app.error
    async def original_callback(*args):
        nonlocal original_callback_called
        original_callback_called = True

    test_app.settings['RETRY_CALLBACK'] = coroutine
    test_app.settings['RETRY_THRESHOLD'] = 0

    for cb in test_app._callbacks['error']:
        await cb(test_app, {}, retry.RetryableException())

    assert original_callback_called


@pytest.mark.asyncio
async def test_callback_exceeds_timeout(test_app, coroutine):
    """Test that callback doesn't run when the timeout is exceeded."""
    # Create a function that sets a flag indicating it's been called.
    original_callback_called = False

    @test_app.error
    async def original_callback(*args):
        nonlocal original_callback_called
        original_callback_called = True

    test_app.settings['RETRY_CALLBACK'] = coroutine
    test_app.settings['RETRY_TIMEOUT'] = 0

    for cb in test_app._callbacks['error']:
        await cb(test_app, {}, retry.RetryableException())

    assert original_callback_called


@pytest.mark.asyncio
async def test_callback_prevents_others(test_app, coroutine):
    """Test that the callback blocks other callbacks."""
    test_app.settings['RETRY_CALLBACK'] = coroutine
    retry.Retry(test_app)

    with pytest.raises(Abort):
        for cb in test_app._callbacks['error']:
            await cb(test_app, {}, retry.RetryableException())


@pytest.mark.asyncio
async def test_delay(monkeypatch, test_app, coroutine):
    """Test that retry delays."""
    sleep_called = False

    test_app.settings['RETRY_CALLBACK'] = coroutine
    test_app.settings['RETRY_DELAY'] = 1
    retry.Retry(test_app)

    async def sleep(duration):
        nonlocal sleep_called
        sleep_called = True

    monkeypatch.setattr(asyncio, 'sleep', sleep)

    with suppress(Abort):
        await retry._retry(test_app, {}, retry.RetryableException())

    assert sleep_called


@pytest.mark.parametrize('exception, backoff, callback, delay, threshold, timeout', (
    (IOError, 1.05, 'coroutine', 0, None, None),
    (FileNotFoundError, 1, 'coroutine', 0, None, 21600),
    (Abort, 1, 'coroutine', 0, 2, None),
    (retry.RetryableException, None, None, None, None, None),
))
@pytest.mark.asyncio
async def test_merge_override_settings(
    test_app, coroutine, exception, backoff, callback, delay, threshold, timeout, request
):
    """Test that overrides are working."""
    test_app.settings['RETRY_CALLBACK'] = coroutine
    test_app.settings['RETRY_EXCEPTIONS'] = (IOError, FileNotFoundError, Abort)
    test_app.settings['RETRY_OVERRIDES'] = {
        IOError : {
            'RETRY_BACKOFF': 1.05,
        },
        FileNotFoundError: {
            'RETRY_TIMEOUT': 21600, # 6 hours
        },
        Abort : {
            'RETRY_THRESHOLD': 2,
        },
        retry.RetryableException: {},
    }
    retry.Retry(test_app)

    # Check to see if the callback fixture exists, else, default to None
    try:
        callback_arg = request.getfixturevalue(callback)
    except pytest.FixtureLookupError:
        callback_arg = None

    assert test_app.settings['RETRY_OVERRIDES'][exception].get('RETRY_BACKOFF', None) == backoff
    assert test_app.settings['RETRY_OVERRIDES'][exception].get('RETRY_CALLBACK', None) == callback_arg
    assert test_app.settings['RETRY_OVERRIDES'][exception].get('RETRY_DELAY', None) == delay
    assert test_app.settings['RETRY_OVERRIDES'][exception].get('RETRY_THRESHOLD', None) == threshold
    assert test_app.settings['RETRY_OVERRIDES'][exception].get('RETRY_TIMEOUT', None) == timeout

@pytest.mark.parametrize('exc, expected, excs', (
    (KeyError('test KeyError'), 1.1, (OSError, KeyError, Abort)),
    (Abort('test', {}), 1.1, (OSError, Abort)),

    # Confirm we can handle a single exception and not a tuple
    (OSError('test OSError'), 1.05, OSError), 
    
    # Test that inheritance is working properly
    (TestRetryChildAException(), 2.05, TestRetryParentException),
    (TestRetryGrandchildException(), 2.05, TestRetryParentException),
    (TestRetryChildBException(), 3.05, TestRetryParentException),
    (TestRetryRedHerringException(), 1.1, TestRetryParentException)
))
@pytest.mark.asyncio
async def test_get_settings(test_app: Application, coroutine: Coroutine, exc: Exception, excs, expected: bool):
    """Test that _get_settings is grabbing the proper settings working."""
    test_app.settings['RETRY_CALLBACK'] = coroutine
    test_app.settings['RETRY_BACKOFF'] = 1.1
    test_app.settings['RETRY_EXCEPTIONS'] = excs
    test_app.settings['RETRY_OVERRIDES'] = {
        OSError : {
            'RETRY_BACKOFF': 1.05,
        },
        TestRetryChildAException: {
            'RETRY_BACKOFF': 2.05,
        },
        TestRetryGrandchildException: {},
        TestRetryChildBException: {
            'RETRY_BACKOFF': 3.05,
        },
    }
    retry.Retry(test_app)

    assert retry._get_settings(test_app, exc)['RETRY_BACKOFF'] == expected
