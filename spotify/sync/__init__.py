import signal

from .sync import SyncExecution

_thread = SyncExecution()
_thread.start()

from .cls import (
	HTTPClient, 
	HTTPUserClient, 
	Client, 
	Track, 
	User, 
	PlaylistTrack, 
	Artist, 
	Album, 
	Playlist, 
	Library
)

signal.signal(signal.SIGINT, signal.SIG_DFL)
