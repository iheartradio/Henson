Changelog
=========

Version 0.3.0
-------------

Release date TBD

- Add ``--reloader`` option to ``henson run``
- Automatically detect instances of Henson applications when running ``henson
  run`` if no attribute name is specified and there exists only one instance of
  an application in the loaded module


Version 0.2.1
-------------

Released 2015-08-03

- Automatically insert the present working directory at the beginning of
  sys.path to remove the need for modifying the PYTHONPATH or installing a
  package to run a Henson application


Version 0.2.0
-------------

Released 2015-07-30

- Add application-level logger
- Remove current_application, proxy support, and application Registry class
- Add extension base class and documentation on writing extensions
- Add CLI and command to run Henson applications


Version 0.1.0
-------------

Released 2015-06-08

- Initial release
