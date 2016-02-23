"""Implementation of the service."""

import asyncio
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

        self.consumer = consumer

        self.logger = logging.getLogger(self.name)

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

    def run_forever(self, num_workers=1, loop=None, debug=False):
        """Consume from the consumer until interrupted.

        Args:
            num_workers (Optional[int]): The number of asynchronous
                tasks to use to process messages received through the
                consumer.  Defaults to 1.
            loop (Optional[asyncio.asyncio.BaseEventLoop]): An event
                loop that, if provided, will be used for running the
                application. If none is provided, the default event loop
                will be used.
            debug (Optional[bool]): Whether or not to run with debug
                mode enabled. Defaults to True.

        Raises:
            TypeError: If the consumer is None or the callback isn't a
                coroutine.
        """
        if self.consumer is None:
            raise TypeError("The Application's consumer cannot be None.")

        if not asyncio.iscoroutinefunction(self.callback):
            raise TypeError("The Application's callback must be a coroutine.")

        # Use the specified event loop, otherwise use the default one.
        loop = loop or asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

        # Start the application.
        tasks = [
            asyncio.async(callback(self), loop=loop) for callback in
            self._callbacks['startup']
        ]
        future = asyncio.gather(*tasks, loop=loop)
        loop.run_until_complete(future)

        # The following debug mode checks are intentionally separate.
        # Using a check of `if debug or self.settings['DEBUG']` would
        # accomplish the same thing but wouldn't respect the
        # PYTHONASYNCIODEBUG environment variable.
        if debug:
            # Set the application's debug mode to true if run_forever
            # was called with debug enabled.
            self.settings['DEBUG'] = True
        if self.settings['DEBUG']:
            # If the application is running in debug mode, enable it for
            # the loop and set the logger to DEBUG.
            loop.set_debug(True)
            self.logger.setLevel(logging.DEBUG)

        self.logger.info('application.started')

        # Create an asynchronous queue to pass the messages from the
        # consumer to the processor. The queue should hold one message
        # for each processing task.
        queue = asyncio.Queue(maxsize=num_workers, loop=loop)

        # Create a future to control consumption and create a task for
        # the consumer to run in.
        consumer = asyncio.Future(loop=loop)
        loop.create_task(self._consume(queue, consumer))

        # Create tasks to process each message received by the
        # consumer and wrap them inside a future. When the loop stops
        # running it should be restarted and wait until the future is
        # done.
        tasks = [
            asyncio.async(self._process(consumer, queue, loop), loop=loop)
            for _ in range(num_workers)
        ]
        future = asyncio.gather(*tasks, loop=loop)

        try:
            # Run the loop until the consumer says to stop.
            loop.run_until_complete(consumer)
        except BaseException as e:
            self.logger.error(e)

            # If something went wrong, cancel the consumer. This will
            # alert the processors to stop once the queue is empty.
            consumer.cancel()
        finally:
            # Run the loop until the future completes. This will allow
            # the tasks to finish processing all of the messages in the
            # queue and then exit cleanly.
            loop.run_until_complete(future)

            # Check for any exceptions that may have been raised by the
            # tasks inside the future.
            exc = future.exception()
            if exc:
                self.logger.error(exc)

            # Teardown
            tasks = [
                asyncio.async(callback(self), loop=loop) for callback in
                self._callbacks['teardown']
            ]
            future = asyncio.gather(*tasks, loop=loop)
            loop.run_until_complete(future)

            # Clean up after ourselves.
            loop.close()

        self.logger.info('application.stopped')

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

    @asyncio.coroutine
    def _abort(self, exc):
        """Log the aborted message.

        Args:
            exc (henson.exceptions.Abort): The exception to be logged.
        """
        tb = sys.exc_info()[-1]
        stack = traceback.extract_tb(tb, 1)[-1]
        self.logger.info('callback.aborted', extra={
            'exception': exc,
            'exception_message': exc.message,
            'aborted_by': stack,
        })

    @asyncio.coroutine
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

    @asyncio.coroutine
    def _consume(self, queue, future):
        """Read in incoming messages.

        Messages will be read from the consumer until it raises an
        :class:`~henson.exceptions.Abort` exception.

        Args:
            queue (asyncio.Queue): Any messages read in by the consumer
                will be added to the queue to share them with any future
                processing the messages.
            future (asyncio.Future): When the consumer tells the
                application to stop, this future will be cancelled.
        """
        while True:
            # Read messages and add them to the queue.
            try:
                value = yield from self.consumer.read()
            except Abort:
                self.logger.info('consumer.aborted')
                future.cancel()
                return
            except Exception as e:
                # If the consumer fails, set the exception on the future
                # so that the loop will stop running and the application
                # will shut down.
                future.set_exception(e)
            else:
                yield from queue.put(value)

    @asyncio.coroutine
    def _process(self, task, queue, loop):
        """Process incoming messages.

        Args:
            task (asyncio.tasks.Task): The task populating ``queue``.
              The function will exit when it's been cancelled.
            queue (asyncio.Queue): A queue containing incoming messages
              to be processed.
            loop (asyncio.asyncio.BaseEventLoop): The event loop used by
                the application.
        """
        while True:
            if queue.empty():
                # If there aren't any messages in the queue, check to
                # see if the consumer is done. If it is, exit.
                # Otherwise yield control back to the event loop and
                # then try again.
                if task.done():
                    break

                yield from asyncio.sleep(
                    self.settings['SLEEP_TIME'], loop=loop)
                continue

            message = yield from queue.get()
            # Save a copy of the original message in case its needed
            # later.
            original_message = deepcopy(message)

            try:
                message = yield from self._apply_callbacks(
                    self._callbacks['message_preprocessor'], message)
                self.logger.info('message.preprocessed')

                results = yield from self.callback(self, message)
            except Abort as e:
                yield from self._abort(e)
            except Exception as e:
                self.logger.error('message.failed', exc_info=sys.exc_info())

                for callback in self._callbacks['error']:
                    # Any callback can prevent execution of further
                    # callbacks by raising Abort.
                    try:
                        yield from callback(self, message, e)
                    except Abort:
                        break
            else:
                yield from self._postprocess_results(results)
            finally:
                # Don't use _apply_callbacks here since we want to pass
                # the original message into each callback.
                for callback in self._callbacks['message_acknowledgement']:
                    yield from callback(self, original_message)
                self.logger.info('message.acknowledged')

    @asyncio.coroutine
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
                yield from self._apply_callbacks(
                    self._callbacks['result_postprocessor'], result)
                self.logger.info('result.postprocessed')
            except Abort as e:
                yield from self._abort(e)

    def _register_callback(self, callback, callback_container):
        """Register a callback.

        Args:
            callback (asyncio.coroutine): The callback to register.
            callback_container (str): The name of the container onto
                which to append the callback.

        Raises:
            TypeError: If the callback isn't a coroutine.
        """
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError('The callback must be a coroutine.')

        self._callbacks[callback_container].append(callback)

        self.logger.info('callback.registered', extra={
            'type': callback_container,
            'callback': callback.__qualname__,
        })

    def _teardown(self, future, loop):
        """Tear down the application."""
        tasks = [
            asyncio.async(callback(self), loop=loop) for callback in
            self._callbacks['teardown']]
        future = asyncio.gather(*tasks, loop=loop)
        loop.run_until_complete(future)
