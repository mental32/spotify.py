![logo](/docs/source/images/logo.png)


![Version info](https://img.shields.io/pypi/v/spotify.svg)
[![GitHub stars](https://img.shields.io/github/stars/mental32/spotify.py.svg)](https://github.com/mental32/spotify.py/stargazers)
![Discord](https://img.shields.io/discord/438465139197607939.svg?style=flat-square)

# spotify.py

An API library for the spotify client and the Spotify Web API written in Python.

Spotify.py is an, primarily, asyncronous library (everything down to the HTTP client is asyncio friendly). 

#### Sync' support

The library also supports **syncronous** usage with `spotify.sync`

```python
import spotify.sync as spotify  # Nothing requires async/await now!
```

## example

 - Sorting a playlist by popularity

```py
import spotify

playlist_uri =   # Playlist uri here
client_id =      # App client id here
secret =         # App secret here
token =          # User token here

client = spotify.Client(client_id, secret)

async def main():
    user = await spotify.User.from_token(client, token)

    playlist = next(filter((lambda playlist: playlist.uri == playlist_uri), await user.get_playlists()))
    tracks = await playlist.get_all_tracks()

    sorted_tracks = sorted(tracks, reverse=True, key=(lambda track: track.popularity))

    await user.replace_tracks(playlist, sorted_tracks)

if __name__ == '__main__':
    client.loop.run_until_complete(main())
```

## Installing

To install the library simply clone it and run setup.py
- `git clone https://github.com/mental32/spotify.py`
- `python3 setup.py install`

or use pypi

- `pip3 install spotify` (latest stable)
- `pip3 install -U git+https://github.com/mental32/spotify.py` (nightly)

## Resources

For resources look at the [examples](https://github.com/mental32/spotify.py/tree/master/examples) or ask in the [discord](https://discord.gg/k43FSFF)
