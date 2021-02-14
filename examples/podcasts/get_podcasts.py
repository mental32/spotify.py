import asyncio
import spotify

client = spotify.Client("some id", "some secret")


async def main():

    user = await client.user_from_token("token")

    podcasts = await user.get_podcasts()

    for podcast in podcasts:
        print(
            f"Added at: {podcast.added_at}, Name: {podcast.show.name}, Description: {podcast.show.description}",
        )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
