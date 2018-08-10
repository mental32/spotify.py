import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
	# list of spotify.Album objects
	albums = await client.get_albums(album_id, ...)

	# list of spotify.Artist objects
	artists = await client.get_artists(artist_id, ...)

if __name__ == '__main__':
	asyncio.loop.run_until_complete(main())
