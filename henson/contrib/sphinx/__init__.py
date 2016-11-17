"""Sphinx contrib plugin for documenting Henson CLI extensions."""

from sphinxcontrib.autoprogram import AutoprogramDirective


def _import_extension(import_path):
    module_name, extension_name = import_path.split(':', 1)
    module = __import__(module_name, None, None, [extension_name])
    return getattr(module, extension_name)


class HensonCLIDirective(AutoprogramDirective):
    """A Sphinx directive that can be used to document a CLI extension.

    This class wraps around
    `autoprogram <https://pythonhosted.org/sphinxcontrib-autoprogram/>`_
    to generate Sphinx documentation for extensions that extend the
    Henson CLI.

    .. code::

        .. hensoncli:: henson_database:Database
           :start_command: db

    .. versionadded:: 1.1.0

    .. versionchanged:: 1.2.0

        The ``prog`` option will default to the proper way to invoke
        command line extensions.
    """

    def prepare_autoprogram(self):
        """Prepare the instance to be run through autoprogram."""
        # Tell autoprogram how to find the argument parser.
        self.arguments = 'henson.cli:parser',

        # Most Henson CLI extensions will be invoked the same way. The
        # extension authors shouldn't have to include that in their
        # Sphinx documentation.
        self.options.setdefault('prog', 'henson --app APP_PATH')

    def register_cli(self):
        """Register the CLI."""
        import_path, = self.arguments
        extension = _import_extension(import_path)
        extension().register_cli()

    def run(self):
        """Register the CLI and run autoprogram."""
        self.register_cli()
        self.prepare_autoprogram()

        return super().run()


def setup(app):
    """Register the extension."""
    app.add_directive('hensoncli', HensonCLIDirective)
