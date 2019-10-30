import asyncio
import unittest
from types import ModuleType

from common import *


class TestArtist(unittest.TestCase):
    @async_with_client(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    async def test_artist(self, *, client):
        for artist_uri in TEST_ARTISTS:
            artist = await client.get_artist(artist_uri)

            await async_chain([
                artist.get_albums(),
                artist.get_all_albums(),
                artist.total_albums(),
                artist.top_tracks(),
                artist.related_artists()
            ])

if __name__ == '__main__':
    unittest.main()
