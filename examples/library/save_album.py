import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
    user = await client.user_from_token('sometoken')

    ### Add from a spotify album id
    album_id = '2o9McLtDM7mbODV7yZF2mc'

    await user.library.add_album(album_id)

    ### Add from a spotify.Album object
    album_obj = await client.get_album(album_id)

    await user.library.add_album(album_obj)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
