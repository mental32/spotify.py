import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
	user = await client.user_from_token('sometoken')

	# returns a list of spotify.Track objects
	tracks = await user.recently_played()

if __name__ == '__main__':
	asyncio.loop.run_until_complete(main())
