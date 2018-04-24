# spotify.py

spotify.py is an asynchronous API wrapper for Spotify written in Python.


Here's an example on how to use it, here we load all of drakes albums and tracks and display them.
It's not really usefull but fun to watch.
```py
import spotify

client = spotify.Client(client_id='someid', client_secret='somesecret')

async def view_artist(spotify_id):
    artist = await client.get_artist(spotify_id)

    for album in await artist.load_all_albums():
        print(album.id, album.name)
        for track in await album.get_tracks():
            print('\t', track.id, track.name, track.artists)
        print()

if __name__ == '__main__':
    drake = '3TVXtAsR1Inumwj472S9r4'
    client.loop.run_until_complete(view_artist(drake))
```
[Official discord](https://discord.gg/zRUBc9Z)
