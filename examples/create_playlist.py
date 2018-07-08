import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
	user = await client.user_from_token('sometoken')

	# create a spotify playlist
	# and return a spotify.Playlist object
	playlist = await user.create_playlist('myplaylist', description='relaxing songs')

if __name__ == '__main__':
	asyncio.loop.run_until_complete(main())
