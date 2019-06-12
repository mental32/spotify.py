import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
    artist = await client.get_artist('spotify:artist:3TVXtAsR1Inumwj472S9r4')

    related_artists = await artist.related_artists()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
