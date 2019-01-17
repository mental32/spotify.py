import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():

    # spotify.Track object
    track = await client.get_track(track_id)

    # spotify.Album object
    album = await client.get_album(album_id)

    # spotify.Artist object
    artist = await client.get_artist(artist_id)

    # spotify.User object
    user = await client.get_user(user_id)

    # spotify.User object with a http presence
    user = await client.user_from_token(user_token)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
