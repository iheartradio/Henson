"""Retry plugin for Henson.

Retry is a plugin to add the ability for Henson to automatically retry
messages that fail to process.

.. versionadded:: 0.4.0
"""

import time

from henson.extensions import Extension

__all__ = ('Retry', 'RetryableException')


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

    # Duration is in seconds, not milliseconds like start_time.
    return start_time + (duration * 1000) <= int(time.time())


def _retry(app, message, exc):
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
        StopIteration: If the message is scheduled to be retried.
    """
    if not isinstance(exc, app.settings['RETRY_EXCEPTIONS']):
        # If the exception raised isn't retryable, return control so the
        # next error callback can be called.
        return

    retry_info = _retry_info(message)

    threshold = app.settings['RETRY_THRESHOLD']
    if _exceeded_threshold(retry_info['count'], threshold):
        # If we've exceeded the number of times to retry the message,
        # don't retry it again.
        return

    timeout = app.settings['RETRY_TIMEOUT']
    if _exceeded_timeout(retry_info['start_time'], timeout):
        # If we've gone past the time to stop retrying, don't retry it
        # again.
        return

    retry_info['count'] += 1
    message['_retry'] = retry_info

    # TODO: Incorporate delay and backoff.
    # Retry the message.
    app.settings['RETRY_CALLBACK'](app, message)

    # If the exception was retryable, none of the other callbacks should
    # execute.
    raise StopIteration


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


class RetryableException(Exception):
    """Exception to be raised when a message should be retried."""


class Retry(Extension):
    """A class that adds retries to an application."""

    DEFAULT_SETTINGS = {
        'RETRY_BACKOFF': False,
        'RETRY_DELAY': 0,
        'RETRY_EXCEPTIONS': RetryableException,
        'RETRY_THRESHOLD': None,
        'RETRY_TIMEOUT': None,
    }

    REQUIRED_SETTINGS = (
        'RETRY_CALLBACK',
    )

    def init_app(self, app):
        """Initialize an ``Application`` instance.

        Args:
            app (henson.base.Application): Application instance to be
                initialized.
        """
        super().init_app(app)

        if not callable(app.settings['RETRY_CALLBACK']):
            raise TypeError('The retry callback is not callable.')

        # The retry callback should be executed before all other
        # callbacks. This will ensure that retryable exceptions are
        # retried.
        app.error_callbacks.insert(0, _retry)
