import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
    user = await client.user_from_token('sometoken')

    # returns a list of spotify.Artist objects
    top_artists = await user.top_artists()

    # returns a list of spotif.Track objects
    top_tracks = await user.top_tracks()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
