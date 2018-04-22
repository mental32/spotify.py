##
# -*- coding: utf-8 -*-
##

class SpotifyModel:
    __slots__ = ['is_simple']

class Image:
    __slots__ = ['height', 'width', 'url']

    def __init__(self, *, height, width, url):
        self.height = height
        self.width = width
        self.url = url

    def __repr__(self):
        return '<spotify.Image (width: %s, height: %s)>' %(self.width, self.height)
