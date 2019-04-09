![Version info](https://img.shields.io/pypi/v/spotify.svg)
[![GitHub stars](https://img.shields.io/github/stars/mental32/spotify.py.svg)](https://github.com/mental32/spotify.py/stargazers)
# spotify.py

An API library for the spotify client and the Spotify Web API written in Python.

spotify.py is 100% asyncronous meaning everything down to the HTTP library is designed to work with asyncio.<br>The library offers coverage over every endpoint in the Spotify web API.


As of v0.1.5 it is possible to use spotify.py in a syncronous manner. No await/async syntax required! To do this simply use

```py
import spotify.sync as spotify # and now no methods require the async/await syntax.
```

Added in v0.3.0 it's now possible to have self refreshing User sessions, this update allows for users to hand off the second half of the OAuth flow directly to the library which will ensure an authenticated session for the duration of the User objects lifetime. See the [example](examples/user_auth.py)!

## Examples

- Top tracks (drake)

```py
import spotify

client = spotify.Client('someid', 'sometoken')

async def example():
    drake = await client.get_artist('3TVXtAsR1Inumwj472S9r4')

    for track in await drake.top_tracks():
        print(repr(track))
```

- Backing up playlists

```py
import json
import time

import spotify
from spotify import User

client = spotify.Client('someid', 'sometoken')

async def backup():
    user = await User.from_token(client, 'sometoken')
    backup_data = []

    for playlist in await user.get_playlists():

        backup_data.append({
            'metadata': [playlist.name, playlist.public, playlist.collaborative, playlist.description], 
            'tracks': []
        })

        for track in await playlist.get_tracks():
            backup_data[-1]['tracks'].append(track.uri)

    with open('spotify_playlists_%s_%s.json' % (user.id, int(time.time())), 'w') as file:
        json.dump(backup_data, file)
```

## Resources

For resources look at the [examples](https://github.com/mental32/spotify.py/tree/master/examples) or ask in the [discord](https://discord.gg/k43FSFF)

## Installing

To install the library simply clone it and run setup.py
- `git clone https://github.com/mental32/spotify.py`
- `python3 setup.py install`

or use pypi

- `pip3 install spotify`
- `pip3 install -U git+https://github.com/mental32/spotify.py` (recommened)

## Contributing
To contribute you must:
- have a presence in the [discord](https://discord.gg/k43FSFF) server
- fork and open a PR with changes.

> spotify.py is in beta, there may be bugs.
