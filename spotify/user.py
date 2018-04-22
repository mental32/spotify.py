##
# -*- coding: utf-8 -*-
##
from .http import HTTPUserClient
from .model import SpotifyModel, Image

class User(SpotifyModel):
    __slots__ = ['http', 'display_name', 'external_urls', 'followers', 'id', 'href', 'uri', 'images', 'birthdate', 'country', 'email', 'premium', 'private', 'scopes']

    def __init__(self, **kwargs):
        if kwargs.get('token'):
            self.http = HTTPUserClient(kwargs.get('token'))

        if kwargs.get('data'):
            self._parse(kwargs.get('data'), kwargs.get('private', False))

    def _parse(self, data, private=False):
        self.display_name = data.get('display_name')
        self.external_urls = data.get('external_urls')
        self.followers = data.get('followers').get('total')

        self.id = data.get('id')
        self.href = data.get('href')
        self.uri = data.get('uri')

        self.images = [Image(**image) for image in data.get('images')]

        if private:
            self.birthdate = data.get('birthdate')
            self.country = data.get('country')
            self.email = data.get('email')
            self.premium = (data.get('product') == 'premium')

    def __repr__(self):
        try:
            return '<spotify.User: "%s">' %(self.display_name)
        except AttributeError:
            return '<spotify.User: BLANK_USER>'
