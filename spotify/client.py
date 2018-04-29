##
# -*- coding: utf-8 -*-
##
import asyncio
import random
import json
from urllib.parse import quote_plus as quote

from .http import HTTPClient
from .state import Cache

from .user import User
from .artist import Artist
from .album import Album
from .track import Track
from .playlist import Playlist

_swap = {
    'artist': Artist,
    'album': Album,
    'track': Track,
    'playlist': Playlist,
    'user': User
}

class Client:
    '''Represents a client connection that connects to Spotify.

    This class is used to interact with the Spotify API.
    Also used for local methods that involve caching.'''

    def __init__(self, client_id, client_secret, loop=None):
        self.__cache = Cache()
        self._cache = self.__cache

        self.loop = loop or asyncio.get_event_loop()
        self.http = HTTPClient(client_id, client_secret)
        self.user_sessions = []

    def __repr__(self):
        return '<spotify.Client: "%s">' %(self.http.client_id)

    def _construct(self, _object, _type):
        '''take the raw json data and construct a model then return it.
        this is mainly to be used by the models themselves to avoid any circular dependencies.
        '''
        return _swap.get(_type)(client=self, data=_object)

    def _build(self, pool, data):
        '''like Client._construct but prefers to return the object from cache before constructing'''
        obj = self.__cache.get(pool, id=data.get('id'))
        return obj or self._construct(data, data['type'])

    def _istype(self, obj, _type):
        return isinstance(obj, _swap[_type])

    ### Client exposed cache points ###

    @property
    def artists(self):
        return tuple(artist for artist in self.__cache._artists)

    @property
    def albums(self):
        return tuple(album for album in self.__cache._albums)

    @property
    def tracks(self):
        return tuple(track for track in self._cache._tracks)

    @property
    def playlists(self):
        return tuple(playlist for playlist in self._cache._playlists)

    ### Custom constructors for other objects ###

    def oauth2_url(self, redirect_uri, scope, state=None):
        if state is None:
            state = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(12))

        BASE = 'https://accounts.spotify.com/authorize'

        return BASE + '/?client_id={0}&response_type=code&redirect_uri={1}&scope={2}&state={3}'.format(self.http.client_id, quote(redirect_uri), scope, state)

    def refresh_token(self):
        pass

    def user_from_token(self, token):
        session = User(self, token=token)
        self.user_sessions.append(session)
        return session

    ### Get single objects ###

    async def get_album(self, id, *, market='US'):
        return self._construct(await self.http.album(id, market=market), 'album')

    async def get_artist(self, id):
        return self._construct(await self.http.artist(id), 'artist')

    async def get_track(self, id):
        return self._construct(await self.http.track(id), 'track')

    async def get_category(self, id, *, country=None, locale=None):
        return self._construct(await self.http.category(id, country=country, locale=locale), 'category')

    async def get_user(self, id):
        return User(self, data=await self.http.user(id))

    ### Get multiple objects ###

    async def get_albums(self, *, ids, market='US'):
        raw = []
        data = await self.http.albums(','.join(ids), market=market)
        for album in data['albums']:
            raw.append(self._construct(json.loads(album), 'album'))
        return raw

    async def get_artists(self, *, ids):
        raw = []
        data = await self.http.artists(','.join(ids))
        for artist in data['artists']:
            raw.append(self._construct(artist, 'artist'))
        return raw

    async def search(self, q, *, types=['track', 'playlist', 'artist', 'album'], limit=20, offset=0, market=None):
        '''return a dict that contains the queary results per queary type found in types parameter'''
        fmt = 'Bad queary type! got %s expected any: track, playlist, artist, album'

        if not hasattr(types, '__iter__'):
            raise TypeError('types must be an iterable.')

        elif not isinstance(types, list):
            types = [item for item in types]

        elif not isinstance(limit, int):
            raise TypeError('limit must be an int.')

        elif not 51 > limit >= 1:
            raise ValueError('Limit can not go over 50 or under 1.')

        elif not isinstance(offset, int):
            raise TypeError('offset must be an int.')

        elif offset > 100000:
            raise ValueError('offset can not go over 100000')

        for qt in types:
            if qt not in ['track', 'playlist', 'artist', 'album']:
                raise ValueError(fmt %(qt))

        types = ','.join(_type.strip() for _type in types)
        queary = q.replace(' ', '%20').replace(':', '%3')

        kwargs = {'q': queary, 'queary_type': types, 'market': market, 'limit': limit, 'offset': offset}
        data = await self.http.search(**kwargs)

        container = {}
        for key, value in data.items():
            if key not in container:
                container[key] = []

            for _object in value['items']:
                container[key].append(self._construct(_object, _object.get('type')))

        return container
