from spotify import _types

Track = _types.track


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
        return '<spotify.Context: "%s">' %(self.uri)


class Device:
    __slots__ = ('id', 'name', 'type', 'volume', 'is_active', 'is_restricted')

    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.type = data.get('type')

        self.volume = data.get('volume_percent')

        self.is_active = data.get('is_active')
        self.is_restricted = data.get('is_restricted')

    def __eq__(self, other):
        return self.id == other.id

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
        if isinstance(context ,(list, tuple)):
            context_uri = [uri for uri in context]
        else:
            context_uri = context

        if device:
            device = device.id

        return await self._user.http.play_playback(context_uri, offset=offset, device_id=device)

    async def shuffle(self):
        state = self.ctx['shuffle']
        self.ctx['shuffle'] = int(not state)

        return await self._user.http.shuffle_playback(state)

    async def transfer(self, device, ensure_playback=False):
        is_dev = isinstance(device, Device)

        if is_dev:
            device = device.id

        await self._user.http.transfer_player(device, play=ensure_playback)

        if is_dev:
            self.device = device
