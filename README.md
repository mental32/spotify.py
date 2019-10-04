![logo](/docs/source/images/logo.png)


![Version info](https://img.shields.io/pypi/v/spotify.svg)
[![GitHub stars](https://img.shields.io/github/stars/mental32/spotify.py.svg)](https://github.com/mental32/spotify.py/stargazers)
![Discord](https://img.shields.io/discord/438465139197607939.svg?style=flat-square)

# spotify.py

An API library for the spotify client and the Spotify Web API written in Python.

Spotify.py is an asyncronous API library for Spotify. While maintaining an
emphasis on being purely asyncronous the library provides syncronous
functionality with the `spotify.sync` module.

```python
import spotify.sync as spotify  # Nothing requires async/await now!
```

## Index

 - [Installing](#Installing)
 - [Examples](#Examples)
 - [Resources](#Resources)

## Installing

To install the library simply clone it and run setup.py
- `git clone https://github.com/mental32/spotify.py`
- `python3 setup.py install`

or use pypi

- `pip3 install spotify` (latest stable)
- `pip3 install -U git+https://github.com/mental32/spotify.py` (nightly)

## Examples
### Sorting a playlist by popularity

```py
import sys

import spotify

playlist_uri =   # Playlist uri here
client_id =      # App client id here
secret =         # App secret here
token =          # User token here

client = spotify.Client(client_id, secret)

async def main():
    user = await spotify.User.from_token(client, token)

    for playlist in await user.get_playlists():
        if playlist.uri == playlist_uri:
            await playlist.sort(reverse=True, key=(lambda track: track.popularity))
            break
    else:
        print('No playlists were found!', file=sys.stderr)

if __name__ == '__main__':
    client.loop.run_until_complete(main())
```

### Usage with flask

```py
import string
import random
from typing import Tuple, Dict

import flask
import spotify.sync as spotify

SPOTIFY_CLIENT = spotify.Client('SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET')

APP = flask.Flask(__name__)
APP.config.from_mapping({'spotify_client': SPOTIFY_CLIENT})

REDIRECT_URI: str = 'http://localhost:8888/spotify/callback'

OAUTH2_SCOPES: Tuple[str] = ('user-modify-playback-state', 'user-read-currently-playing', 'user-read-playback-state')
OAUTH2: spotify.OAuth2 = spotify.OAuth2(SPOTIFY_CLIENT.id, REDIRECT_URI, scope=OAUTH2_SCOPES)

SPOTIFY_USERS: Dict[str, spotify.User] = {}


@APP.route('/spotify/callback')
def spotify_callback():
    try:
        code = flask.request.args['code']
    except KeyError:
        return flask.redirect('/spotify/failed')
    else:
        key = ''.join(random.choice(string.ascii_uppercase) for _ in range(16))
        SPOTIFY_USERS[key] = spotify.User.from_code(
            SPOTIFY_CLIENT,
            code,
            redirect_uri=REDIRECT_URI,
            refresh=True
        )

        flask.session['spotify_user_id'] = key

    return flask.redirect('/')

@APP.route('spotify/failed')
def spotify_failed():
    flask.session.pop('spotify_user_id', None)
    return 'Failed to authenticate with Spotify.'

@APP.route('/')
@APP.route('/index')
def index():
    try:
        return repr(SPOTIFY_USERS[flask.session['spotify_user_id']])
    except KeyError:
        return flask.redirect(OAUTH2.url)

if __name__ == '__main__':
    APP.run('127.0.0.1', port=8888, debug=False)
```

## Resources

For resources look at the [examples](https://github.com/mental32/spotify.py/tree/master/examples) or ask in the [discord](https://discord.gg/k43FSFF)
