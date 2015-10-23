Changelog
=========

Version 0.5.0
-------------

Released TBD

Version 0.4.0
-------------

Released 2015-10-23

- Remove argument to override application-level logger
- Improve test coverage
- Add ``message_preprocessors`` to handle preprocessing incoming messages
- Add ``result_postprocessors`` to handle postprocessing results of processing
  the incoming messages
- Restructure exception catching to handle ``Exception`` and break on
  ``BaseException``
- Add Retry to ``contrib`` packages to allow for automatic message retrying

Version 0.3.0
-------------

Released 2015-09-21

- Add ``--reloader`` option to ``henson run``
- Automatically detect instances of Henson applications when running ``henson
  run`` if no attribute name is specified and there exists only one instance of
  an application in the loaded module
- Add REQUIRED_SETTINGS functionality to the Extension class

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
