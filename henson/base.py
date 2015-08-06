"""Implementation of the service."""

import logging
import sys

from .config import Config

__all__ = ('Application',)


class Application:

    """A service application.

    Each message received from the consumer will be passed to the
    callback.

    Args:
        name (str): The name of the application.
        settings (object, optional): An object with attributed-based
          settings.
        consumer (optional): Any object that is an iterator or an
          iterable and yields instances of any type that is supported by
          ``callback``. While this isn't required, it must be provided
          before the application can be run.
        callback (callable, optional): A callable object that takes two
          arguments, an instance of this class and the incoming message.
          While this isn't required, it must be prodivded before the
          application can be run.
        error_callback (callable, optional): A callable object that
          takes two arguments, an instance of this class and the
          incoming message. This callback will be called any time there
          is an exception while reading a message from the queue.
        logger (:class:`~logging.RootLogger`, optional): A logger object
          to be associated with the application. If none is provided,
          the return value of :func:`~logging.getLogger` will be used.
    """

    def __init__(self, name, settings=None, *, consumer=None, callback=None,
                 error_callback=None, logger=None):
        """Initialize the class."""
        self.name = name
        self.settings = Config()
        self.settings.from_object(settings or {})
        self.callback = callback
        self.error_callback = error_callback
        self._logger = logger
        self._messages = None

        self.consumer = consumer

    @property
    def messages(self):
        """Return an iterator for the consumer.

        Raises:
            TypeError: If the consumer is None.
        """
        if self._messages is None:
            if self.consumer is None:
                raise TypeError('The consumer cannot be None.')
            self._messages = iter(self.consumer)
        return self._messages

    @property
    def logger(self):
        """Return the application's logger."""
        if not self._logger:
            self._logger = logging.getLogger(self.name)
        return self._logger

    def process_message(self):
        """Process a single message."""
        logger = self.logger

        try:
            message = next(self.messages)
        except StopIteration:
            # If there are no messages left, simply continue processing
            pass
        except BaseException:
            logger.error('message.failed', exc_info=sys.exc_info())
            if self.error_callback:
                self.error_callback(self, message)
        else:
            logger.info('message.received')
            self.callback(self, message)

    def run_forever(self):
        """Consume from the consumer until interrupted.

        Raises:
            TypeError: If the consumer is None or the callback isn't
              callable.
        """
        if not callable(self.callback):
            raise TypeError('The specified callback is not callable.')

        logger = self.logger

        logger.info('application.started')

        while True:
            try:
                self.process_message()
            except KeyboardInterrupt:
                break

        logger.info('application.stopped')
