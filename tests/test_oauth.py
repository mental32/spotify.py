import unittest
from urllib.parse import quote_plus as quote

from common import *


class TestOAuth(unittest.TestCase):

    @async_with_client("foo", "bar")
    async def test_oauth_passive(self, *, client):
        kwargs = {
            "redirect_uri": "https://google.com",
            "scopes": ("user-read-currently-playing",),
        }

        oauth = spotify.OAuth2.from_client(client, **kwargs)

        attrs = {
            "client_id": client.http.client_id,
            "redirect_uri": quote(kwargs["redirect_uri"]),
            "scope": quote("user-read-currently-playing"),
        }

        parameters = f"client_id={attrs['client_id']}&redirect_uri={attrs['redirect_uri']}&scope={attrs['scope']}"

        scopes = frozenset(kwargs["scopes"])

        url = (
            "https://accounts.spotify.com/authorize/?response_type=code&"
            + parameters
        )

        self.assertTrue(str(oauth) == url)
        self.assertTrue(oauth.scopes == scopes)
        self.assertTrue(oauth.attributes == attrs)
        self.assertTrue(oauth.parameters == parameters)

        oauth.set_scopes(**{"user-top-read": True, "user-read-currently-playing": False})
        scopes = frozenset(("user-top-read",))
        self.assertTrue(oauth.scopes == scopes)


if __name__ == '__main__':
    unittest.main()
