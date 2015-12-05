from setuptools import find_packages, setup

setup(
    name='Henson',
    version='0.5.0',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        # TODO: determine minimum versions for requirements
        # Version 6 of click changed the signature of BadOptionUsage,
        # breaking version 5.x compatible code. While we decide how best
        # to handle this in Henson, click is being pinned to older
        # versions of click.
        'click<6.0',
        'watchdog>=0.8.3',
    ],
    tests_require=[
        'tox',
    ],
    entry_points='''
        [console_scripts]
        henson=henson.cli:cli
    ''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ]
)
