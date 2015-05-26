"""Utilities."""


class ProxyObject:

    """A wrapper around an object to delay its instantiation.

    A proxy can be created to either an object or a callable. When using
    a callable, it will not be executed until an attribute of the object
    it creates is accessed.

    Args:
        proxied (object or callable): The object to proxy or the
          callable that will instantiate it.

    .. note::

       The result of the callable is not cached. It will be executed
       upon each access.
    """

    # This class is inspired heavily be werkzeug.local.LocalProxy and
    # wrapt.wrappers.ObjectProxy.

    __slots__ = ('__proxied',)

    def __init__(self, proxied):
        """Initialize the class."""
        object.__setattr__(self, '_ProxyObject__proxied', proxied)

    @property
    def _current_object(self):
        """Return the current object."""
        if callable(self.__proxied):
            return self.__proxied()
        else:
            return self.__proxied

    # The properties and methods that follow implement the data model.
    # They serve as passthroughs to the proxied object. Whenever
    # possible a lambda is used to shorten the code. Full methods are
    # used whenever the lambda syntax won't suffice.

    __class__ = property(lambda s: s._current_object.__class__)
    __dict__ = property(lambda s: s._current_object.__dict__)
    __name__ = property(lambda s: s._current_object.__name__)

    # Basic

    def __repr__(self):
        """Return a printable representation."""
        try:
            return repr(self._current_object)
        except RuntimeError:
            return '<{}: unbound>'.format(self.__class__.__name__)

    def __str__(self):
        """Return a readable representation."""
        try:
            return str(self._current_object)
        except RuntimeError:
            return repr(self)

    __lt__ = lambda s, o: s._current_object < o
    __le__ = lambda s, o: s._current_object <= o
    __eq__ = lambda s, o: s._current_object == o
    __ne__ = lambda s, o: s._current_object != o
    __gt__ = lambda s, o: s._current_object > o
    __ge__ = lambda s, o: s._current_object >= o

    __hash__ = lambda s: hash(s._current_object)

    def __bool__(self):
        """Return a boolean representation."""
        try:
            return bool(self._current_object)
        except RuntimeError:
            return False

    # Attribute access

    __getattr__ = lambda s, n: getattr(s._current_object, n)
    __setattr__ = lambda s, n, v: setattr(s._current_object, n, v)
    __delattr__ = lambda s, n: delattr(s._current_object, n)

    def __dir__(self):
        """Return a directory listing."""
        try:
            return dir(self._current_object)
        except RuntimeError:
            return []

    # Callable

    __call__ = lambda s, *a, **kw: s._current_object(*a, **kw)

    # Containers

    __len__ = lambda s: len(s._current_object)

    __getitem__ = lambda s, k: s._current_object[k]

    def __setitem__(self, key, value):
        """Assign a value to a key."""
        self._current_object[key] = value

    def __delitem__(self, key):
        """Delete a key."""
        del self._current_object[key]

    __iter__ = lambda s: iter(s._current_object)
    __contains__ = lambda s, i: i in s._current_object

    # Numeric

    __add__ = lambda s, o: s._current_object + o
    __sub__ = lambda s, o: s._current_object - o
    __mul__ = lambda s, o: s._current_object * o
    __truediv__ = lambda s, o: s._current_object / o
    __floordiv__ = lambda s, o: s._current_object // o
    __mod__ = lambda s, o: s._current_object % o
    __divmod__ = lambda s, o: divmod(s._current_object, o)
    __pow__ = lambda s, o: s._current_object ** o
    __lshift__ = lambda s, o: s._current_object << o
    __rshift__ = lambda s, o: s._current_object >> o
    __and__ = lambda s, o: s._current_object & o
    __xor__ = lambda s, o: s._current_object ^ o
    __or__ = lambda s, o: s._current_object | o

    __radd__ = lambda s, o: o + s._current_object
    __rsub__ = lambda s, o: o - s._current_object
    __rmul__ = lambda s, o: o * s._current_object
    __rtruediv__ = lambda s, o: o / s._current_object
    __rfloordiv__ = lambda s, o: o // s._current_object
    __rmod__ = lambda s, o: o % s._current_object
    __rdivmod__ = lambda s, o: divmod(o, s._current_object)
    __rpow__ = lambda s, o: o ** s._current_object
    __rlshift__ = lambda s, o: o << s._current_object
    __rrshift__ = lambda s, o: o >> s._current_object
    __rand__ = lambda s, o: o & s._current_object
    __rxor__ = lambda s, o: o ^ s._current_object
    __ror__ = lambda s, o: o | s._current_object

    __neg__ = lambda s: -(s._current_object)
    __pos__ = lambda s: +(s._current_object)
    __abs__ = lambda s: abs(s._current_object)
    __invert__ = lambda s: ~(s._current_object)

    __complex__ = lambda s: complex(s._current_object)
    __int__ = lambda s: int(s._current_object)
    __round__ = lambda s, n=0: round(s._current_object, n)
    __float__ = lambda s: float(s._current_object)

    __index__ = lambda s: s._current_object.__index__()

    # Context manager

    __enter__ = lambda s: s._current_object.__enter__()
    __exit__ = lambda s, *a, **kw: s._current_object.__exit__(*a, **kw)
