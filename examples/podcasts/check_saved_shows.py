import asyncio
import spotify

client = spotify.Client("some id", "some secret")


async def main():

    user = await client.user_from_token("token")

    show_ids = ["5CfCWKI5pZ28U0uOzXkDHe", "5as3aKmN2k11yfDDDSrvaZ"]
    shows = await client.get_multiple_shows(show_ids)

    podcasts = await user.library.check_saved_shows(*shows)

    print(podcasts)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
