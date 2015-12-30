"""Test Application."""

import asyncio

import pytest

from henson.base import Application


@pytest.mark.asyncio
@pytest.mark.parametrize('original, expected', ((1, 4), (2, 6)))
def test_apply_callbacks(original, expected):
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

    app = Application('testing')

    actual = yield from app._apply_callbacks([callback1, callback2], original)
    assert actual == expected

    assert callback1_called
    assert callback2_called


def test_consume(event_loop, test_consumer, cancelled_future):
    """Test Application._consume."""
    queue = asyncio.Queue(maxsize=1)

    app = Application('testing', consumer=test_consumer)

    asyncio.async(app._consume(queue, cancelled_future))

    event_loop.stop()  # Run the event loop once.
    event_loop.run_forever()

    # The size of the queue won't ever be larger than 1 because of the
    # maxsize argument.
    assert queue.qsize() == 1


def test_consumer_is_none_typeerror():
    """Test TypeError is raised if the consumer is None."""
    app = Application('testing', consumer=None)
    with pytest.raises(TypeError):
        app.run_forever()


@pytest.mark.parametrize('callback', (None, '', False, 10, sum))
def test_callback_not_coroutine_typerror(callback):
    """Test TypeError is raised if callback isn't a coroutine."""
    app = Application('testing', consumer=[], callback=callback)
    with pytest.raises(TypeError):
        app.run_forever()


@pytest.mark.parametrize('error_callback', (None, '', False, 10, sum))
def test_error_not_coroutine_typeerror(error_callback):
    """Test TypeError is raised if error callback isn't a coroutine."""
    app = Application('testing')
    with pytest.raises(TypeError):
        app.error(error_callback)


@pytest.mark.parametrize('acknowledgement', (None, '', False, 10, sum))
def test_message_acknowledgement_not_coroutine_typeerror(acknowledgement):
    """Test TypeError is raised if acknowledgement isn't a coroutine."""
    app = Application('testing')
    with pytest.raises(TypeError):
        app.message_acknowledgement(acknowledgement)


def test_message_acknowledgement_original_message(event_loop, coroutine,
                                                  cancelled_future, queue):
    """Test that original message is acknowledged."""
    actual = ''

    expected = 'original'
    queue.put_nowait(expected)

    app = Application('testing', callback=coroutine)

    @app.message_preprocessor
    @asyncio.coroutine
    def preprocess(app, message):
        return 'changed'

    @app.message_acknowledgement
    @asyncio.coroutine
    def acknowledge(app, message):
        nonlocal actual
        actual = message

    event_loop.run_until_complete(app._process(cancelled_future, queue))

    assert actual == expected


@pytest.mark.parametrize('preprocess', (None, '', False, 10, sum))
def test_message_preprocessor_not_coroutine_typeerror(preprocess):
    """Test TypeError is raised if preprocessor isn't a coroutine."""
    app = Application('testing')
    with pytest.raises(TypeError):
        app.message_preprocessor(preprocess)


@pytest.mark.asyncio
@pytest.mark.parametrize('original, expected', ((1, 2), (2, 3)))
def test_postprocess_results(original, expected):
    """Test Application._postprocess_results."""
    callback1_called = False
    callback2_called = False

    app = Application('testing')

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


@pytest.mark.parametrize('postprocess', (None, '', False, 10, sum))
def test_result_postprocessor_not_coroutine_typeerror(postprocess):
    """Test TypeError is raised if postprocessor isn't a coroutine."""
    app = Application('testing')
    with pytest.raises(TypeError):
        app.result_postprocessor(postprocess)


@pytest.mark.parametrize('startup', (None, '', False, 10, sum))
def test_startup_not_coroutine_typeerror(startup):
    """Test TypeError is raised if startup isn't a coroutine."""
    app = Application('testing')
    with pytest.raises(TypeError):
        app.startup(startup)


@pytest.mark.parametrize('teardown', (None, '', False, 10, sum))
def test_teardown_not_coroutine_typeerror(teardown):
    """Test TypeError is raised if teardown isn't a coroutine."""
    app = Application('testing')
    with pytest.raises(TypeError):
        app.teardown(teardown)


def test_run_forever(event_loop, test_consumer_with_abort):
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
