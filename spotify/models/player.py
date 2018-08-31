from spotify import _types
from spotify.errors import HTTPException

from .common import Context, Device

Track = _types.track


class Player:
    '''wrapper for a users current playback'''
    __slots__ = ('repeat_state', 'timestamp', 'progress_ms', 'shuffle_state', 'is_playing', '_user', 'item', 'context', 'device', 'ctx')

    def __init__(self, user):
        self._user = user
        self.ctx = {'shuffle': False}

    def __repr__(self):
        return '<spotify.Player: "%s">' % (self._user.display_name or self._user.id)

    def populate(self, data):
        self.repeat_state = data.get('repeat_state')

        self.timestamp = data.get('timestamp')
        self.progress_ms = data.get('progress_ms')

        self.shuffle_state = data.get('shuffle_state')
        self.is_playing = data.get('is_playing')

        if data.get('context'):
            self.context = Context(data.get('context'))

        if data.get('device'):
            self.device = Device(data.get('device'))

        if data.get('item'):
            self.item = Track(self._user._User__client, data.get('item'))

    async def pause(self):
        return await self._user.http.pause_playback()

    async def resume(self):
        return await self._user.http.play_playback(None)

    async def seek(self, pos):
        return await self._user.http.seek_playback(pos)

    async def set_repeat(self, state):
        return await self._user.http.repeat_playback(state)

    async def set_volume(self, volume):
        return await self._user.http.set_playback_volume(volume)

    async def next(self):
        return await self._user.http.skip_next()

    async def previous(self):
        return await self._user.http.skip_previous()

    async def play(self, context, *, offset=0, device=None):
        if isinstance(context, (list, tuple)):
            context_uri = [uri for uri in context]
        else:
            context_uri = [context]

        if device:
            device = device.id

        return await self._user.http.play_playback(context_uri, offset=offset, device_id=device)

    async def shuffle(self):
        state = self.ctx['shuffle']
        self.ctx['shuffle'] = int(not state)

        return await self._user.http.shuffle_playback(state)

    async def transfer(self, device, ensure_playback=False):
        try:
            if isinstance(device, Device):
                device = device.id
                self.device, old_device = device, self.device
            else:
                self.device, old_device = None, self.device

            await self._user.http.transfer_player(device, play=ensure_playback)
        except HTTPException:
            self.device = old_device
            raise
        else:
            return self.device
