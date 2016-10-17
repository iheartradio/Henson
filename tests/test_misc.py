"""Miscellaneous tests that don't have a better home."""

import asyncio
import asyncio.base_events
import sys

from henson.base import _new_event_loop


def test_new_event_loop(monkeypatch, request):
    """Test that _new_event_loop returns the default event loop."""
    policy = asyncio.get_event_loop_policy()

    def restore_event_loop_policy():
        asyncio.set_event_loop_policy(policy)
    request.addfinalizer(restore_event_loop_policy)

    asyncio.set_event_loop_policy(None)

    event_loop = _new_event_loop()
    assert isinstance(event_loop, asyncio.base_events.BaseEventLoop)


def test_new_event_loop_uvloop(monkeypatch, request):
    """Test that uvloop's event policy is used when its installed."""
    expected = 'event loop'

    # Inject the stub uvloop into the imported modules so that we don't
    # actually need to install it to run this test.
    class uvloop:
        @staticmethod
        def new_event_loop():
            return expected

    monkeypatch.setitem(sys.modules, 'uvloop', uvloop)

    actual = _new_event_loop()

    assert actual == expected
