"""Implementation of Application using threading."""

from multiprocessing.pool import ThreadPool

from .base import PooledApplication


class Application(PooledApplication):
    Pool = ThreadPool
