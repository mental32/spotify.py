class Image:
    """An object representing a Spotify image resource.

    Attributes
    ----------
    height : str
        The height of the image.
    width : str
        The width of the image.
    url : str
        The URL of the image.
    """

    __slots__ = ('height', 'width', 'url')

    def __init__(self, *, height: str, width: str, url: str):
        self.height = height
        self.width = width
        self.url = url

    def __repr__(self):
        return '<spotify.Image: "%s" (width: %s, height: %s)>' % (self.url, self.width, self.height)

    def __eq__(self, other):
        return type(self) is type(other) and self.url == other.url


class Context:
    """  # TODO: Add Context documenataion.
    """
    __slots__ = ('external_urls', 'type', 'href', 'uri')

    def __init__(self, data):
        self.external_urls = data.get('external_urls')
        self.type = data.get('type')

        self.href = data.get('href')
        self.uri = data.get('uri')

    def __repr__(self):
        return '<spotify.Context: "%s">' % (self.uri)

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri


class Device:
    """  # TODO: Add Device documentation.
    """
    __slots__ = ('id', 'name', 'type', 'volume', 'is_active', 'is_restricted')

    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.type = data.get('type')

        self.volume = data.get('volume_percent')

        self.is_active = data.get('is_active')
        self.is_restricted = data.get('is_restricted')

    def __eq__(self, other):
        return type(self) is type(other) and self.id == other.id

    def __repr__(self):
        return '<spotify.Device: "%s">' % (self.name or self.id)
