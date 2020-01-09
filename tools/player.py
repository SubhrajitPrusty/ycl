import sys
import time
import curses
from .youtube import *
from time import sleep
from ffpyplayer.player import MediaPlayer

LOOP=True

def rewind_callback(player, start=False):
	if start:
		player.seek(0, relative=False)
	else:
		player.seek(-10.0)
		
def forward_callback(player):
	player.seek(10.0)

def increase_volume(player):
	curr_vol = player.get_volume()
	curr_vol += 0.05
	curr_vol = 1.0 if curr_vol > 1.0 else curr_vol
	player.set_volume(curr_vol)
	
def decrease_volume(player):
	curr_vol = player.get_volume()
	curr_vol -= 0.05
	curr_vol = 0.0 if curr_vol < 0.0 else curr_vol
	player.set_volume(curr_vol)

def get_player_pos(player):
	pos_int = player.get_pts()
	dur_int = player.get_metadata()['duration']
	seconds_curr = pos_int 
	mins_curr = int(seconds_curr // 60)
	secs_curr = int(seconds_curr % 60)

	seconds_tot = dur_int
	mins_tot = int(seconds_tot // 60)
	secs_tot = int(seconds_tot % 60)
	
	return "{:02d}:{:02d}/{:02d}:{:02d}".format(mins_curr, secs_curr, mins_tot, secs_tot), seconds_curr, seconds_tot

def create_player(url):
	music_stream_uri = extract_video_url(url)[0]
	if not music_stream_uri:
		print("Failed to create player")
		sys.exit(1)
	
	ff_opts = {"vn": True, "sn": True} # only audio

	player = MediaPlayer(music_stream_uri, ff_opts=ff_opts, loglevel='debug')
	
	# refer : https://github.com/kivy/kivy/blob/52d12ebf33e410c9f4798674a93cbd0db8038bf1/kivy/core/audio/audio_ffpyplayer.py#L116
	# method to prevent crash on load - since the stream hasn't been downloaded sufficiently yet 

	player.toggle_pause()
	s = time.perf_counter()
	while (player.get_metadata()['duration'] is None and time.perf_counter() - s < 10.):
		time.sleep(0.005)
	
	return player

def get_vol(player):
	vol = int(player.get_volume()*100)
	if vol < 100:
		return str(vol)+" "
	else:
		return str(vol)


def play_audio(url, title=None):

	stdscr = curses.initscr()
	curses.cbreak()
	curses.noecho()
	stdscr.clear()
	stdscr.keypad(True)
	stdscr.nodelay(1)

	# Let user stop player gracefully
	control = " "
	player = create_player(url)
	player.toggle_pause()
	state = "Playing"
	
	if title:
		stdscr.addstr(0, 0, f"Playing {title}")
	
	try:
		while True:
			pos_str, pos, dur = get_player_pos(player)
			stdscr.addstr(1, 0, f"{state}: {pos_str}\t\tVolume: {get_vol(player)}") 
			stdscr.hline(2, 0, curses.ACS_HLINE, int(curses.COLS))
			stdscr.addstr(4, 0, "CONTROLS : ")
			stdscr.addstr(5, 0, "s      : STOP (Start next song in playlist)")
			stdscr.addstr(6, 0, "SPACE  : Toggle PLAY/PAUSE")
			stdscr.addstr(7, 0, "→      : Seek 10 seconds forward")
			stdscr.addstr(8, 0, "←      : Seek 10 seconds backward")
			stdscr.addstr(9, 0, "↑      : Increase Volume")
			stdscr.addstr(10, 0, "↓      : Decrease Volume")
			stdscr.addstr(11, 0, "q      : Quit")
			control = stdscr.getch()

			if control == ord("s"):
				player.set_pause(True)
				player.close_player()
				break

			elif control == ord(" "):
				if state == "Playing":
					player.set_pause(True)
					#NOTE Added space here to pad Paused as same width as Playing
					state = "Paused "
				else:
					player.set_pause(False)
					state = "Playing"
			elif control == curses.KEY_RIGHT:
				forward_callback(player)
			elif control == curses.KEY_LEFT:
				rewind_callback(player)
			elif control == curses.KEY_UP:
				increase_volume(player)
			elif control == curses.KEY_DOWN:
				decrease_volume(player)
			elif control == ord('q'):
				player.set_pause(True)
				player.close_player()
				curses.endwin()
				print("Quitting...\n\n")
				sys.exit(0)
			elif pos >= dur-1:
				sleep(1)
				if LOOP:
					rewind_callback(player,start=True)
				else:
					player.close_player()
					break				
	finally:
		curses.endwin()
		print("\rStopping player...")
