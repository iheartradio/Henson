"""Test Henson's exceptions."""

import asyncio

from henson import exceptions
from henson.base import Application


def test_abort_preprocessor(event_loop, cancelled_future, queue):
    """Test that aborted preprocessors stop execution."""
    # This test sets up two preprocessors, a callback, and a
    # postprocessor. The first preprocessor will raise an Abort
    # exception. None of the others should be called.
    preprocess1_called = False
    preprocess2_called = False
    callback_called = False
    postprocess_called = False

    queue.put_nowait({'a': 1})

    @asyncio.coroutine
    def callback(app, message):
        nonlocal callback_called
        callback_called = True
        return message

    app = Application('testing', callback=callback)

    @app.message_preprocessor
    @asyncio.coroutine
    def preprocess1(app, message):
        nonlocal preprocess1_called
        preprocess1_called = True
        raise exceptions.Abort('testing', message)

    @app.message_preprocessor
    @asyncio.coroutine
    def preprocess2(app, message):
        nonlocal preprocess2_called
        preprocess2_called = True
        return message

    @app.result_postprocessor
    @asyncio.coroutine
    def postprocess(app, result):
        nonlocal postprocess_called
        postprocess_called = True
        return result

    event_loop.run_until_complete(
        app._process(cancelled_future, queue, event_loop))

    assert preprocess1_called
    assert not preprocess2_called
    assert not callback_called
    assert not postprocess_called


def test_abort_callback(event_loop, cancelled_future, queue):
    """Test that aborted callbacks stop execution."""
    # This test sets up a callback and a postprocessor. The callback
    # will raise an Abort exception. The postprocessor shouldn't be
    # called.
    callback_called = False
    postprocess_called = False

    queue.put_nowait({'a': 1})

    @asyncio.coroutine
    def callback(app, message):
        nonlocal callback_called
        callback_called = True
        raise exceptions.Abort('testing', message)

    app = Application('testing', callback=callback)

    @app.result_postprocessor
    @asyncio.coroutine
    def postprocess(app, result):
        nonlocal postprocess_called
        postprocess_called = True
        return result

    event_loop.run_until_complete(
        app._process(cancelled_future, queue, event_loop))

    assert callback_called
    assert not postprocess_called


def test_abort_error(event_loop, cancelled_future, queue):
    """Test that aborted error callbacks stop execution."""
    # This test sets up a callback and two error callbacks. The callback
    # will raise an exception and the first error callback will an raise
    # Abort exception. The second error callback shouldn't be called.
    callback_called = False
    error1_called = False
    error2_called = False

    queue.put_nowait({'a': 1})

    @asyncio.coroutine
    def callback(app, message):
        nonlocal callback_called
        callback_called = True
        raise TypeError('testing')

    app = Application('testing', callback=callback)

    @app.error
    @asyncio.coroutine
    def error1(app, message, exc):
        nonlocal error1_called
        error1_called = True
        raise exceptions.Abort('testing', message)

    @app.error
    @asyncio.coroutine
    def error2(app, message, exc):
        nonlocal error2_called
        error2_called = True

    event_loop.run_until_complete(
        app._process(cancelled_future, queue, event_loop))

    assert callback_called
    assert error1_called
    assert not error2_called


def test_abort_postprocess(event_loop, cancelled_future, queue):
    """Test that aborted postprocessors stop execution of the result."""
    # This test sets up a callback and two postprocessors. The first
    # will raise an Abort exception for one of the two results returned
    # by the callback.
    postprocess1_called_count = 0
    postprocess2_called_count = 0

    queue.put_nowait({'a': 1})

    @asyncio.coroutine
    def callback(app, message):
        return [True, False]

    app = Application('testing', callback=callback)

    @app.result_postprocessor
    @asyncio.coroutine
    def postprocess1(app, result):
        nonlocal postprocess1_called_count
        postprocess1_called_count += 1
        if result:
            raise exceptions.Abort('testing', result)
        return result

    @app.result_postprocessor
    @asyncio.coroutine
    def postprocess2(app, result):
        nonlocal postprocess2_called_count
        postprocess2_called_count += 1
        return result

    event_loop.run_until_complete(
        app._process(cancelled_future, queue, event_loop))

    assert postprocess1_called_count == 2
    assert postprocess2_called_count == 1
