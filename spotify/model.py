##
# -*- coding: utf-8 -*-
##

class SpotifyModel:
    __slots__ = ['is_simple']


class Image:
    __slots__ = ('height', 'width', 'url')

    def __init__(self, *, height, width, url):
        self.height = height
        self.width = width
        self.url = url

    def __repr__(self):
        return '<spotify.Image (width: %s, height: %s)>' %(self.width, self.height)


class Context:
    __slots__ = ('external_urls', 'type', 'href', 'uri')

    def __init__(self, data):
        self.external_urls = data.get('external_urls')
        self.type = data.get('type')

        self.href = data.get('href')
        self.uri = data.get('uri')

    def __repr__(self):
        return '<spotify.Context: "%s">' %(self.href)

class Device:
    __slots__ = ('id', 'name', 'type', 'volume', 'is_active', 'is_restricted')

    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.type = data.get('type')

        self.volume = data.get('volume_percent')

        self.is_active = data.get('is_active')
        self.is_restricted = data.get('is_restricted')

    def __repr__(self):
        return '<spotify.Device: "%s">' %(self.name or self.id)

class Player:
    '''wrapper for a users current playback'''
    __slots__ = ('repeat_state', 'timestamp', 'progress_ms', 'shuffle_state', 'is_playing', '_user', 'item', 'context', 'device', 'ctx')

    def __init__(self, user):
        self._user = user
        self.ctx = {'shuffle': False}

    def __repr__(self):
        return '<spotify.Player: "%s">' %(self._user.display_name or self._user.id)

    def from_data(self, data):
        self.repeat_state = data.get('repeat_state')

        self.timestamp = data.get('timestamp')
        self.progress_ms = data.get('progress_ms')

        self.shuffle_state = data.get('shuffle_state')
        self.is_playing = data.get('is_playing')

        self.context = Context(data.get('context'))
        self.device = Device(data.get('device'))

        self.item = self._user._client._build('_tracks', data.get('item'))

    async def pause(self):
        return await self._user.http.pause_playback()

    async def transfer(self, device_id, ensure_playback=False):
        return await self._user.http.transfer_player(device_id, play=ensure_playback)

    async def shuffle(self):
        state = self.ctx['shuffle']
        self.ctx['shuffle'] = not state

        return await self._user.http.shuffle_playback(state)

    async def start(self, context_uri, *, uris=None, offset=0):
        return await self._user.http.play_playback(uris or context_uri, offset=offset)

    async def set_volume(self, volume):
        return await self._user.http.set_playback_volume(volume)

    async def seek(self, pos):
        return await self._user.http.seek_playback(pos)

    async def next(self):
        return await self._user.http.skip_next()

    async def previous(self):
        return await self._user.http.skip_previous()
