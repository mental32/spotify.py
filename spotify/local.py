import asyncio
import warnings

from .http import LocalHTTPClient


class LocalClient:
    '''Represents an interface to the locally running spotify app.

    **Paramters**

    - *loop* (EventLoop)
        The event loop the client should run on, if no loop is specified `asyncio.get_event_loop()` is called and used instead.
    '''
    def __init__(self, loop=None):
        warnings.warn('LocalClient is currently depreciated.', DeprecationWarning)

        self.loop = loop or asyncio.get_event_loop()
        self.http = LocalHTTPClient()

    def __del__(self):
        asyncio.run_coroutine_threadsafe(self.http.close(), self.loop)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *other):
        await self.http.close()

    async def pause(self):
        '''Pause a running session'''
        return await self.http.set_pause(True)

    async def unpause(self):
        '''Unpause a running session'''
        return await self.http.set_pause(False)

    async def status(self):
        '''Get status of local spotify app'''
        return await self.http.get_status()

    async def version(self):
        '''Get the version of local spotify app'''
        return await self.http.get_version()

    async def play(self, track):
        '''Play a track'''
        return await self.http.play(str(track))
