##
# -*- coding: utf-8 -*-
##
import functools

class _spotify__lookup(dict):

	def artist(self, *args, **kwargs):
		return self['artist'](*args, **kwargs)

	def track(self, *args, **kwargs):
		return self['track'](*args, **kwargs)

	def user(self, *args, **kwargs):
		return self['user'](*args, **kwargs)

	def playlist(self, *args, **kwargs):
		return self['playlist'](*args, **kwargs)

	def album(self, *args, **kwargs):
		return self['album'](*args, **kwargs)

	def library(self, *args, **kwargs):
		return self['library'](*args, **kwargs)


_types = _spotify__lookup()

from .errors import *
from .models import *

from .client import Client, _types

__title__ = 'spotify'
__author__ = 'mental'
__license__ = 'MIT'
__version__ = '0.1.1'
