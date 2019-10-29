import asyncio
import sys
import os
import functools
from typing import List, Any

if os.path.abspath("../.") not in sys.path:
    sys.path.insert(0, os.path.abspath("../."))

try:
    SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
    SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
except KeyError:
    sys.exit(1)

import spotify

__all__ = (
    "async_with_client",
    "spotify",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_CLIENT_ID",
    "TEST_ALBUMS",
    "TEST_ARTISTS",
    "async_chain",
)

TEST_ALBUMS = ["spotify:album:334X6XoNKUzpAQbm5FPsMh"]

TEST_ARTISTS = ["spotify:artist:6UCQYrcJ6wab6gnQ89OJFh"]


async def async_chain(corofuncs, delay: float = 0.25) -> List[Any]:
    results = []
    for corofunc in corofuncs:
        result = await corofunc
        results.append(result)
        await asyncio.sleep(delay)
    return results


def async_with_client(*client_args, **client_kwargs):
    """Decorate an async test to run inside a `async with client` statement.

    Parameters
    ----------
    *client_args : Any
        The args to pass into spotify.Client
    **client_kwargs : Any
        The kwargs to pass into spotify.Client
    """

    def decorator(corofunc):
        @functools.wraps(corofunc)
        def decorated(*args, **kwargs):
            loop = asyncio.get_event_loop()

            async def inner():
                async with spotify.Client(*client_args, **client_kwargs) as client:
                    kwargs["client"] = client
                    await corofunc(*args, **kwargs)

            return loop.run_until_complete(inner())

        return decorated

    return decorator
