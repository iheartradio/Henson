from setuptools import find_packages, setup

setup(
    name='ingestion.service',
    version='0.3.0',
    namespace_packages=['ingestion'],
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'click==4.0',
        'ingestion.kafka>=0.2.0',
        'setuptools',
    ],
    tests_require=[
        'tox',
    ],
)
