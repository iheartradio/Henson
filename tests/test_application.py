import asyncio
import pytest
import queue as sync_queue

from henson.base import Application
from henson.exceptions import Abort


@pytest.mark.asyncio
@pytest.mark.parametrize('original, expected, ASYNC_QUEUE', ((1, 4, True), (2, 6, True), (1, 4, False), (2, 6, False)))
def test_apply_callbacks(original, expected, ASYNC_QUEUE):
    """Test Application._apply_callbacks."""
    callback1_called = False
    callback2_called = False

    @asyncio.coroutine
    def callback1(app, message):
        nonlocal callback1_called
        callback1_called = True
        return message + 1

    @asyncio.coroutine
    def callback2(app, message):
        nonlocal callback2_called
        callback2_called = True
        return message * 2

    app = Application('testing', settings={'ASYNC_QUEUE': ASYNC_QUEUE})

    actual = yield from app._apply_callbacks([callback1, callback2], original)
    assert actual == expected

    assert callback1_called
    assert callback2_called


@pytest.mark.parametrize('ASYNC_QUEUE', (True, False))
def test_consume(event_loop, test_consumer, ASYNC_QUEUE):
    """Test Application._consume."""
    if ASYNC_QUEUE:
        queue = asyncio.Queue(maxsize=1)
    else:
        queue = sync_queue.Queue(maxsize=1)

    app = Application('testing', settings={
                      "ASYNC_QUEUE": ASYNC_QUEUE}, consumer=test_consumer)

    asyncio.ensure_future(app._consume(queue), loop=event_loop)

    event_loop.stop()  # Run the event loop once.
    event_loop.run_forever()

    # The size of the queue won't ever be larger than 1 because of the
    # maxsize argument.
    assert queue.qsize() == 1


@pytest.mark.parametrize('ASYNC_QUEUE', (True, False))
def test_consumer_aborts(event_loop, ASYNC_QUEUE):
    """Test that the application stops after the consumer aborts."""
    consumer_called = False
    callback_called = False

    class Consumer:
        @asyncio.coroutine
        def read(self):
            nonlocal consumer_called
            consumer_called = True
            raise Abort('reason', 'message')

    @asyncio.coroutine
    def callback(app, message):
        nonlocal callback_called
        callback_called = True
        while True:
            yield from asyncio.sleep(0)

    app = Application('testing', consumer=Consumer(), callback=callback,
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    app.run_forever(loop=event_loop)

    assert consumer_called
    assert not callback_called


@pytest.mark.parametrize('ASYNC_QUEUE', (True, False))
def test_consumer_exception(event_loop, ASYNC_QUEUE):
    """Test that the application stops after a consumer exception."""
    consumer_called = False
    callback_called = False

    class Consumer:
        @asyncio.coroutine
        def read(self):
            nonlocal consumer_called
            consumer_called = True
            raise Exception()

    @asyncio.coroutine
    def callback(app, message):
        nonlocal callback_called
        callback_called = True

    app = Application('testing', consumer=Consumer(), callback=callback,
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    app.run_forever(loop=event_loop)

    assert consumer_called
    assert not callback_called


@pytest.mark.parametrize('ASYNC_QUEUE', (True, False))
def test_consumer_is_none_typeerror(ASYNC_QUEUE):
    """Test TypeError is raised if the consumer is None."""
    app = Application('testing', consumer=None,
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.run_forever()


@pytest.mark.parametrize('callback, ASYNC_QUEUE', ((None, True), ('', True), (False, True), (10, True), (sum, True), (None, False), ('', False), (False, False), (10, False), (sum, False)))
def test_callback_not_coroutine_typerror(callback, ASYNC_QUEUE):
    """Test TypeError is raised if callback isn't a coroutine."""
    app = Application('testing', consumer=[], callback=callback,
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.run_forever()


@pytest.mark.parametrize('error_callback, ASYNC_QUEUE', ((None, True), ('', True), (False, True), (10, True), (sum, True), (None, False), ('', False), (False, False), (10, False), (sum, False)))
def test_error_not_coroutine_typeerror(error_callback, ASYNC_QUEUE):
    """Test TypeError is raised if error callback isn't a coroutine."""
    app = Application('testing',
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.error(error_callback)


@pytest.mark.parametrize('acknowledgement, ASYNC_QUEUE', ((None, True), ('', True), (False, True), (10, True), (sum, True), (None, False), ('', False), (False, False), (10, False), (sum, False)))
def test_message_acknowledgement_not_coroutine_typeerror(acknowledgement, ASYNC_QUEUE):
    """Test TypeError is raised if acknowledgement isn't a coroutine."""
    app = Application('testing',
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.message_acknowledgement(acknowledgement)


@pytest.mark.parametrize('ASYNC_QUEUE', (True, False))
def test_message_acknowledgement_original_message(event_loop, coroutine,
                                                  cancelled_future, queue, ASYNC_QUEUE):
    """Test that original message is acknowledged."""
    actual = ''

    expected = 'original'
    queue.put_nowait(expected)

    app = Application('testing', callback=coroutine,
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})

    @app.message_preprocessor
    @asyncio.coroutine
    def preprocess(app, message):
        return 'changed'

    @app.message_acknowledgement
    @asyncio.coroutine
    def acknowledge(app, message):
        nonlocal actual
        actual = message

    event_loop.run_until_complete(
        app._process(cancelled_future, queue, event_loop))

    assert actual == expected


@pytest.mark.parametrize('preprocess, ASYNC_QUEUE', ((None, True), ('', True), (False, True), (10, True), (sum, True), (None, False), ('', False), (False, False), (10, False), (sum, False)))
def test_message_preprocessor_not_coroutine_typeerror(preprocess, ASYNC_QUEUE):
    """Test TypeError is raised if preprocessor isn't a coroutine."""
    app = Application('testing',
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.message_preprocessor(preprocess)


@pytest.mark.asyncio
@pytest.mark.parametrize('original, expected, ASYNC_QUEUE', ((1, 2, True), (1, 2, False), (2, 3, True), (2, 3, False)))
def test_postprocess_results(original, expected, ASYNC_QUEUE):
    """Test Application._postprocess_results."""
    callback1_called = False
    callback2_called = False

    app = Application('testing',
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})

    @app.result_postprocessor
    @asyncio.coroutine
    def callback1(app, message):
        nonlocal callback1_called
        callback1_called = True
        return message + 1

    @app.result_postprocessor
    @asyncio.coroutine
    def callback2(app, message):
        nonlocal callback2_called
        callback2_called = True
        # Nothing is returned out of Application._postprocess_results so
        # the assertion needs to happen inside a callback.
        assert message == expected

    yield from app._postprocess_results([original])

    assert callback1_called
    assert callback2_called


@pytest.mark.parametrize('ASYNC_QUEUE', (True, False))
def test_process_exception_stops_application(event_loop, test_consumer, ASYNC_QUEUE):
    """Test that the application stops after a processing exception."""
    @asyncio.coroutine
    def callback(app, message):
        return [{}]

    app = Application('testing', consumer=test_consumer, callback=callback,
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})

    @app.result_postprocessor
    @asyncio.coroutine
    def postprocess(app, message):
        raise Exception()

    with pytest.raises(Exception):
        app.run_forever(loop=event_loop)


@pytest.mark.parametrize('postprocess, ASYNC_QUEUE', ((None, True), ('', True), (False, True), (10, True), (sum, True), (None, False), ('', False), (False, False), (10, False), (sum, False)))
def test_result_postprocessor_not_coroutine_typeerror(postprocess, ASYNC_QUEUE):
    """Test TypeError is raised if postprocessor isn't a coroutine."""
    app = Application('testing',
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.result_postprocessor(postprocess)


@pytest.mark.parametrize('startup, ASYNC_QUEUE', ((None, True), ('', True), (False, True), (10, True), (sum, True), (None, False), ('', False), (False, False), (10, False), (sum, False)))
def test_startup_not_coroutine_typeerror(startup, ASYNC_QUEUE):
    """Test TypeError is raised if startup isn't a coroutine."""
    app = Application('testing',
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.startup(startup)


@pytest.mark.parametrize('teardown, ASYNC_QUEUE', ((None, True), ('', True), (False, True), (10, True), (sum, True), (None, False), ('', False), (False, False), (10, False), (sum, False)))
def test_teardown_not_coroutine_typeerror(teardown, ASYNC_QUEUE):
    """Test TypeError is raised if teardown isn't a coroutine."""
    app = Application('testing',
                      settings={'ASYNC_QUEUE': ASYNC_QUEUE})
    with pytest.raises(TypeError):
        app.teardown(teardown)


@pytest.mark.parametrize('ASYNC_QUEUE', (True, False))
def test_run_forever(event_loop, test_consumer_with_abort, ASYNC_QUEUE):
    """Test Application.run_forever."""
    startup_called = False
    preprocess_called = False
    callback_called = False
    postprocess_called = False
    acknowledgement_called = False
    teardown_called = False

    @asyncio.coroutine
    def callback(app, message):
        nonlocal callback_called
        callback_called = True
        return [message + 1]

    app = Application(
        'testing',
        consumer=test_consumer_with_abort,
        callback=callback,
        settings={"ASYNC_QUEUE": ASYNC_QUEUE}
    )

    @app.startup
    @asyncio.coroutine
    def startup(app):
        nonlocal startup_called
        startup_called = True

    @app.message_preprocessor
    @asyncio.coroutine
    def preprocess(app, message):
        nonlocal preprocess_called
        preprocess_called = True
        return message + 1

    @app.result_postprocessor
    @asyncio.coroutine
    def postprocess(app, result):
        nonlocal postprocess_called
        postprocess_called = True

    @app.message_acknowledgement
    @asyncio.coroutine
    def acknowledge(app, message):
        nonlocal acknowledgement_called
        acknowledgement_called = True

    @app.teardown
    @asyncio.coroutine
    def teardown(app):
        nonlocal teardown_called
        teardown_called = True

    app.run_forever(loop=event_loop)

    assert startup_called
    assert preprocess_called
    assert callback_called
    assert postprocess_called
    assert acknowledgement_called
    assert teardown_called
