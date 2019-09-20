import spotify


class SpotifyBase:
    """The base class all Spotify models **must** derive from.

    This base class is used to transparently construct spotify
    models based on the :class:`spotify,Client` type.

    Currently it is used to detect whether a Client is a syncronous
    client and, if as such, construct and return the appropriate
    syncronous model.
    """

    __slots__ = ()

    def __new__(cls, client, *_, **__):
        if not isinstance(client, spotify.Client):
            raise TypeError(
                f"{cls!r}: expected client argument to be an instance of spotify.Client. instead got {type(client)}"
            )

        if hasattr(client, "__client_thread__"):
            cls = getattr(
                spotify.sync.models, cls.__name__
            )  # pylint: disable=self-cls-assignment

        return object.__new__(cls)

    async def from_href(self):
        """Get the full object from spotify with a `href` attribute.

        .. note ::

            This can be used to get an updated model of the object.

        Returns
        -------
        model : SpotifyBase
            An instance of whatever the class was before.

        Raises
        ------
        TypeError
            This is raised if the model has no `href` attribute.

            Additionally if the model has no `http` attribute and
            the model has no way to access its client, while theoretically
            impossible its a failsafe, this will be raised.
        """
        if not hasattr(self, "href"):
            raise TypeError(
                "Spotify object has no `href` attribute, therefore cannot be retrived"
            )

        if hasattr(self, "http"):
            return await self.http.request(
                ("GET", self.href)
            )  # pylint: disable=no-member

        klass = type(self)

        try:
            client = getattr(self, "_{0}__client".format(klass.__name__))
        except AttributeError:
            raise TypeError("Spotify object has no way to access a HTTPClient.")
        else:
            http = client.http  # pylint: disable=no-member

        data = await http.request(("GET", self.href))  # pylint: disable=no-member

        return klass(client, data)


class URIBase(SpotifyBase):
    """Base class used for inheriting magic methods for models who have URIs.

    This class inherits from :class:`SpotifyBase` and is used to reduce boilerplate
    in spotify models by supplying a `__eq__`, `__ne__`, and `__str__` double underscore
    methods.

    The objects that inherit from :class:`URIBase` support equality and string casting.

     - Two objects are equal if **They are strictly the same type and have the same uri**
     - Casting to a string will return the uri of the object.
    """

    def __hash__(self):
        return hash(self.uri)  # pylint: disable=no-member

    def __eq__(self, other):
        return (
            type(self) is type(other) and self.uri == other.uri
        )  # pylint: disable=no-member

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.uri  # pylint: disable=no-member
