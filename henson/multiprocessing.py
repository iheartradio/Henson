"""Implmentation of Application using multiprocessing."""

from multiprocessing import Pool

from .base import PooledApplication


class Application(PooledApplication):
    Pool = Pool
