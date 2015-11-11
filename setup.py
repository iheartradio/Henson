from setuptools import find_packages, setup

setup(
    name='Henson',
    version='0.5.0',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        # TODO: determine minimum versions for requirements
        'click',
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
