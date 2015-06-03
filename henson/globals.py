"""Global objects."""

from .base import registry as _registry
from .utils import ProxyObject


def _get_application():
    app = _registry.current_application
    if app is None:
        raise RuntimeError('No application instance has been registered.')
    return app


current_application = ProxyObject(_get_application)
