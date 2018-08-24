import datetime

from spotify import _types

Artist = _types.artist


class Track:
    __slots__ = ('__data', '__client', 'artists')

    def __init__(self, client, data):
        self.__client = client
        self.__data = data

        self.artists = [Artist(client, artist) for artist in data.get('artists', [])]

    def __repr__(self):
        return '<spotify.Track: "%s">' % self.name

    def __str__(self):
        return self.uri

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def id(self):
        return self.__data.get('id')

    @property
    def name(self):
        return self.__data.get('name')

    @property
    def href(self):
        return self.__data.get('href')

    @property
    def uri(self):
        return self.__data.get('uri')

    @property
    def duration(self):
        return self.__data.get('duration_ms')

    @property
    def explicit(self):
        return self.__data.get('explicit')

    async def audio_analysis(self):
        '''Get a detailed audio analysis for the track'''
        return await self.__client.http.track_audio_analysis(self.id)

    async def audio_features(self):
        '''Get audio feature information for the track'''
        return await self.__client.http.track_audio_features(self.id)


class PlaylistTrack(Track):
    __slots__ = ('added_at', 'added_by', 'is_local')

    def __init__(self, client, data):
        super().__init__(client, data['track'])

        self.added_by = data['added_by']
        self.is_local = data['is_local']
        self.added_at = datetime.datetime.strptime(data['added_at'], '%Y-%m-%dT%H:%M:%SZ')

    def __repr__(self):
        return '<spotify.PlaylistTrack: "%s">' % self.name
