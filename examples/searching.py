import sys
import pprint

import spotify

client = spotify.Client(client_id='someid', client_secret='somesecret')

async def main():
    pprint.pprint(
        await client.search(' '.join(sys.argv[1:]))
    )

if __name__ == '__main__':
    client.loop.run_until_complete(main())
