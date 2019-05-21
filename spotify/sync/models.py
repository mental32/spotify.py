import inspect
import functools

from .. import SpotifyBase
from . import Client as _Client
from .thread import SyncExecution


class SyncMeta(type):
    """Metaclass used for overloading coroutine functions on models."""
    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)

        base = bases[0]
        base_name = base.__name__

        if base_name in ('HTTPClient', 'HTTPUserClient'):
            def __init__(self, *args, **kwargs):
                super(type(self), self).__init__(*args, **kwargs)
                self.__client_thread__ = kwargs['loop']._thread

        elif base_name != 'Client':
            def __init__(self, client, *args, **kwargs):
                super(type(self), self).__init__(client, *args, **kwargs)
                self.__client_thread__ = client.__client_thread__

        try:
            setattr(klass, '__init__', __init__)
        except NameError:
            pass

        for name, func in inspect.getmembers(base):
            if inspect.iscoroutinefunction(func):
                def wrap(func):
                    @functools.wraps(func)
                    def wrapper(self, *args, **kwargs):
                        return self.__client_thread__.run_coro(func(self, *args, **kwargs))
                    return wrapper
                setattr(klass, func.__name__, wrap(getattr(base, name)))
            del name, func
        return klass


class Client(_Client, metaclass=SyncMeta):
    def __init__(self, *args, **kwargs):
        thread = SyncExecution()
        thread.start()

        kwargs['loop'] = thread._loop

        super().__init__(*args, **kwargs)
        self.__thread = self.__client_thread__ = thread


def _install(_types):
    for name, obj in _types.items():
        class Mock(obj, metaclass=SyncMeta):
            __slots__ = ('__client_thread__',)

        Mock.__name__ = obj.__name__
        Mock.__qualname__ = obj.__qualname__
        Mock.__doc__ = obj.__doc__

        yield name, Mock
