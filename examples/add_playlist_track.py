import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
	user = await client.user_from_token('sometoken')

	# Get the first of the users playlists
	# This can also just be a playlist id :str:
	playlist = (await user.get_playlists())[0]

	### Add from a spotify track id
	track_id = '0HVv5bEOiI9a0QfgcASXpX'

	await user.add_tracks(playlist, track_id)

	### Add from a spotify.Track object
	track_obj = await client.get_track(track_id)

	await user.add_tracks(playlist, track_obj)

if __name__ == '__main__':
	asyncio.loop.run_until_complete(main())
