import sys
import curses
import pickle
from time import sleep
import npyscreen as nps
from tools.player import *
from tools.youtube import *
from threading import Thread

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)

results = None
choice = None
player = None
loop = None

def quit_app(*args, **kwargs):
	sys.exit(0) # User requested quit - i.e gracefull

def notify_help(*args, **kwargs):
	nps.notify_wait("Ctrl+h: show this help\nq: quit the app", title="Help")

class searchForm(nps.Form):
	def create(self):
		self.search = self.add(nps.TitleText, name="Search")
		self.helptext = self.add(nps.FixedText, editable=False, value="Press q to quit, Ctrl+h to see help", rely=-3)
		self.add_handlers({
			'q': quit_app,
			'^H': notify_help
			})

	def afterEditing(self):
		nextForm = self.parentApp.getForm('RESULTS')
		if len(self.search.value) < 1:
			nps.notify_wait("Enter a search query", title="Error")
			sleep(1)
			self.parentApp.switchForm('MAIN')
		else:
			self.results = search_video(self.search.value)
			global results
			results = self.results
			nextForm.selected.values = [item['title'] for item in self.results]
			self.parentApp.switchForm('RESULTS')

class resultForm(nps.Form):
	def create(self):
		self.selected = self.add(nps.TitleSelectOne, name="Results")
		self.helptext = self.add(nps.FixedText, editable=False, value="Press q to quit, Ctrl+h to see help", rely=-3)
		self.add_handlers({
			'q': quit_app,
			'^H': notify_help
			})


	def afterEditing(self):
		nextForm = self.parentApp.getForm('DECISION')
		try:
			self.choice = results[self.selected.get_value()[0]]
			global choice
			choice = self.choice
			nextForm.display_choice.value = f" {self.choice['title']} {self.choice['url']} "
			self.parentApp.switchForm('DECISION')		
		except Exception as e:
			nps.notify_wait("Select a result!", title="Error")
			sleep(1)
			self.parentApp.switchForm('RESULTS')

class decisionForm(nps.Form):
	def create(self):
		self.display_choice = self.add(nps.TitleFixedText, name="Selected : ")
		self.display_choice.editable = False
		self.decision = self.add(nps.TitleSelectOne, values=['Play', 'Download'], name="Choose what to do")
		self.helptext = self.add(nps.FixedText, editable=False, value="Press q to quit, Ctrl+h to see help", rely=-3)
		self.add_handlers({
			'q': quit_app,
			'^H': notify_help
			})


	def afterEditing(self):
		if self.decision.get_value()[0] == 0:
			pl, lo = create_player(choice['url'])
			global player, loop
			player = pl
			loop = lo
			self.parentApp.switchForm('PLAYER')

		elif self.decision.get_value()[0] == 1:
			self.parentApp.switchForm('DOWNLOADER')

class playerForm(nps.Form):
	def create(self):
		self.add_handlers({
			"p": self.toggle_pause_player,
			"s": self.stop_player,
			"q": self.quit_player,
			"]": self.seek_ahead,
			"[": self.seek_behind,
			'^H': self.notify_help_player,
			"^R": self.display()
			})

		self.display_name = self.add(nps.TitleFixedText, name="Now Playing", editable=False)
		self.display_time = self.add(nps.FixedText, editable=False)
		self.helptext = self.add(nps.FixedText, editable=False, value="Press q to quit, Ctrl+h to see help", rely=-3)

	def beforeEditing(self):
		global player, loop
		self.display_name.value = choice['title']
		self.player = player 
		self.loop = loop
		self.player.set_state(Gst.State.PLAYING)
		self.PLAYING = True
		Thread(target=self.loop.run).start()
		self.display()

		thread_pl_pos = Thread(target=self.update_pos)
		thread_pl_pos.daemon = True
		thread_pl_pos.start()
		

	def afterEditing(self):
		self.stop_player()
		self.parentApp.setNextForm(None)
	
	def notify_help_player(self, *args, **kwargs):
		helptext = """
		Ctrl+h: show this help
		q: quit the app
		p: toggle pause
		s: stop player and exit
		]: seek forward 10 seconds
		]: seek backward 10 seconds
		"""
		nps.notify_wait(helptext, title="Help")

	def get_player_pos(self):
		rc, pos_int = self.player.query_position(Gst.Format.TIME)
		rc, dur_nano = self.player.query_duration(Gst.Format.TIME)
		seconds_curr = pos_int // 10**9
		mins_curr = seconds_curr // 60
		secs_curr= seconds_curr % 60

		seconds_tot = dur_nano // 10**9
		mins_tot = seconds_tot // 60
		secs_tot = seconds_tot % 60

		return "{:02d}:{:02d}/{:02d}:{:02d}".format(mins_curr, secs_curr, mins_tot, secs_tot)

	def update_pos(self):
		while True:
			self.display_time.value = self.get_player_pos()
			self.display_time.display()
			sleep(1)

	def toggle_pause_player(self, *args, **kwargs):
		if self.PLAYING:
			self.player.set_state(Gst.State.PAUSED)
			self.PLAYING = False
		else:
			self.player.set_state(Gst.State.PLAYING)
			self.PLAYING = True

	def seek_behind(self, *args, **kwargs):
		rc, pos_int = self.player.query_position(Gst.Format.TIME)
		seek_ns = pos_int - 10 * 1000000000
		if seek_ns < 0:
			seek_ns = 0
		self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)
		
	def seek_ahead(self, *args, **kwargs):
		rc, pos_int = self.player.query_position(Gst.Format.TIME)
		seek_ns = pos_int + 10 * 1000000000
		self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

	def stop_player(self, *args, **kwargs):
		self.player.set_state(Gst.State.NULL)
		self.loop.quit()
		self.parentApp.setNextForm(None)

	def quit_player(self, *args, **kwargs):
		self.stop_player()
		sys.exit(0)


class downloadForm(nps.Form):
	def create(self):
		self.display_status = self.add(nps.TitleFixedText, name="Downloading")
		self.display_status.editable = False
		self.helptext = self.add(nps.FixedText, editable=False, value="Press q to quit, Ctrl+h to see help", rely=-3)
		self.add_handlers({
			'q': quit_app,
			'^H': notify_help
			})

	def update_status(self):
		thread_dw = Thread(target=download_video, args=[choice['url'], return_hook])
		thread_dw.daemon = True
		thread_dw.start()

		sleep(2)

		while True:
			with open("/tmp/msg.pkl", "rb") as fp:
				pkl = pickle.load(fp)
				self.display_status.value = f"  {pkl}   "
				self.display_status.display()
				sleep(1)

	def beforeEditing(self):
		thread_dw_st = Thread(target=self.update_status)
		thread_dw_st.daemon = True
		thread_dw_st.start()

		self.display()

	def afterEditing(self):
		self.parentApp.setNextForm(None)

class yclApp(nps.NPSAppManaged):
	def onStart(self):
		self.TITLE = "YCL - Youtube Command Line"
		self.addForm('MAIN', searchForm, name=self.TITLE)
		self.addForm('RESULTS', resultForm, name=self.TITLE)
		self.addForm('DECISION', decisionForm, name=self.TITLE)
		self.addForm('PLAYER', playerForm, name=self.TITLE)
		self.addForm('DOWNLOADER', downloadForm, name=self.TITLE)

def main():
	myapp = yclApp()
	myapp.run()

if __name__ == '__main__':
	main()
