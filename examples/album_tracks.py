import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
	album = await client.get_album('spotify:album:1ATL5GLyefJaxhQzSPVrLX')

	# Get all the tracks at once
	all_tracks = await album.get_all_tracks()

	# Getting tracks using limits and offsets
	some_tracks = await album.get_tracks(limit=5, offset=10)

if __name__ == '__main__':
	asyncio.loop.run_until_complete(main())
