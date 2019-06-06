import gi
import sys
import threading
from .youtube import *

gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)


def rewind_callback(player):
	rc, pos_int = player.query_position(Gst.Format.TIME)
	seek_ns = pos_int - 10 * 1000000000
	if seek_ns < 0:
		seek_ns = 0
	player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)
		
def forward_callback(player):
	rc, pos_int = player.query_position(Gst.Format.TIME)
	seek_ns = pos_int + 10 * 1000000000
	player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

def create_player(url):
	music_stream_uri = extract_audio_url(url)[0]

	if not music_stream_uri:
		print("Failed to create player")
		sys.exit(1)
	
	# Create a custom bin element, that will serve as audio sink to
	# player bin. Audio filters will be added to this sink.
	audio_sink = Gst.Bin.new('audiosink')
	
	# Create element to attenuate/amplify the signal
	amplify = Gst.ElementFactory.make('audioamplify')
	amplify.set_property('amplification', 1)
	audio_sink.add(amplify)

	# Create element to play the pipeline to hardware
	sink = Gst.ElementFactory.make('autoaudiosink')
	audio_sink.add(sink)

	amplify.link(sink)
	audio_sink.add_pad(Gst.GhostPad.new('sink', amplify.get_static_pad('sink')))

	# Create playbin and add the custom audio sink to it
	player = Gst.ElementFactory.make("playbin", "player")
	player.props.audio_sink = audio_sink

	#set the uri
	player.set_property('uri', music_stream_uri)

	loop = GObject.MainLoop()

	return player, loop


def play_audio(url):
	player, loop = create_player(url)
	
	threading.Thread(target=loop.run).start()

	# Let user stop player gracefully
	control = " "
	player.set_state(Gst.State.PLAYING)
	state = "Playing"
	
	while True:
		control = input(f"{state}: STOP/PLAY-PAUSE/FF/RR/QUIT (s/p/l/j/q) : ")
		
		if control.lower() == "s" or control.lower() == "":
			player.set_state(Gst.State.NULL)
			loop.quit()
			break

		elif control.lower() == "p":
			if state == "Playing":
				player.set_state(Gst.State.PAUSED)
				state = "Paused"
			else:
				player.set_state(Gst.State.PLAYING)
				state = "Playing"
		elif control.lower() == 'l':
			forward_callback(player)
		elif control.lower() == 'j':
			rewind_callback(player)
		elif control.lower() == 'q':
			player.set_state(Gst.State.NULL)
			loop.quit()
			sys.exit(0)		
		


