import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
	user = await client.user_from_token('sometoken')

	# Get the first of the users playlists
	# This can also just be a playlist id :str:
	playlist = (await user.get_playlists())[0]

	await user.replace_tracks(playlist)

if __name__ == '__main__':
	asyncio.loop.run_until_complete(main())
