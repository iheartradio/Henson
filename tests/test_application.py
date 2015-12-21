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


def test_consume(event_loop, test_consumer):
    """Test Application._consume."""
    queue = asyncio.Queue(maxsize=1)

    app = Application('testing', consumer=test_consumer)

    asyncio.async(app._consume(queue))

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
    with pytest.raises(TypeError) as e:
        app.run_forever()
    assert 'specified callback' in str(e.value).lower()


@pytest.mark.parametrize('error_callback', (None, '', False, 10, sum))
def test_error_callback_not_coroutine_typeerror(error_callback, coroutine):
    """Test TypeError is raised if error callback isn't a coroutine."""
    app = Application(
        'testing',
        consumer=[],
        callback=coroutine,
        error_callbacks=[error_callback],
    )
    with pytest.raises(TypeError) as e:
        app.run_forever()
    assert 'error callbacks' in str(e.value).lower()


@pytest.mark.parametrize('preprocess', (None, '', False, 10, sum))
def test_message_preprocessor_not_coroutine_typeerror(preprocess, coroutine):
    """Test TypeError is raised if preprocessor isn't a coroutine."""
    app = Application(
        'testing',
        consumer=[],
        callback=coroutine,
        message_preprocessors=[preprocess],
    )
    with pytest.raises(TypeError) as e:
        app.run_forever()
    assert 'message preprocessors' in str(e.value).lower()


@pytest.mark.asyncio
@pytest.mark.parametrize('original, expected', ((1, 2), (2, 3)))
def test_postprocess_results(original, expected):
    """Test Application._postprocess_results."""
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
        # Nothing is returned out of Application._postprocess_results so
        # the assertion needs to happen inside a callback.
        assert message == expected

    app = Application('testing', result_postprocessors=[callback1, callback2])

    yield from app._postprocess_results([original])

    assert callback1_called
    assert callback2_called


@pytest.mark.parametrize('postprocess', (None, '', False, 10, sum))
def test_result_postprocessor_not_coroutine_typeerror(postprocess, coroutine):
    """Test TypeError is raised if postprocessor isn't a coroutine."""
    app = Application(
        'testing',
        consumer=[],
        callback=coroutine,
        result_postprocessors=[postprocess],
    )
    with pytest.raises(TypeError) as e:
        app.run_forever()
    assert 'result postprocessors' in str(e.value).lower()


def test_run_forever(event_loop, test_consumer):
    """Test Application.run_forever."""
    preprocess_called = False
    callback_called = False
    postprocess_called = False

    @asyncio.coroutine
    def preprocess(app, message):
        nonlocal preprocess_called
        preprocess_called = True
        return message + 1

    @asyncio.coroutine
    def callback(app, message):
        nonlocal callback_called
        callback_called = True
        return [message + 1]

    @asyncio.coroutine
    def postprocess(app, result):
        nonlocal postprocess_called
        postprocess_called = True
        assert result == 3
        # Stop the event loop from running again.
        event_loop.stop()

    app = Application(
        'testing',
        consumer=test_consumer,
        callback=callback,
        message_preprocessors=[preprocess],
        result_postprocessors=[postprocess],
    )

    app.run_forever(loop=event_loop)

    assert preprocess_called
    assert callback_called
    assert postprocess_called
