from setuptools import find_packages, setup

setup(
    name='Henson',
    version='0.3.0',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'click',
    ],
    tests_require=[
        'tox',
    ],
    entry_points='''
        [console_scripts]
        henson=henson.cli:cli
    ''',
)
