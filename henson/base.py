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
          arguments, an instance of this class and the (possibly)
          preprocessed incoming message.  While this isn't required, it
          must be provided before the application can be run.
        error_callbacks (List[callable], optional): A list of callable
          objects that take three arguments: an instance of this class,
          the incoming message, and the exception that was raised. These
          callbacks will be called any time there is an exception while
          reading a message from the queue.
        message_preprocessors (List[callable], optional): A list of
          callable objects that take two arguments: an instance of this
          class and the incoming message. These callbacks will be called
          first for each incoming message and its return value will be
          passed to ``callback``.
        result_postprocessors (List[callable], optional): A list of
          callable objects that takes two arguments: an instance of this
          class and the each result of ``callback``.

    .. versionchanged:: 0.4.0
       The ``message_preprocessors`` and ``result_postprocessors``
       parameters have been added to optionally preprocess an incoming
       msesage and postprocess all results.
    """

    def __init__(self, name, settings=None, *, consumer=None, callback=None,
                 error_callbacks=None, message_preprocessors=None,
                 result_postprocessors=None):
        """Initialize the class."""
        self.name = name
        self.settings = Config()
        self.settings.from_object(settings or {})
        self.callback = callback
        self.error_callbacks = error_callbacks or []
        self.message_preprocessors = message_preprocessors or []
        self.result_postprocessors = result_postprocessors or []

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

        if not all(callable(cb) for cb in self.message_preprocessors):
            raise TypeError(
                'Message preprocessors must be callable.')

        if not all(callable(cb) for cb in self.result_postprocessors):
            raise TypeError(
                'Result postprocessors must be callable.')

        if not all(callable(cb) for cb in self.error_callbacks):
            raise TypeError(
                'Error callbacks must be callable.')

        self.logger.info('application.started')

        messages = iter(self.consumer)
        while True:
            try:
                message = next(messages)
            except BaseException:
                self.logger.error('message.failed', exc_info=sys.exc_info())
                break
            else:
                self.logger.info('message.received')

                for preprocess in self.message_preprocessors:
                    message = preprocess(self, message)
                    self.logger.info('message.preprocessed')

                try:
                    results = self.callback(self, message)
                except Exception as e:
                    self.logger.error(
                        'message.failed', exc_info=sys.exc_info())
                    for callback in self.error_callbacks:
                        # Any callback can prevent execution of further
                        # callbacks by raising StopIteration.
                        try:
                            callback(self, message, e)
                        except StopIteration:
                            break
                else:
                    if results is not None:
                        # TODO: Evaluate this further. What are the pros
                        # and cons of operating over multiple results
                        # versus keeping it just one. As we look into
                        # asyncio, there may be benefits to yielding
                        # from callback rather than returning.
                        for result in results:
                            for postprocess in self.result_postprocessors:
                                result = postprocess(self, result)
                                self.logger.info('result.postprocessed')

        self.logger.info('application.stopped')
