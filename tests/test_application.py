"""Test Application."""

import asyncio

import pytest

from henson.base import Application


def test_consume(event_loop, test_consumer):
    """Test Application._consume."""
    queue = asyncio.Queue(maxsize=1)

    app = Application('testing', consumer=test_consumer)

    # Eventually stop the event loop so that we can check the contents
    # of the queue.
    def stop_loop():
        event_loop.stop()
    event_loop.call_soon(stop_loop)

    asyncio.async(app._consume(queue))

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
