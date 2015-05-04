"""Handle service imports."""

from importlib import import_module
import os
import sys

__all__ = ('import_from_service', 'ServiceImportError')


class ServiceImportError(ImportError):

    """A custom ImportError provides information related to services."""

    def __init__(self, service, module):
        """Initialize the exception.

        Args:
            service (str): The name of the service importing from.
            module (str): The name of the module that couldn't be
              imported.
        """
        self.service = service
        self.module = module

    def __str__(self):
        """Return a printable version."""
        return 'The {} service does not contain a module named {}.'.format(
            self.service, self.module)


def import_from_service(service, module):
    """Import a module from a service.

    Args:
        service (str): The name of the service importing from.
        module (str): The name of the module to import.

    Returns:
        module: The imported module.

    Raises:
        ServiceImportError
    """
    import_ = '{}.{}'.format(service, module)

    try:
        return import_module(import_)
    except ImportError:
        # If there was an ImportError, check to see if it was an error
        # importing the desired module or an error while importing that
        # module. If it was the former, raise an exception to indicate
        # the problem importing the module. If, however, it was the
        # later, let the original exception propagate up.
        exc_type, exc_value, tb = sys.exc_info()
        if _is_important_traceback(import_, tb):
            _reraise(exc_type, exc_value, tb.tb_next)
        raise ServiceImportError(service, module)


# The following functions are adopted from Flask's extension loader
# import hook. (reraise is from Flask's _compat module.) Flask is
# distrbuted under a 3-clause BSD license.


def _is_important_frame(module, traceback):  # NOQA
    """Checks a single frame if it's important."""
    g = traceback.tb_frame.f_globals
    if '__name__' not in g:
        return False

    # Some python versions will will clean up modules so early that the
    # module name at that point is no longer set.  Try guessing from
    # the filename then.
    filename = os.path.abspath(traceback.tb_frame.f_code.co_filename)
    test_string = os.path.sep + module.replace('.', os.path.sep)
    return (
        test_string + '.py' in filename or
        test_string + os.path.sep + '__init__.py' in filename
    )


def _is_important_traceback(module, traceback):  # NOQA
    """Walks a traceback's frames and checks if any of the frames
    originated in the given important module.  If that is the case then we
    were able to import the module itself but apparently something went
    wrong when the module was imported.  (Eg: import of an import failed).
    """
    while traceback is not None:
        if _is_important_frame(module, traceback):
            return True
        traceback = traceback.tb_next
    return False


def _reraise(tp, value, tb=None):
    """Reraise an exception."""
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value
