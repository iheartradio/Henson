from henson import Abort, Application

class FileConsumer:
    """Read lines from a file."""

    def __init__(self, filename):
        self.filename = filename
        self._file = None

    def __iter__(self):
        """FileConsumer objects are iterators."""
        return self

    def __next__(self):
        """Return the next line of the file, if available."""
        if not self._file:
            self._file = open(self.filename)
        try:
            return next(self._file)
        except StopIteration:
            self._file.close()
            raise Abort('Reached end of file', None)

    async def read(self):
        """Return the next line in the file."""
        return next(self)

async def callback(app, message):
    """Print the message retrieved from the file consumer."""
    print(app.name, 'received:', message)
    return message

app = Application(
    __name__,
    callback=callback,
    consumer=FileConsumer(__file__),
)

@app.startup
async def print_header(app):
    """Print a header for the file being processed."""
    print('# Begin processing', app.consumer.filename)

@app.teardown
async def print_footer(app):
    """Print a footer for the file being processed."""
    print('# Done processing', app.consumer.filename)

@app.message_preprocessor
async def remove_comments(app, line):
    """Abort processing of comments (lines that start with #)."""
    if line.strip().startswith('#'):
        raise Abort('Line is a comment', line)
    return line
