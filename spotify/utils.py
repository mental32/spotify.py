##
# -*- coding: utf-8 -*-
##
import functools

def ensure_http(func):

    @functools.wraps(func)
    async def decorator(self, *args, **kwargs):
        if not hasattr(self, 'http'):
            raise AttributeError('type obj {0} has no attribute \'http\': To perform API requests {0} needs a HTTP presence.'.format(type(self)))

        return await func(self, *args, **kwargs)

    return decorator
