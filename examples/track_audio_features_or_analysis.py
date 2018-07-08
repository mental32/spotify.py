import asyncio
import spotify

client = spotify.Client('someid', 'somesecret')

async def main():
	track = client.get_track(track_id)

	audio_features = await track.audio_features()
	audio_analysis = await track.audio_analysis()

if __name__ == '__main__':
	asyncio.loop.run_until_complete(main())
