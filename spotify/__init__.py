##
# -*- coding: utf-8 -*-
##

"""
Spotify API Wrapper

A basic wrapper for the Spotify API.
"""

__title__ = 'spotify'
__author__ = 'mental'
__license__ = 'MIT'
__version__ = '0.0.2'

from . import utils

from .user import User
from .client import Client

from .album import Album
from .artist import Artist
from .playlist import Playlist

from .model import Image
from .errors import *
