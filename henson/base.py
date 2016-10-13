"""Implementation of the service."""

from copy import deepcopy
import logging
import sys
import traceback

from .config import Config
from .exceptions import Abort

__all__ = ('Application',)


class Application:
    """A service application.

    Each message received from the consumer will be passed to the
    callback.

    Args:
        name (str): The name of the application.
        settings (Optional[object]): An object with attributed-based
            settings.
        consumer (optional): Any object that is an iterator or an
            iterable and yields instances of any type that is supported
            by ``callback``. While this isn't required, it must be
            provided before the application can be run.
        callback (Optional[asyncio.coroutine]): A callable object that
            takes two arguments, an instance of
            :class:`henson.base.Application` and the (possibly)
            preprocessed incoming message.  While this isn't required,
            it must be provided before the application can be run.
    """

    def __init__(self, name, settings=None, *, consumer=None, callback=None):
        """Initialize the class."""
        self.name = name

        # Configuration
        self.settings = Config()
        self.settings.from_object(settings or {})
        self.settings.setdefault('DEBUG', False)
        self.settings.setdefault('SLEEP_TIME', 0.1)

        # Callbacks
        self.callback = callback
        self._callbacks = {
            'error': [],
            'message_acknowledgement': [],
            'message_preprocessor': [],
            'result_postprocessor': [],
            'startup': [],
            'teardown': [],
        }

        self.extensions = {}

        self.consumer = consumer

        self.logger = logging.getLogger(self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Application: {}>'.format(self)

    def error(self, callback):
        """Register an error callback.

        Args:
            callback (asyncio.coroutine): A callable object that takes
                three arguments: an instance of
                :class:`henson.base.Application`, the incoming message,
                and the exception that was raised. It will be called any
                time there is an exception while reading a message from
                the queue.

        Returns:
            asyncio.coroutine: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'error')
        return callback

    def message_acknowledgement(self, callback):
        """Register a message acknowledgement callback.

        Args:
            callback (asyncio.coroutine): A callable object that takes
                two arguments: an instance of
                :class:`henson.base.Application` and the original
                incoming message as its only argument. It will be called
                once a message has been fully processed.

        Returns:
            asyncio.coroutine: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'message_acknowledgement')
        return callback

    def message_preprocessor(self, callback):
        """Register a message preprocessing callback.

        Args:
            callback (asyncio.coroutine): A callable object that takes
                two arguments: an instance of
                :class:`henson.base.Application` and the incoming
                message. It will be called for each incoming message
                with its result being passed to ``callback``.

        Returns:
            asyncio.coroutine: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'message_preprocessor')
        return callback

    def result_postprocessor(self, callback):
        """Register a result postprocessing callback.

        Args:
            callback (asyncio.coroutine): A callable object that takes
                two arguments: an instance of
                :class:`henson.base.Application` and a result of
                processing the incoming message. It will be called for
                each result returned from ``callback``.

        Returns:
            asyncio.coroutine: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'result_postprocessor')
        return callback

    def run_forever(self, debug=False):
        """Consume from the consumer until interrupted.

        Args:
            num_workers (Optional[int]): The number of asynchronous
                tasks to use to process messages received through the
                consumer.  Defaults to 1.

        Raises:
            TypeError: If the consumer is None or the callback isn't
                callable.

        .. versionchanged:: 1.2

            Unhandled exceptions resulting from processing a message
            while the consumer is still active will stop cause the
            application to shut down gracefully.
        """
        if self.consumer is None:
            raise TypeError("The Application's consumer cannot be None.")

        if not callable(self.callback):
            raise TypeError("The Application's callback must be callable.")

        for callback in self._callbacks['startup']:
            callback(self)

        # The following debug mode checks are intentionally separate.
        if debug:
            # Set the application's debug mode to true if run_forever
            # was called with debug enabled.
            self.settings['DEBUG'] = True
        if self.settings['DEBUG']:
            # If the application is running in debug mode, enable it for
            # the loop and set the logger to DEBUG. If, however, the
            # log level was set to something lower than DEBUG, don't
            # change it.
            self.logger.setLevel(min(self.logger.level, logging.DEBUG))

        self.logger.debug('application.started')

        try:
            # Run the loop until the consumer says to stop.
            while True:
                self._process()
        except BaseException as e:
            self.logger.error(e)
        finally:
            # Teardown
            for callback in self._callbacks['teardown']:
                callback(self)

        self.logger.debug('application.stopped')

    def startup(self, callback):
        """Register a startup callback.

        Args:
            callback (asyncio.coroutine): A callable object that takes
                an instance of :class:`~henson.base.Application` as its
                only argument. It will be called once when the
                application first starts up.

        Returns:
            asyncio.coroutine: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'startup')
        return callback

    def teardown(self, callback):
        """Register a teardown callback.

        Args:
            callback (asyncio.coroutine): A callable object that takes
                an instance of :class:`~henson.base.Application` as its
                only argument. It will be called once when the
                application is shutting down.

        Returns:
            asyncio.coroutine: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'teardown')
        return callback

    def _abort(self, exc):
        """Log the aborted message.

        Args:
            exc (henson.exceptions.Abort): The exception to be logged.
        """
        tb = sys.exc_info()[-1]
        stack = traceback.extract_tb(tb, 1)[-1]
        self.logger.debug('callback.aborted', extra={
            'exception': exc,
            'exception_message': exc.message,
            'aborted_by': stack,
        })

    def _apply_callbacks(self, callbacks, value):
        """Apply callbacks to a set of arguments.

        The callbacks will be called in the order in which they are
        specified, with the return value of each being passed to the
        next callback.

        Args:
            callbacks (List[callable]): The callbacks to apply to the
                provided arguments.
            value: The value to pass to the first callback.

        Returns:
            The return value of the final callback.
        """
        for callback in callbacks:
            value = callback(self, value)
        return value

    def _process(self):
        """Process incoming messages."""
        message = self.consumer.read()
        # Save a copy of the original message in case its needed
        # later.
        original_message = deepcopy(message)

        try:
            message = self._apply_callbacks(
                self._callbacks['message_preprocessor'], message)
            self.logger.debug('message.preprocessed')

            results = self.callback(self, message)
        except Abort as e:
            self._abort(e)
        except Exception as e:
            self.logger.error('message.failed', exc_info=sys.exc_info())

            for callback in self._callbacks['error']:
                # Any callback can prevent execution of further
                # callbacks by raising Abort.
                try:
                    callback(self, message, e)
                except Abort:
                    break
        else:
            self._postprocess_results(results)
        finally:
            # Don't use _apply_callbacks here since we want to pass
            # the original message into each callback.
            for callback in self._callbacks['message_acknowledgement']:
                callback(self, original_message)
            self.logger.debug('message.acknowledged')

    def _postprocess_results(self, results):
        """Postprocess the results.

        Args:
            results (iterable): The results returned by processing the
                message.
        """
        if results is None:
            return

        for result in results:
            try:
                self._apply_callbacks(
                    self._callbacks['result_postprocessor'], result)
                self.logger.debug('result.postprocessed')
            except Abort as e:
                self._abort(e)

    def _register_callback(self, callback, callback_container):
        """Register a callback.

        Args:
            callback (asyncio.coroutine): The callback to register.
            callback_container (str): The name of the container onto
                which to append the callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        if not callable(callback):
            raise TypeError('The callback must be callable.')

        self._callbacks[callback_container].append(callback)

        self.logger.debug('callback.registered', extra={
            'type': callback_container,
            'callback': callback.__qualname__,
        })

    def _teardown(self, future, loop):
        """Tear down the application."""
        for callback in self._callbacks['teardown']:
            callback(self)
