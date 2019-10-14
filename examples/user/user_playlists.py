import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
    # You can use a user with a http presence
    user = await client.user_from_token('sometoken')

    # Or you can get a generic user
    user = await client.get_user(user_id)

    # returns a list of spotify.Playlist objects
    playlists = await user.get_playlists()

    # Or if you want to target all playlists
    all_playlists = await user.get_all_playlists()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
