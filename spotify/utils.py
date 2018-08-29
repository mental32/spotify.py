import functools


def uri_to_id(string):
    if string[:8] == 'spotify:':
        return string.rsplit(':', maxsplit=1)[-1]
    return string


def ensure_http(func):
    @functools.wraps(func)
    async def decorator(self, *args, **kwargs):
        if not hasattr(self, 'http'):
            raise AttributeError('"{0}" has no attribute \'http\': To perform API requests {0} needs a HTTP presence.'.format(self))

        return await func(self, *args, **kwargs)

    return decorator


class _spotify__lookup(dict):
    __types = ['artist', 'track', 'user', 'playlist', 'album', 'library', 'playlist_track']

    def __getattribute__(self, key):
        _types = object.__getattribute__(self, '_spotify__lookup__types')

        if key in _types:
            def _lookup(*args, **kwargs):
                return self[key](*args, **kwargs)

            return _lookup

        return object.__getattribute__(self, key)
