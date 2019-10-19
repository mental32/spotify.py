import inspect
import functools

from . import Client as _Client
from .thread import SyncExecution


class SyncMeta(type):
    """Metaclass used for overloading coroutine functions on models."""

    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)

        base = bases[0]
        base_name = base.__name__

        if base_name in ("HTTPClient", "HTTPUserClient"):

            def __init__(self, *args, **kwargs):
                base.__init__(self, *args, **kwargs)
                self.__client_thread__ = kwargs[
                    "loop"
                ]._thread  # pylint: disable=protected-access

        elif base_name != "Client":

            def __init__(self, client, *args, **kwargs):  # type: ignore
                base.__init__(self, client, *args, **kwargs)
                self.__client_thread__ = client.__client_thread__

        try:
            setattr(klass, "__init__", __init__)
        except NameError:
            pass

        for ident, func in inspect.getmembers(base):

            if inspect.iscoroutinefunction(func):
                _func = getattr(base, ident)

                def wrap(func):
                    if isinstance(func, classmethod):

                        @classmethod
                        @functools.wraps(func)
                        def wrapper(
                            cls, client, *args, **kwargs
                        ):  # pylint: disable=unused-argument
                            assert isinstance(
                                client, _Client
                            ), "First argument of classmethod was not a `spotify.Client` instance"
                            client.__client_thread__.run_coro(
                                func,
                                client,
                                *args,
                                **kwargs  # TODO: investigate if this is correct.
                            )

                    else:

                        @functools.wraps(func)
                        def wrapper(self, *args, **kwargs):
                            return self.__client_thread__.run_coro(
                                func(self, *args, **kwargs)
                            )

                    return wrapper

                setattr(klass, ident, wrap(_func))
            del ident
        return klass


class Client(_Client, metaclass=SyncMeta):
    def __init__(self, *args, **kwargs):
        thread = SyncExecution()
        thread.start()

        kwargs["loop"] = thread._loop  # pylint: disable=protected-access

        super().__init__(*args, **kwargs)
        self.__thread = self.__client_thread__ = thread


def _install(_types):
    for name, obj in _types.items():

        class Mock(obj, metaclass=SyncMeta):  # pylint: disable=too-few-public-methods
            __slots__ = ("__client_thread__",)

        Mock.__name__ = obj.__name__
        Mock.__qualname__ = obj.__qualname__
        Mock.__doc__ = obj.__doc__

        yield name, Mock
