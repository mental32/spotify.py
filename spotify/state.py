##
# -*- coding: utf-8 -*-
##
import sys


class Cache:
    __slots__ = ['_artists', '_albums', '_tracks', '_playlists']

    def __init__(self):
        self._artists = []
        self._albums = []
        self._tracks = []
        self._playlists = []

    def find(self, predicate, seq):
        for element in seq:
            if predicate(element):
                return element
        else:
            return None

    def get(self, pool, **kwargs):
        def predicate(element):
            for key, value in kwargs.items():
                obj = getattr(element, key)
                if obj != value:
                    return False
            else:
                return True

        seq = getattr(self, pool)
        return self.find(predicate, seq)

    def add(self, pool, obj):
        container = getattr(self, pool)

        for index, other in enumerate(container):
            if other.id == obj.id:
                integrity = (other.is_simple, obj.is_simple)
                if integrity[0] != integrity[1] and obj.is_simple:
                    other._update(obj)
                else:
                    container[index] = obj
                return
        else:
            container.append(obj)

        # to propperly sync refs between objects
        # typically artists exist before tracks or albums
        # so we have to update them of the new object
        #
        # other times the object may exist before the artist does
        # so when adding an artist check for anything that it should be aware of

        if pool in ('_tracks', '_albums'):
            # update other
            for parent in obj.artists:
                if obj not in parent.tracks:
                    parent._cache[obj.id] = obj

            if pool == '_tracks' and not obj.is_simple:
                if obj not in obj.album.tracks:
                    obj.album._cache[obj.id] = obj

        elif pool == '_artists':
            # update self
            for parent in (self._albums, self._tracks):
                for child in parent:
                    if obj in child.artists and child.id not in obj._cache:
                        obj._cache[child.id] = child

    def stats(self):
        get_mem = lambda seq: sum((*map(lambda i: sys.getsizeof(i), seq),))
        return {
            'artists': (len(self._artists), get_mem(self._artists)),
            'albums': (len(self._albums), get_mem(self._albums)),
            'tracks': (len(self._tracks), get_mem(self._tracks))
        }
