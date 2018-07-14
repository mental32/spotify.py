from spotify import _types

Artist = _types.artist

class Track:
    __slots__ = ['__data', '__client', 'artists']

    def __init__(self, client, data):
        self.__client = client
        self.__data = data

        self.artists = [Artist(client, artist) for artist in data.get('artists', [])]

    def __repr__(self):
        return '<spotify.Track: "%s">' % (self.name)

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
