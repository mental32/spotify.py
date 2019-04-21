![Version info](https://img.shields.io/pypi/v/spotify.svg)
[![GitHub stars](https://img.shields.io/github/stars/mental32/spotify.py.svg)](https://github.com/mental32/spotify.py/stargazers)
# spotify.py

An API library for the spotify client and the Spotify Web API written in Python.

> spotify.py is in beta, there may be bugs.

spotify.py is 100% asyncronous meaning everything down to the HTTP library is designed to work with asyncio.<br>The library offers coverage over every endpoint in the Spotify web API.

## Simple example

- Top tracks (drake)

```py
import spotify

client = spotify.Client('someid', 'sometoken')

async def example():
    drake = await client.get_artist('3TVXtAsR1Inumwj472S9r4')

    for track in await drake.top_tracks():
        print(repr(track))
```

## Installing

To install the library simply clone it and run setup.py
- `git clone https://github.com/mental32/spotify.py`
- `python3 setup.py install`

or use pypi

- `pip3 install spotify` (latest stable release)
- `pip3 install -U git+https://github.com/mental32/spotify.py` (bleeding edge)

## Resources

For resources look at the [examples](https://github.com/mental32/spotify.py/tree/master/examples) or ask in the [discord](https://discord.gg/k43FSFF)

## Contributing
To contribute you must:
- fork and open a PR with changes.
