import sys
import curses
import pickle
from time import sleep
from tools.pick import Picker
from tools.player import *
from tools.youtube import *
from threading import Thread

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)

class Window(object):
	def __init__(self):
		self.APP_NAME = " YCL - Youtube Command Line "
		self.stdscr = curses.initscr()
		self.stdscr.clear()	
		curses.noecho()
		curses.cbreak()
		curses.start_color()
		self.stdscr.keypad(True)
		self.draw_bounds()

	def draw_bounds(self):
		self.stdscr.box()
		self.draw(0, 10, self.APP_NAME)
		self.stdscr.refresh()
	
	def clear(self):
		self.stdscr.clear()

	def reset(self):
		self.clear()
		self.draw_bounds()

	def draw(self, y, x, text):
		self.stdscr.addstr(y, x, text) 
		self.stdscr.refresh()

	def take_input(self, y, x, input_text):
		curses.echo()
		self.draw(y, x, input_text)
		s = self.stdscr.getstr(y, len(input_text)+2, 30)
		self.stdscr.refresh()
		curses.noecho()
		return s.decode()

	def quit(self, *args, **kwargs):
		self.stdscr.clear()
		curses.nocbreak()
		self.stdscr.keypad(False)
		curses.echo()
		curses.endwin()
		sys.exit(0)

def query_input(screen):
	query = screen.take_input(2, 2, "Search : ")
	return query

def play_audio(screen, url, title=None):
	stdscr = screen.stdscr
	stdscr.nodelay(1)
	player, loop = create_player(url)
	
	player_thread = threading.Thread(target=loop.run)
	player_thread.daemon = True
	player_thread.start()

	control = " "
	player.set_state(Gst.State.PLAYING)
	state = "Playing"
	
	if title:
		stdscr.addstr(2, 2, f"Playing {title}")
	
	while True:
		stdscr.refresh()
		pos = get_player_pos(player)
		stdscr.addstr(3, 2, f"{state}: {pos} ") 
		stdscr.hline(4, 2, curses.ACS_HLINE, curses.COLS-1)
		stdscr.addstr(6, 2, "Controls : ")
		stdscr.addstr(7, 2, "s: STOP")
		stdscr.addstr(8, 2, "p: Toggle PLAY/PAUSE")
		stdscr.addstr(9, 2, "->: Seek 10 seconds forward")
		stdscr.addstr(10, 2, "<-: Seek 10 seconds backward")
		stdscr.addstr(11, 2, "q: Quit")

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
			screen.quit()
			sys.exit(0)


def main():
	scr = Window()
	try:
		query = query_input(scr)
		scr.reset()
		while len(query) < 1:
			scr.reset()
			scr.draw(2, 2, "You didnot enter a valid query")
			sleep(2)
			scr.reset()
			query = query_input(scr)

	except KeyboardInterrupt:
		scr.quit()
			
	scr.reset()
	curses.curs_set(0)
	try:
		results = search_video(query)
	except Exception as e:
		scr.draw(2, 2, f"Oops! Make sure you are connected to the internet")
		sleep(2)
		scr.quit()

	# Pick results
	title = f"You searched for {query}. Search results: "
	options = [r['title'] for r in results]
	picker = Picker(options, title, indicator="=>")
	picker.register_custom_handler(ord('q'), scr.quit)
	option, index = picker._start(scr.stdscr)
	choice = results[index]
	scr.reset()

	# Pick action
	title = f"You selected {option}. Choose what you want to do: "
	options = ["Play", "Download"]
	picker = Picker(options, title, indicator="=>")
	picker.register_custom_handler(ord('q'), scr.quit)
	option, index = picker._start(scr.stdscr)
	scr.reset()

	# Perform action
	if index == 0:
		play_audio(scr, choice['url'], choice['title'])
	else:
		curses.endwin()
		download_video(choice['url'], print_hook)

	sleep(2)
	scr.quit()

if __name__ == "__main__":
	main()
