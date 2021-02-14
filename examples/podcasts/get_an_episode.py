import asyncio
import spotify

client = spotify.Client("some id", "some secret")


async def main():

    episode_id = "27SyhdfgURYPhw4JSSEPVs"
    episode = await client.get_episode(episode_id)

    print(episode.name, episode.description)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
