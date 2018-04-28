# spotify.py

spotify.py is an asynchronous API wrapper for Spotify written in Python.

## installing
To install the library simply clone it and run setup.py
- `git clone https://github.com/mental32/spotify.py`
- `python3 setup.py install`

> this branch is currently unstable and is updated weekly.

## resources

[Official discord](https://discord.gg/zRUBc9Z)

Here's an example on how to use it, here we load all of drakes albums and tracks and display them.
It's not really usefull but fun to watch.

```py
import spotify

client = spotify.Client(client_id='someid', client_secret='somesecret')

async def view_artist(spotify_id):
    artist = await client.get_artist(spotify_id)

    # This method returns a shallow copy of the album objects
    # you could iterate over it directly but it can be called anywhere
    # and then iterate over `artist.albums`
    await artist.load_all_albums() 

    for album in artist.albums:
        print(album.id, album.name)
        # album.get_tracks uses the same design as `Artist.load_all_albums` (see above comment)
        for track in await album.get_tracks():
            print('\t', track.id, track.name, track.artists)
        print()

if __name__ == '__main__':
    drake = '3TVXtAsR1Inumwj472S9r4'
    client.loop.run_until_complete(view_artist(drake))
```
[read the docs](http://spotifypy.readthedocs.io/en/latest/) (Not complete!)
