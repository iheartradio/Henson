"""Retry plugin for Henson.

Retry is a plugin to add the ability for Henson to automatically retry
messages that fail to process.
"""

import asyncio
import time

import henson
from henson.config import Config
from henson.exceptions import Abort
from henson.extensions import Extension

__all__ = ('Retry', 'RetryableException')


def _calculate_delay(delay, backoff, number_of_retries):
    """Return the time to wait before retrying.

    Args:
        delay (numbers.Number): The base amount of time, in seconds, by
            which to delay the retry.
        backoff (numbers.Number): The factor by which each retry should
            be extended.
        number_of_retries (int): The number of retry attempts already
            made.

    Returns:
        numbers.Number: The amount of time to wait.

    """
    backoff_factor = backoff ** number_of_retries
    return delay * backoff_factor


def _exceeded_threshold(number_of_retries, maximum_retries):
    """Return True if the number of retries has been exceeded.

    Args:
        number_of_retries (int): The number of retry attempts made
            already.
        maximum_retries (int): The maximum number of retry attempts to
            make.

    Returns:
        bool: True if the maximum number of retry attempts have already
            been made.

    """
    if maximum_retries is None:
        # Retry forever.
        return False

    return number_of_retries >= maximum_retries


def _exceeded_timeout(start_time, duration):
    """Return True if the timeout has been exceeded.

    Args:
        start_time (int): The timestamp of the first retry attempt.
        duration (int): The total number of seconds to retry for.

    Returns:
        bool: True if the timeout has passed.

    """
    if duration is None:
        # Retry forever.
        return False

    return (start_time + duration) <= int(time.time())


async def _retry(app, message, exc):
    """Retry the message.

    An exception that is included as a retryable type will result in the
    message being retried so long as the threshold and timeout haven't
    been reached.

    Args:
        app (henson.base.Application): The current application.
        message (dict): The message to be retried.
        exc (Exception): The exception that caused processing the
            message to fail.

    Raises:
        Abort: If the message is scheduled to be retried.

    """
    if not isinstance(exc, app.settings['RETRY_EXCEPTIONS']):
        # If the exception raised isn't retryable, return control so the
        # next error callback can be called.
        return

    settings = _get_settings(app, exc)

    retry_info = _retry_info(message)

    threshold = settings['RETRY_THRESHOLD']
    if _exceeded_threshold(retry_info['count'], threshold):
        # If we've exceeded the number of times to retry the message,
        # don't retry it again.
        return

    timeout = settings['RETRY_TIMEOUT']
    if _exceeded_timeout(retry_info['start_time'], timeout):
        # If we've gone past the time to stop retrying, don't retry it
        # again.
        return

    if settings['RETRY_DELAY']:
        # If a delay has been specified, calculate the actual delay
        # based on any backoff and then sleep for that long. Add the
        # delay time to the retry information so that it can be used
        # to gain insight into the full history of a retried message.
        retry_info['delay'] = _calculate_delay(
            delay=settings['RETRY_DELAY'],
            backoff=settings['RETRY_BACKOFF'],
            number_of_retries=retry_info['count'],
        )
        await asyncio.sleep(retry_info['delay'])

    # Update the retry information and retry the message.
    retry_info['count'] += 1
    message['_retry'] = retry_info
    await settings['RETRY_CALLBACK'](app, message)

    # If the exception was retryable, none of the other callbacks should
    # execute.
    raise Abort('message.retried', message)


def _retry_info(message):
    """Return the retry attempt information.

    Args:
        message (dict): The message to be retried.

    Returns:
        dict: The retry attempt information.

    """
    info = message.get('_retry', {})
    info.setdefault('count', 0)
    info.setdefault('start_time', int(time.time()))
    return info


def _get_settings(app: henson.Application, exc: Exception) -> Config:
    """Get either normal or override settings."""
    for exc_key in tuple(app.settings['RETRY_OVERRIDES'].keys()):
        if isinstance(exc, exc_key):
            return app.settings['RETRY_OVERRIDES'][exc_key]
    return app.settings


class RetryableException(Exception):
    """Exception to be raised when a message should be retried."""


class Retry(Extension):
    """A class that adds retries to an application."""

    DEFAULT_SETTINGS = {
        'RETRY_BACKOFF': 1,
        'RETRY_DELAY': 0,
        'RETRY_EXCEPTIONS': RetryableException,
        'RETRY_THRESHOLD': None,
        'RETRY_TIMEOUT': None,
        'RETRY_OVERRIDES': {},
    }

    REQUIRED_SETTINGS = (
        'RETRY_CALLBACK',
    )

    def init_app(self, app):
        """Initialize an ``Application`` instance.

        Args:
            app (henson.base.Application): Application instance to be
                initialized.

        Raises:
            TypeError: If the callback isn't a coroutine.
            ValueError: If the delay or backoff is negative.

        """
        super().init_app(app)

        self._validate_settings(app.settings)

        # Merge overrides
        self._merge_override_settings(app)

        # The retry callback should be executed before all other
        # callbacks. This will ensure that retryable exceptions are
        # retried.
        app._callbacks['error'].insert(0, _retry)

    def _validate_settings(self, settings: Config) -> None:
        """Validate the settings.

        Raises:
            TypeError: If the callback isn't a coroutine.
            ValueError: If the delay or backoff is negative.

        """
        if settings['RETRY_DELAY'] < 0:
            raise ValueError('The delay cannot be negative.')

        if settings['RETRY_BACKOFF'] < 0:
            raise ValueError('The backoff cannot be negative.')

        if not asyncio.iscoroutinefunction(settings['RETRY_CALLBACK']):
            raise TypeError('The retry callback is not a coroutine.')

    def _merge_override_settings(self, app: henson.Application) -> None:
        """Merge base settings with override settings.

        Raises:
            TypeError: If the callback isn't a coroutine.
            ValueError: If the delay or backoff is negative.

        """
        override_settings = (
            'RETRY_BACKOFF',
            'RETRY_CALLBACK',
            'RETRY_DELAY',
            'RETRY_THRESHOLD',
            'RETRY_TIMEOUT',
        )
        default_settings = {}

        # Get the settings we want to merge with any override settings
        for setting in override_settings:
            default_settings[setting] = app.settings[setting]

        for exc, override_settings in app.settings[
            'RETRY_OVERRIDES'
        ].items():
            if issubclass(exc, (app.settings['RETRY_EXCEPTIONS'])):
                merged_settings = {**default_settings, **override_settings}
                self._validate_settings(merged_settings)
                app.settings['RETRY_OVERRIDES'][exc] = merged_settings
