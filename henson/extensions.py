"""Extension base."""

__all__ = ('Extension',)


class Extension:

    """A base class for Hension extensions.

    Args:
        app (optional): An application instance that has an attribute
          named settings that contains a mapping of settings to interact
          with a database.


    .. versionadded:: 0.2.0
    """

    def __init__(self, app=None):
        """Initialize an instance of the extension.

        If app is provided, init_app will also be called with the provided
        application. Otherwise, init_app must be called with an application
        explicitly before the extension's reference to an application is
        usable.
        """
        self._app = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Configure the application with the extension's default settings.

        Args:
            app: Application instance that has an attribute named
              settings that contains a mapping of settings.
        """
        if hasattr(self, 'DEFAULT_SETTINGS'):
            for key, value in self.DEFAULT_SETTINGS.items():
                app.settings.setdefault(key, value)

        self._app = app

    @property
    def app(self):
        """Return the registered app."""
        if not self._app:
            raise RuntimeError(
                'No application has been assigned to this instance. '
                'init_app must be called before referencing instance.app.')
        return self._app
