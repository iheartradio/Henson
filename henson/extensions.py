"""Extension base."""

__all__ = ('Extension',)


class Extension:
    """A base class for Hension extensions.

    Args:
        app (Optional[henson.base.Application]): An application instance
            that has an attribute named settings that contains a mapping
            of settings to interact with a database.
    """

    def __init__(self, app=None):
        """Initialize an instance of the extension.

        If app is provided, init_app will also be called with the
        provided application. Otherwise, init_app must be called with an
        application explicitly before the extension's reference to an
        application is usable.

        Args:
            app (Optional[henson.base.Application]): An application
                instance that will be initialized.
        """
        self._app = None

        if app:
            self.init_app(app)

    @property
    def DEFAULT_SETTINGS(self):  # NOQA
        """A ``dict`` of default settings for the extension.

        When a setting is not specified by the application instance and
        has a default specified, the default value will be used.
        Extensions should define this where appropriate. Defaults to
        ``{}``.
        """
        return {}

    @property
    def REQUIRED_SETTINGS(self):  # NOQA
        """An ``iterable`` of required settings for the extension.

        When an extension has required settings that do not have default
        values, their keys may be specified here. Upon extension
        initialization, an exception will be raised if a value is not
        set for each key specified in this list. Extensions should
        define this where appropriate. Defaults to ``()``.
        """
        return ()

    def init_app(self, app):
        """Initialize the application.

        In addition to associating the extension's default settings with
        the application, this method will also check for the extension's
        required settings.

        Args:
            app (henson.base.Application): An application instance that
                will be initialized.
        """
        for key, value in self.DEFAULT_SETTINGS.items():
            app.settings.setdefault(key, value)

        required_settings = set(self.REQUIRED_SETTINGS)
        current_settings = set(app.settings.keys())
        missing_settings = required_settings - current_settings
        if missing_settings:
            raise KeyError(
                '{} requires the following missing settings: {}'.format(
                    self.__class__.__name__,
                    ', '.join(str(key) for key in missing_settings),
                )
            )

        self._app = app

    @property
    def app(self):
        """Return the registered app."""
        if not self._app:
            raise RuntimeError(
                'No application has been assigned to this instance. '
                'init_app must be called before referencing instance.app.')
        return self._app
