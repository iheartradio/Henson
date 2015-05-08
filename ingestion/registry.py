"""Application registry."""

__all__ = ('Registry')


class Registry:

    """An application registry.

    The registry provides easy access to the most recently registered
    application.

    .. versionadded:: 0.3.0
    """

    def __init__(self):
        """Initialize the class."""
        self._applications = []

    @property
    def current_application(self):
        """Return the most recently registered application.

        Returns:
            :class:~`ingestion.service.Application`: The most recent
              application. None if no applications have been registered.
        """
        if not self._applications:
            return None
        return self._applications[-1]

    @current_application.setter
    def current_application(self, app):
        """Register a new application.

        Args:
            app (:class:`~ingestion.service.Application`): The
              application to register.
        """
        self._applications.append(app)
