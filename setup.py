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
    version='2.2.0',
    author='Aditya Ghosh, Leonard Bedner, Zack Morris, and others',
    author_email='henson@iheart.com',
    url='https://henson.readthedocs.io',
    description='A framework for running a Python service driven by a consumer',
    long_description=read('README.rst'),
    license='Apache License, Version 2.0',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=[
        # TODO: determine minimum versions for requirements
        'argh',
        'watchdog>=0.8.3',
    ],
    extras_require={
        'sphinx': [
            'sphinx<1.7.1',
            'sphinxcontrib-autoprogram>=0.1.3',
        ],
    },
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ]
)
