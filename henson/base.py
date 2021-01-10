"""Implementation of the service."""

import asyncio
import queue as sync_queue
from contextlib import suppress
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
        self.settings.setdefault('ASYNC_QUEUE', True)

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
        """Return name of application."""
        return self.name

    def __repr__(self):
        """Return representation of name of application."""
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

        .. versionchanged:: 1.2

            Unhandled exceptions resulting from processing a message
            while the consumer is still active will stop cause the
            application to shut down gracefully.

        """
        if self.consumer is None:
            raise TypeError("The Application's consumer cannot be None.")

        if not asyncio.iscoroutinefunction(self.callback):
            raise TypeError("The Application's callback must be a coroutine.")

        # Use the specified event loop, otherwise use the default one.
        loop = loop or _new_event_loop()
        asyncio.set_event_loop(loop)

        # Start the application.
        tasks = [
            asyncio.ensure_future(callback(self)) for callback in
            self._callbacks['startup']
        ]
        future = asyncio.gather(*tasks)
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
            # the loop and set the logger to DEBUG. If, however, the
            # log level was set to something lower than DEBUG, don't
            # change it.
            loop.set_debug(True)
            self.logger.setLevel(
                min(self.logger.getEffectiveLevel(), logging.DEBUG)
            )

        self.logger.debug('application.started')

        # Create an asynchronous queue to pass the messages from the
        # consumer to the processor. The queue should hold one message
        # for each processing task.

        if self.settings['ASYNC_QUEUE']:
            queue = asyncio.Queue(maxsize=num_workers)
        else:
            queue = sync_queue.Queue()

        # Create a task to monitor the consumer.
        consumer = loop.create_task(self._consume(queue))

        # Create tasks to process each message received by the
        # consumer and wrap them inside a future. When the loop stops
        # running it should be restarted and wait until the future is
        # done.
        tasks = [
            asyncio.ensure_future(
                self._process(consumer, queue, loop),
            )
            for _ in range(num_workers)
        ]
        future = asyncio.gather(*tasks)

        try:
            # Run the loop until the consumer says to stop or message
            # processing fails.
            loop.run_until_complete(asyncio.gather(consumer, future))
        except BaseException as e:
            self.logger.error(e)
        finally:
            # If something went wrong while processing the message,
            # cancel the consumer. This will alert the processors to
            # stop once the queue is empty.
            consumer.cancel()

            # Run the loop until message processing completes. This will
            # allow the tasks to finish processing all of the messages
            # in the queue and then exit cleanly.
            loop.run_until_complete(future)

            # Check for any exceptions that may have been raised by the
            # tasks inside the future.
            exc = future.exception()
            if exc:
                self.logger.error(exc)

            # Teardown
            tasks = [
                asyncio.ensure_future(callback(self))
                for callback
                in self._callbacks['teardown']
            ]
            future = asyncio.gather(*tasks)
            loop.run_until_complete(future)

            # Clean up after ourselves.
            loop.close()

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

    async def _abort(self, exc):
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

    async def _apply_callbacks(self, callbacks, value):
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
            value = await callback(self, value)
        return value

    async def _consume(self, queue):
        """Read in incoming messages.

        Messages will be read from the consumer until it raises an
        :class:`~henson.exceptions.Abort` exception.

        Args:
            queue (asyncio.Queue): Any messages read in by the consumer
                will be added to the queue to share them with any future
                processing the messages.
        """
        while True:
            # Read messages and add them to the queue.
            try:
                value = await self.consumer.read()
            except Abort:
                self.logger.debug('consumer.aborted')
                return
            else:
                if self.settings["ASYNC_QUEUE"]:
                    await queue.put(value)
                else:
                    queue.put(value)

    async def _process(self, future, queue, loop):
        """Process incoming messages.

        Args:
            future (asyncio.Future): The future that, when done, will
                indicate that the consumer is no longer receiving new
                messages.
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
                if future.done():
                    break

                await asyncio.sleep(
                    self.settings['SLEEP_TIME'])
                continue

            if self.settings["ASYNC_QUEUE"]:
                message = await queue.get()
            else:
                message = queue.get()
            # Save a copy of the original message in case its needed
            # later.
            original_message = deepcopy(message)

            try:
                message = await self._apply_callbacks(
                    self._callbacks['message_preprocessor'], message)
                self.logger.debug('message.preprocessed')

                results = await self.callback(self, message)
            except Abort as e:
                await self._abort(e)
            except Exception as e:
                self.logger.error('message.failed', exc_info=sys.exc_info())

                for callback in self._callbacks['error']:
                    # Any callback can prevent execution of further
                    # callbacks by raising Abort.
                    try:
                        await callback(self, message, e)
                    except Abort:
                        break
            else:
                await self._postprocess_results(results)
            finally:
                # Don't use _apply_callbacks here since we want to pass
                # the original message into each callback.
                for callback in self._callbacks['message_acknowledgement']:
                    await callback(self, original_message)
                self.logger.debug('message.acknowledged')

                # If there are no new messages in the queue, _process
                # won't reassign the variables that it uses to track the
                # message and its results. This will cause the memory to
                # stay allocated longer than the application needs it.
                # By destroying the references to the objects that are
                # no longer needed, the memory can be freed up for other
                # things to use.
                with suppress(UnboundLocalError):
                    # If an exception was raised, results may not have
                    # been set.
                    del results
                del message
                del original_message

    async def _postprocess_results(self, results):
        """Postprocess the results.

        Args:
            results (iterable): The results returned by processing the
                message.
        """
        if results is None:
            return

        for result in results:
            try:
                await self._apply_callbacks(
                    self._callbacks['result_postprocessor'], result)
                self.logger.debug('result.postprocessed')
            except Abort as e:
                await self._abort(e)

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

        self.logger.debug('callback.registered', extra={
            'type': callback_container,
            'callback': callback.__qualname__,
        })

    def _teardown(self, future, loop):
        """Tear down the application."""
        tasks = [
            asyncio.ensure_future(callback(self)) for callback in
            self._callbacks['teardown']]
        future = asyncio.gather(*tasks)
        loop.run_until_complete(future)


def _new_event_loop():
    """Return a new event loop.

    If `uvloop <https://uvloop.readthedocs.io>`_ is installed, its event
    loop will be used. Otherwise, the default event loop provided by
    asyncio will be used. The latter behavior can be overridden by
    setting the event loop policy.

    Returns:
        asyncio.AbstractEventLoopPolicy: The new event loop.

    """
    try:
        import uvloop
    except ImportError:
        return asyncio.new_event_loop()
    else:
        return uvloop.new_event_loop()
