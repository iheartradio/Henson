from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    def finalize_options(self):
        super().finalize_options()
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


def read(filename):
    with open(filename) as f:
        return f.read()

setup(
    name='Henson',
    version='1.0.1',
    author='Andy Dirnberger, Jon Banafato, and others',
    author_email='henson@iheart.com',
    url='https://henson.rtfd.org',
    description='A framework for running a Python service driven by a consumer',
    license='Apache License, Version 2.0',
    long_description=read('README.rst'),
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=[
        # TODO: determine minimum versions for requirements
        'argh',
        'watchdog>=0.8.3',
    ],
    tests_require=[
        'pytest',
        'pytest-asyncio',
    ],
    cmdclass={
        'test': PyTest,
    },
    entry_points='''
        [console_scripts]
        henson=henson.cli:main
    ''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ]
)
