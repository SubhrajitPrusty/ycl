import gi
import sys
import curses
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

def get_player_pos(player):
	rc, pos_int = player.query_position(Gst.Format.TIME)
	rc, dur_nano = player.query_duration(Gst.Format.TIME)
	seconds_curr = pos_int // 10**9
	mins_curr = seconds_curr // 60
	secs_curr= seconds_curr % 60

	seconds_tot = dur_nano // 10**9
	mins_tot = seconds_tot // 60
	secs_tot = seconds_tot % 60

	return "{:02d}:{:02d}/{:02d}:{:02d}".format(mins_curr, secs_curr, mins_tot, secs_tot)

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


def play_audio(url, title=None):
	player, loop = create_player(url)
	
	threading.Thread(target=loop.run).start()

	stdscr = curses.initscr()
	curses.cbreak()
	curses.noecho()
	stdscr.clear()
	stdscr.keypad(True)
	stdscr.nodelay(1)

	# Let user stop player gracefully
	control = " "
	player.set_state(Gst.State.PLAYING)
	state = "Playing"
	
	if title:
		stdscr.addstr(0, 0, f"Playing {title}")
	
	try:
		while True:
			pos = get_player_pos(player)
			stdscr.addstr(1, 0, f"{state}: {pos} ") 
			stdscr.hline(2, 0, curses.ACS_HLINE, int(curses.COLS))
			stdscr.addstr(4, 0, "Controls : ")
			stdscr.addstr(5, 0, "s: STOP")
			stdscr.addstr(6, 0, "p: Toggle PLAY/PAUSE")
			stdscr.addstr(7, 0, "->: Seek 10 seconds forward")
			stdscr.addstr(8, 0, "<-: Seek 10 seconds backward")
			stdscr.addstr(9, 0, "q: Quit")

			control = stdscr.getch()

			if control == ord("s"):
				player.set_state(Gst.State.NULL)
				loop.quit()
				break

			elif control == ord("p"):
				if state == "Playing":
					player.set_state(Gst.State.PAUSED)
					state = "Paused"
				else:
					player.set_state(Gst.State.PLAYING)
					state = "Playing"
			elif control == curses.KEY_RIGHT:
				forward_callback(player)
			elif control == curses.KEY_LEFT:
				rewind_callback(player)
			elif control == ord('q'):
				player.set_state(Gst.State.NULL)
				loop.quit()
				curses.endwin()
				print("Quitting...\n")
				sys.exit(0)
	finally:
		curses.endwin()
		print("\rStopping player...", end="")
