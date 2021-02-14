import asyncio
import spotify

client = spotify.Client("some id", "some secret")


async def main():

    user = await client.user_from_token("token")

    podcasts = await user.get_podcasts()

    print("saved podcasts:", podcasts)

    print(
        await user.library.remove_saved_shows(*podcasts[:2])
    )  # Delete first two podcast

    podcasts = await user.get_podcasts()
    print("podcasts after deletion", podcasts)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
