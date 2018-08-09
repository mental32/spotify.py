import datetime

from spotify import _types

Track = _types.track


class PlaylistTrack:
    __slots__ = ('added_at', 'added_by', 'is_local', 'track')

    def __init__(self, client, data):
        self.added_by = data['added_by']
        self.added_at = datetime.datetime.strptime(data['added_at'], '%Y-%m-%dT%H:%M:%SZ')
        self.is_local = data['is_local']
        self.track = Track(client, data['track'])

    def __repr__(self):
        return '<spotify.PlaylistTrack: %s>' % repr(self.track)

    def __str__(self):
        return str(self.track)
