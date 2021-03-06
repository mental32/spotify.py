from functools import partial
from typing import Any, Dict, List, Optional, Union

from ..http import HTTPClient
from ..oauth import set_required_scopes
from . import AsyncIterable, Image, URIBase


class Episode(URIBase):
    """A Spotify Episode.

    Attributes
    ----------
    id : :class:`str`
        The Spotify ID for the episode.
    preview_url : :class:`str`
        The preview URL for the Episode.
    description : :class:`str`
        The episode description.
    duration : int
        The episode length in milliseconds.
    languages : :class:`str`
        The languages that show is available to listen.
    explicit : bool
        Whether or not the episode has explicit
        `True` if it does.
        `False` if it does not (or unknown)
    href : :class:`str`
        A link to the Web API endpoint providing full details of the episode.
    images : List[Image]
        The images of the Episode.
    url : :class:`str`
        The open.spotify URL.
    name : :class:`str`
        The name of the episode.
    type : :class:`str`
        The type of the Episode.
    uri : :class:`str`
        The Spotify URI for the episode.
    release_date : str
        The date the episode was first released.
    release_date_precision : str
        The precision with which release_date value is known: year, month or day.
    externally_hosted : bool
        Whether or not the episode has externally hosted or not.
        `True` if it does.
        `False` if it does not (or unknown)
    """

    def __init__(self, client, data):

        self.__client = client

        self.preview_url = data.pop("audio_preview_url", None)
        self.description = data.pop("description", None)
        self.duration = data.pop("duration_ms", None)
        self.explicit = data.pop("explicit", None)
        self.external_urls = data.pop("external_urls").get("spotify", None)
        self.href = data.pop("href", None)
        self.id = data.pop("id", None)
        self.externally_hosted = data.pop("is_externally_hosted", None)
        self.playable = data.pop("is_playable", None)
        self.languages = data.pop("languages", None)
        self.name = data.pop("name", None)
        self.release_date = data.pop("release_date", None)
        self.release_date_presicion = data.pop("release_date_precision", None)
        self.type = data.pop("episode", None)
        self.uri = data.pop("uri", None)

        show_ = data.pop("show", None)
        self.show = show = show_ and Show(client, show_)

        if "images" in data:
            self.images = list(Image(**img) for img in data.pop("images"))
        else:
            self.images = show.images.copy() if show is not None else []

    def __repr__(self) -> str:
        return f"<spotify.Episode: {self.name!r}>"

    def __str__(self) -> str:
        return self.id


class Show(URIBase, AsyncIterable):
    """A Spotify Show Object.

    Attributes
    ----------
    id : :class:`str`
        The Spotify ID for the show.
    copyrights : List[Dict]
        The copyright statements of the show.
    description : :class:`str`
        The show description.
    languages : :class:`str`
        The languages that show is available to listen.
    duration : int
        The show length in milliseconds.
    explicit : bool
        Whether or not the show has explicit
        `True` if it does.
        `False` if it does not (or unknown)
    href : :class:`str`
        A link to the Web API endpoint providing full details of the episodes.
    images : List[Image]
        The images of the show.
    available_markets : List[:class:`str`]
        The available markets for the show.
    url : :class:`str`
        The open.spotify URL.
    name : :class:`str`
        The name of the show.
    type : :class:`str`
        The type of the show.
    uri : :class:`str`
        The Spotify URI for the show.
    total_episodes : :class:`int`
        The number of total episodes.
    media_type : :class:`string`
        The media type to of the show.
    externally_hosted : :class:`bool`
        Whether or not the show is externally hosted or not.
        `True` if it does.
        `False` if it does not (or unknown)
    publisher: :class:`str`
        The publisher of the show.
    episodes: :class:`List[spotify.Episode]`
        A list of episodes.
    """

    def __init__(self, client, data):
        self.__client = client

        self.available_markets = data.pop("available_markets", None)
        self.copyrights = data.pop("copyrights", None)
        self.description = data.pop("description", None)
        self.explicit = data.pop("explicit", None)
        self.external_urls = data.pop("external_urls").get("spotify", None)
        self.href = data.pop("href", None)
        self.id = data.pop("id", None)

        self.images = list(Image(**image) for image in data.pop("images", None))
        self.externally_hosted = data.pop("is_externally_hosted", None)
        self.languages = data.pop("languages", None)
        self.media_type = data.pop("media_type", None)
        self.name = data.pop("name", None)
        self.publisher = data.pop("publisher", None)
        self.total_episodes = data.pop("total_episodes", None)
        self.type = data.pop("type", None)
        self.uri = data.pop("uri", None)

        self.episodes = list(
            Episode(client, episode) for episode in data.pop("episodes", {})
        )

        # AsyncIterable attrs
        self.__aiter_klass__ = Episode
        self.__aiter_fetch__ = partial(
            self.__client.http.get_shows_episodes, self.id, limit=50
        )

    def __repr__(self) -> str:
        return f"<spotify.Show: {self.name!r}>"

    def __str__(self):
        return self.id


class Podcast(URIBase, AsyncIterable):
    """A Spotify Podcast.

    date_added: :class:`str`
        The publish date of the podcast.
    show: :class:`spotify.Show`
        A spotify Show object.
    """

    def __init__(
        self,
        client,
        data: Dict[str, Any],
        *,
        http: Optional[HTTPClient] = None,
    ):
        self.__client = client
        self.__http = http or client.http

        assert self.__http is not None

        if not isinstance(data, (Podcast, dict)):
            raise TypeError("data must be a Podcast instance or a dict.")

        self.added_at = data.pop("added_at", None)

        self.show = Show(client, data.pop("show", None))

    def __str__(self) -> str:
        return self.show.id

    def __repr__(self) -> str:
        return f"<spotify.Podcast: {self.show.name}>"

    @set_required_scopes("user-read-playback-position")
    async def get_all_episodes(self) -> List[Episode]:
        """Get all playlist episodess from the playlist.

        Returns
        -------
        episodes : List[:class:`Episode`]
            The all episodes of a Podcast.
        """
        episodes: List[Episode] = []
        offset = 0

        if self.show.total_episodes is None:
            self.show.total_episodes = (
                await self.__http.get_shows_episodes(self.show.id, limit=1, offset=0)
            )["total"]

        while len(episodes) < self.show.total_episodes:
            data = await self.__http.get_shows_episodes(
                self.show.id, limit=50, offset=offset
            )

            episodes += [Episode(self.__client, item) for item in data["items"]]
            offset += 50

        self.show.total_episodes = len(episodes)
        return episodes
