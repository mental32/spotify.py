import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
    user = await client.user_from_token('sometoken')

    ### Add from a spotify track id
    track_id = '0HVv5bEOiI9a0QfgcASXpX'

    await user.library.add_track(track_id)

    ### Add from a spotify.Track object
    track_obj = await client.get_track(track_id)

    await user.library.add_track(track_obj)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
