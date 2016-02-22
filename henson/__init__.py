"""Henson."""

import os as _os
import pkg_resources as _pkg_resources

from .base import Application  # NOQA
from .exceptions import Abort  # NOQA
from .extensions import Extension  # NOQA

try:
    _dist = _pkg_resources.get_distribution(__package__)
    if not __file__.startswith(_os.path.join(_dist.location, __package__)):
        # Manually raise the exception if there is a distribution but
        # it's installed from elsewhere.
        raise _pkg_resources.DistributionNotFound
except _pkg_resources.DistributionNotFound:
    __version__ = 'development'
else:
    __version__ = _dist.version
