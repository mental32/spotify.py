import asyncio
import json
from urllib.parse import quote_plus as quote

from .http import HTTPClient, HTTPUserClient

from spotify import _types
from spotify.models import User, Artist, Track, Playlist, Album, Library

_types.update({
    'artist': Artist,
    'track': Track,
    'user': User,
    'playlist': Playlist,
    'album': Album,
    'library': Library
})

class Client:
    '''Represents an interface to Spotify.

    This class is used to interact with the Spotify API

    **Parameters**

    - *client_id* (:class:`str`)
        The client id provided by spotify for the app.

    - *client_secret* (:class:`str`)
        The client secret for the app.

    - *loop* (`optional`:`event loop`)
        The event loop the client should run on, if no loop is specified `asyncio.get_event_loop()` is called and used instead.
    '''
    def __init__(self, client_id, client_secret, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.http = HTTPClient(client_id, client_secret)

    def __repr__(self):
        return '<spotify.Client: "%s"' % self.http.client_id

    @property
    def client_id(self):
        return self.http.client_id

    ### External model contstructors

    def oauth2_url(self, redirect_uri, scope, state=None):
        '''Generate an outh2 url for user authentication
        
        **parameters**

        - *redirect_uri* (:class:`str`)
            Where spotify should redirect the user to after authentication.

        - *scope* (:class:`str`)
            Space seperated spotify scopes for different levels of access.

        - *state* (:class:`str`)
            using a state value can increase your assurance that an incoming connection is the result of an authentication request.
        '''

        state = state or ''
        BASE = 'https://accounts.spotify.com/authorize'

        return BASE + '/?client_id={0}&response_type=code&redirect_uri={1}&scope={2}{3}'.format(self.http.client_id, quote(redirect_uri), scope, state)

    async def user_from_token(self, token):
        '''Create a user session from a token

        **parameters**

        - *token* (:class:`str`)
            The token to attatch the user session to
        '''
        http = HTTPUserClient(token)
        data = await http.current_user()

        return User(self, data=data, http=http)

    ### Get single objects ###

    async def get_album(self, spotify_id, *, market='US'):
        '''Retrive an album with a spotify ID
        
        **parameters**

        - spotify_id (:class:`str`) - the ID to look for
        '''
        data = await self.http.album(spotify_id, market=market)
        return Album(self, data)

    async def get_artist(self, spotify_id):
        '''Retrive an artist with a spotify ID
        
        **parameters**

        - spotify_id (:class:`str`) - the ID to look for
        '''
        data = await self.http.artist(spotify_id)
        return Artist(self, data)

    async def get_track(self, spotify_id):
        '''Retrive an track with a spotify ID
        
        **parameters**

        - spotify_id (:class:`str`) - the ID to look for
        '''
        data = await self.http.track(spotify_id)
        return Track(self, data)

    async def get_user(self, spotify_id):
        '''Retrive an user with a spotify ID
        
        **parameters**

        - spotify_id (:class:`str`) - the ID to look for
        '''
        data = await self.http.user(spotify_id)
        return User(self, data)

    ### Get multiple objects ###

    async def get_albums(self, *, ids, market='US'):
        '''Retrive multiple albums with a list of spotify IDs
        
        **parameters**

        - ids (:class:`str`) - the ID to look for
        '''
        data = await self.http.albums(','.join(ids), market=market)
        return [Album(self, album) for album in data['albums']]

    async def get_artists(self, *, ids):
        '''Retrive multiple artists with a list of spotify IDs
        
        **parameters**

        - ids (:class:`str`) - the ID to look for
        '''
        data = await self.http.artists(','.join(ids))
        return [Album(self, artist) for artist in data['artists']]

    async def search(self, q, *, types=['track', 'playlist', 'artist', 'album'], limit=20, offset=0, market=None):
        '''Access the spotify search functionality

        **parameters**

        - *q* (:class:`str`) - the search query

        - *types* (Optional `iterable`)
            A sequence of search types (can be any of `track`, `playlist`, `artist` or `album`) to refine the search request.
            A `ValueError` may be raised if a search type is found that is not valid.

        - *limit* (Optional :class:`int`)
            The limit of search results to return when searching.
            Maximum limit is 50, any larger may raise a :class:`HTTPException`

        - *offset* (Optional :class:`int`)
            The offset from where the api should start from in the search results.

        - *market* (Optional :class:`str`)
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.
        '''
        fmt = 'Bad queary type! got %s expected any: track, playlist, artist, album'

        if not hasattr(types, '__iter__'):
            raise TypeError('types must be an iterable.')

        elif not isinstance(types, list):
            types = [item for item in types]

        for qt in types:
            if qt not in ['track', 'playlist', 'artist', 'album']:
                raise ValueError(fmt %(qt))

        types = ','.join(_type.strip() for _type in types)

        kwargs = {'q': q.replace(' ', '%20').replace(':', '%3'), 'queary_type': types, 'market': market, 'limit': limit, 'offset': offset}
        data = await self.http.search(**kwargs)

        container = {}
        for key, value in data.items():

            items = [_types[_object.get('type')](self, _object) for _object in value['items']]
            container.setdefault(key, []).extend(items)

        return container
