<div align=center>

![logo](https://i.imgur.com/AYVfaC2.png)

![Version info](https://img.shields.io/pypi/v/spotify.svg?style=for-the-badge)![Github Issues](https://img.shields.io/github/issues/mental32/spotify.py?style=for-the-badge)![Github forks](https://img.shields.io/github/forks/mental32/spotify.py?style=for-the-badge)[![GitHub stars](https://img.shields.io/github/stars/mental32/spotify.py?style=for-the-badge)](https://github.com/mental32/spotify.py/stargazers)![License](https://img.shields.io/github/license/mental32/spotify.py?style=for-the-badge)![Travis](https://img.shields.io/travis/mental32/spotify.py?style=for-the-badge)

<hr>

</div>

# spotify.py

An API library for the spotify client and the Spotify Web API written in Python.

Spotify.py is an asynchronous API library for Spotify. While maintaining an
emphasis on being purely asynchronous the library provides syncronous
functionality with the `spotify.sync` module.

```python
import spotify.sync as spotify  # Nothing requires async/await now!
```

## Notice: Looking For Maintainers

The author of spotify.py considers it deprecated and is provided "as is".

_(of course depending on the user it may be considered feature complete)_

The author does not intend to continue working on it or providing support,
it may work or may not for the purposes it was designed for.

If you encounter an issue:

* open an issue and wait for a PR to come along and fix (you may be waiting a while)
* open a PR that introduces the fix directly (the author is happy to click a button labeled "merge")


## Index

 - [Installing](#Installing)
 - [Examples](#Examples)
 - [Resources](#Resources)

## Installing

To install the library simply clone it and run pip.
- `git clone https://github.com/mental32/spotify.py spotify_py`
- `cd spotify_py`
- `pip3 install -U .`

or use pypi

- `pip3 install -U spotify` (latest stable)
- `pip3 install -U git+https://github.com/mental32/spotify.py#egg=spotify` (nightly)

## Examples
### Sorting a playlist by popularity

```py
import sys
import getpass

import spotify

async def main():
    playlist_uri = input("playlist_uri: ")
    client_id = input("client_id: ")
    secret = getpass.getpass("application secret: ")
    token = getpass.getpass("user token: ")

    async with spotify.Client(client_id, secret) as client:
        user = await spotify.User.from_token(client, token)

        async for playlist in user:
            if playlist.uri == playlist_uri:
                return await playlist.sort(reverse=True, key=(lambda track: track.popularity))

        print('No playlists were found!', file=sys.stderr)

if __name__ == '__main__':
    client.loop.run_until_complete(main())
```

### Required oauth scopes for methods

```py
import spotify
from spotify.oauth import get_required_scopes

# In order to call this method sucessfully the "user-modify-playback-state" scope is required.
print(get_required_scopes(spotify.Player.play))  # => ["user-modify-playback-state"]

# Some methods have no oauth scope requirements, so `None` will be returned instead.
print(get_required_scopes(spotify.Playlist.get_tracks))  # => None
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
OAUTH2: spotify.OAuth2 = spotify.OAuth2(SPOTIFY_CLIENT.id, REDIRECT_URI, scopes=OAUTH2_SCOPES)

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
            redirect_uri=REDIRECT_URI
        )

        flask.session['spotify_user_id'] = key

    return flask.redirect('/')

@APP.route('/spotify/failed')
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

For resources look at the [examples](https://github.com/mental32/spotify.py/tree/master/examples)
