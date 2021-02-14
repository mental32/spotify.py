import asyncio
import spotify

client = spotify.Client("some id", "some secret")


async def main():

    user = await client.user_from_token("token")

    podcasts = await user.get_podcasts()
    first_podcast = podcasts[0]  # Get first podcasts from all podcasts
    episodes = await first_podcast.get_all_episodes()

    print(episodes)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
