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
    """

    def __init__(self, name, settings=None, *, consumer=None, callback=None,
                 error_callback=None):
        """Initialize the class."""
        self.name = name
        self.settings = Config()
        self.settings.from_object(settings or {})
        self.callback = callback
        self.error_callback = error_callback

        self.consumer = consumer

        self.logger = logging.getLogger(self.name)

    def run_forever(self):
        """Consume from the consumer until interrupted.

        Raises:
            TypeError: If the consumer is None or the callback isn't
              callable.
        """
        if self.consumer is None:
            raise TypeError('The consumer cannot be None.')
        if not callable(self.callback):
            raise TypeError('The specified callback is not callable.')

        self.logger.info('application.started')

        messages = iter(self.consumer)
        while True:
            try:
                message = next(messages)
            except KeyboardInterrupt:
                break
            except StopIteration:
                continue
            except BaseException:
                self.logger.error('message.failed', exc_info=sys.exc_info())
                if self.error_callback:
                    self.error_callback(self, message)
            else:
                self.logger.info('message.received')
                self.callback(self, message)

        self.logger.info('application.stopped')
