class Image:
    """An object representing a Spotify image resource.

    Attributes
    ----------
    height : :class:`str`
        The height of the image.
    width : :class:`str`
        The width of the image.
    url : :class:`str`
        The URL of the image.
    """

    __slots__ = ("height", "width", "url")

    def __init__(self, *, height: str, width: str, url: str):
        self.height = height
        self.width = width
        self.url = url

    def __repr__(self):
        return f"<spotify.Image: {self.url!r} (width: {self.width!r}, height: {self.height!r})>"

    def __eq__(self, other):
        return type(self) is type(other) and self.url == other.url


class Context:
    """A Spotify Context.

    Attributes
    ----------
    type : str
        The object type, e.g. “artist”, “playlist”, “album”.
    href : str
        A link to the Web API endpoint providing full details of the track.
    external_urls : str
        External URLs for this context.
    uri : str
        The Spotify URI for the context.
    """

    __slots__ = ("external_urls", "type", "href", "uri")

    def __init__(self, data):
        self.external_urls = data.get("external_urls")
        self.type = data.get("type")

        self.href = data.get("href")
        self.uri = data.get("uri")

    def __repr__(self):
        return f"<spotify.Context: {self.uri!r}>"

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri


class Device:
    """A Spotify Users device.

    Attributes
    ----------
    id : str
        The device ID
    name : int
        The name of the device.
    type : str
        A Device type, such as “Computer”, “Smartphone” or “Speaker”.
    volume : int
        The current volume in percent. This may be null.
    is_active : bool
        if this device is the currently active device.
    is_restricted : bool
        Whether controlling this device is restricted.
        At present if this is “true” then no Web API commands will be accepted by this device.
    is_private_session : bool
        If this device is currently in a private session.
    """

    __slots__ = (
        "id",
        "name",
        "type",
        "volume",
        "is_active",
        "is_restricted",
        "is_private_session",
    )

    def __init__(self, data):
        self.id = data.get("id")  # pylint: disable=invalid-name
        self.name = data.get("name")
        self.type = data.get("type")

        self.volume = data.get("volume_percent")

        self.is_active = data.get("is_active")
        self.is_restricted = data.get("is_restricted")
        self.is_private_session = data.get("is_private_session")

    def __eq__(self, other):
        return type(self) is type(other) and self.id == other.id

    def __repr__(self):
        return f"<spotify.Device: {(self.name or self.id)!r}>"

    def __str__(self):
        return self.id
