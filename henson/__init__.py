"""Henson."""

from pkg_resources import get_distribution

from .base import Application  # NOQA
from .extensions import Extension  # NOQA

__version__ = get_distribution(__package__).version
