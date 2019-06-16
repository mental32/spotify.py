"""Type annotation aliases for other Spotify models."""

from typing import Union, Sequence

from .base import URIBase

SomeURI = Union[URIBase, str]
SomeURIs = Sequence[Union[URIBase, str]]
OneOrMoreURIs = Union[SomeURI, Sequence[SomeURI]]
