import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
    results = await client.search('drake')

    # spotify.Client.search returns a dict
    # the keys are the result types
    # the values are the items returned from the query for that type
    #
    # {
    #     'artists': [spotify.Artist, ...],
    #     'albums': [spotify.Album, ...],
    #     'playlists': [spotify.Playlist, ...],
    #     'tracks': [spotify.Track, ...]
    # }

    # Filtering search types
    # by default the results returns all types until a filter is applied
    # Here we only look for Artists and Tracks with the search query
    results = await client.search('drake', types=['artist', 'track'])

    # You can also apply a limit to the amount of items returned with the limit kwarg
    # You can set an offset to tell spotify where to start from with the offset kwarg
    # You can even filter individual markets with the market kwarg (ISO 3166-1 alpha-2 country code).
    results = await client.search('drake', limit=5, offset=20, market='JP')

if __name__ == '__main__':
    asyncio.loop.run_until_complete(main())
