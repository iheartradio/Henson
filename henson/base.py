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
        callback (Optional[Coroutine[[Application, Any]]]): A callable
            object that will be called for each (possibly) preprocessed
            incoming message. While it isn't required, it must be
            provided before the application can be run.
    """

    _callback_validator = callable
    _callback_validator_message = 'The callback must be callable.'

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
            callback (Callable[[Application, Any, Exception]]): A
                callable object that will be called any time there is an
                exception while processing a message from the queue.

        Returns:
            Callable[[Application, Any, Exception]]: The callback.

        Raises:
            TypeError: If the callback isn't callable.
        """
        self._register_callback(callback, 'error')
        return callback

    def message_acknowledgement(self, callback):
        """Register a message acknowledgement callback.

        Args:
            callback (Callable[[Application, Any]]): A callable object
                that will be called once a message has been fully
                processed.

        Returns:
            Callable[[Application, Any]]: The callback.

        Raises:
            TypeError: If the callback isn't callable.
        """
        self._register_callback(callback, 'message_acknowledgement')
        return callback

    def message_preprocessor(self, callback):
        """Register a message preprocessing callback.

        Args:
            callback (Callable[[Application, Any]]): A callable object
                that will be called for each incoming message with its
                result being passed to ``callback``.

        Returns:
            Callable[[Application, Any]]: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'message_preprocessor')
        return callback

    def result_postprocessor(self, callback):
        """Register a result postprocessing callback.

        Args:
            callback (Callable[[Application, Any]]): A callable object
                that will be called for each result returned from
                ``callback``.

        Returns:
            Callable[[Application, Any]]: The callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        self._register_callback(callback, 'result_postprocessor')
        return callback

    def run_forever(self, debug=False, num_workers=None):
        """Consume from the consumer until interrupted.

        Args:
            debug (Optional[bool]): Whether or not to run with debug
                mode enabled. Defaults to True.

        Raises:
            TypeError: If the consumer is None or the callback isn't a
                coroutine.
        """
        if self.consumer is None:
            raise TypeError("The Application's consumer cannot be None.")

        if not self._callback_validator(self.callback):
            raise TypeError(self._callback_validator_message)

        if debug:
            # Set the application's debug mode to true if run_forever
            # was called with debug enabled.
            self.settings['DEBUG'] = True
        if self.settings['DEBUG']:
            self.logger.setLevel(min(self.logger.level, logging.DEBUG))

        for callback in self._callbacks['startup']:
            callback(self)

        self.logger.debug('application.started')

        while True:
            try:
                value = self.consumer.read()
            except Abort:
                self.logger.debug('consumer.aborted')
                break

            self._process(value)

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
            value = yield from callback(self, value)
        return value

    def _process(self, message):
        original_message = deepcopy(message)

        try:
            for callback in self._callbacks['message_preprocessor']:
                message = callback(self, message)
            if self._callbacks['message_preprocessor']:
                self.logger.debug('message.preprocessed')

            results = self.callback(self, message)

            if not (results and self._callbacks['result_postprocessor']):
                return

            for result in results:
                try:
                    for callback in self._callbacks['result_postprocessor']:
                        result = callback(self, result)
                except Abort as e:
                    self._abort(e)
                self.logger.debug('result.postprocessed')
        except Abort as e:
            self._abort(e)
        except Exception as e:
            self.logger.error('message.failed', exc_info=sys.exc_info())

            for callback in self._callbacks['error']:
                try:
                    callback(self, message, e)
                except Abort:
                    break
        finally:
            for callback in self._callbacks['message_acknowledgement']:
                callback(self, original_message)
            if self._callbacks['message_acknowledgement']:
                self.logger.debug('message.acknowledged')

    def _register_callback(self, callback, callback_container):
        """Register a callback.

        Args:
            callback (asyncio.coroutine): The callback to register.
            callback_container (str): The name of the container onto
                which to append the callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        if not self._callback_validator(callback):
            raise TypeError(self._callback_validator_message)

        self._callbacks[callback_container].append(callback)

        self.logger.debug('callback.registered', extra={
            'type': callback_container,
            'callback': callback.__qualname__,
        })


class PooledApplication(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run_forever(self, num_workers=None, debug=False):
        """Run forever."""
        if num_workers == 0:
            num_workers = None

        if debug:
            self.settings['DEBUG'] = True
        if self.settings['DEBUG']:
            self.logger.setLevel(
                min(self.logger.getEffectiveLevel(), logging.DEBUG))

        for callback in self._callbacks['startup']:
            callback(self)

        self.logger.debug('application.started')

        with self.Pool(processes=num_workers) as pool:
            self._consume(pool)
            pool.close()
            pool.join()

        for callback in self._callbacks['teardown']:
            callback(self)

        self.logger.debug('application.stopped')

    def _consume(self, pool):
        while True:
            try:
                value = self.consumer.read()
            except Abort:
                self.logger.debug('consumer.aborted')
                return
            else:
                pool.apply_async(self._process, args=(value,))
