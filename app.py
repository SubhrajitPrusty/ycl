import sys
import ycl
import curses
import npyscreen as nps
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

class searchForm(nps.Form):
    def create(self):
        self.search = self.add(nps.TitleText, name="Search")

    def afterEditing(self):
        nextForm = self.parentApp.getForm('RESULTS')
        self.results = ycl.search_video(self.search.value)
        global results
        results = self.results
        nextForm.selected.values = [item['title'] for item in self.results]
        self.parentApp.switchForm('RESULTS')

class resultForm(nps.Form):
    def create(self):
        self.selected = self.add(nps.TitleSelectOne, name="Results")

    def afterEditing(self):
        nextForm = self.parentApp.getForm('DECISION')
        self.choice = results[self.selected.get_value()[0]]
        global choice
        choice = self.choice
        nextForm.display_choice.value = self.choice['title'] + " " + self.choice['url']
        self.parentApp.switchForm('DECISION')       

class decisionForm(nps.Form):
    def create(self):
        self.display_choice = self.add(nps.FixedText, name="Selected :")
        self.decision = self.add(nps.TitleSelectOne, values=['Play', 'Download'], name="Choose what to do")

    def afterEditing(self):
        if self.decision.get_value()[0] == 0:
            # ycl.play_audio(choice['url'])
            pl, lo = ycl.create_player(choice['url'])
            global player, loop
            player = pl
            loop = lo
            self.parentApp.switchForm('PLAYER')

        elif self.decision.get_value()[0] == 1:
            # ycl.download_video(choice['url'])
            self.parentApp.switchForm('DOWNLOADER')

class playerForm(nps.Form):
    def create(self):
        self.add_handlers({
            "p": self.toggle_pause_player,
            "P": self.toggle_pause_player,
            "s": self.stop_player,
            "S": self.stop_player,
            "q": self.quit_player,
            "Q": self.quit_player,
            curses.KEY_RIGHT: self.seek_ahead,
            curses.KEY_LEFT: self.seek_behind
            })
        self.display_details = self.add(nps.TitleFixedText, name="Now Playing")

    def beforeEditing(self):
        global player, loop
        self.player = player 
        self.loop = loop
        self.player.set_state(Gst.State.PLAYING)
        self.STATE = "PLAYING"
        Thread(target=self.loop.run).start()


    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def toggle_pause_player(self, *args, **kwargs):
        if self.STATE == "PLAYING":
            self.player.set_state(Gst.State.PAUSED)
            self.state = "PAUSED"
        elif self.STATE == "PAUSED":
            self.player.set_state(Gst.State.PLAYING)
            self.state = "PLAYING"

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

    def quit_player(self, *args, **kwargs):
        self.stop_player()
        sys.exit(0)


class downloadForm(nps.Form):
    def create(self):
        self.display_details = self.add(nps.TitleFixedText, name="Downloading")

    def afterEditing(self):
        self.parentApp.setNextForm(None)

class yclApp(nps.NPSAppManaged):
    results = None
    choice = None
    player = None
    loop = None
    def onStart(self):
        self.TITLE = "YCL - Youtube Command Line"
        self.addForm('MAIN', searchForm, name=self.TITLE)
        self.addForm('RESULTS', resultForm, name=self.TITLE)
        self.addForm('DECISION', decisionForm, name=self.TITLE)
        self.addForm('PLAYER', playerForm, name=self.TITLE)
        self.addForm('DOWNLOADER', downloadForm, name=self.TITLE)


if __name__ == '__main__':
    myapp = yclApp()
    myapp.run()


"""
class player():
    def __init__(self, player=None, loop=None, *args, **keywords):
        self.player = player
        self.loop = loop
        self.add_handlers({
            "p": self.toggle_pause_player,
            "P": self.toggle_pause_player,
            "s": self.stop_player,
            "S": self.stop_player,
            "q": self.quit_player,
            "Q": self.quit_player,
            curses.KEY_RIGHT: self.seek_ahead,
            curses.KEY_LEFT: self.seek_behind
            })
        self.state = "PLAYING"
        Thread(target=self.loop.run).start()

    def display_value(self, vl):
        rc, pos_int = self.player.quert_position(Gst.Format.TIME)
        seconds = pos_int // 10**9
        mins = seconds // 60
        secs = seconds % 60
        time_elapsed = "{}:{}".format(mins, secs)
        return time_elapsed 

    def toggle_pause_player(self):
        if self.STATE == "PLAYING":
            self.player.set_state(Gst.State.PAUSED)
            self.state = "PAUSED"
        elif self.STATE == "PAUSED":
            self.player.set_state(Gst.State.PLAYING)
            self.state = "PLAYING"

    def seek_behind(self):
        rc, pos_int = self.player.query_position(Gst.Format.TIME)
        seek_ns = pos_int - 10 * 1000000000
        if seek_ns < 0:
            seek_ns = 0
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)
        
    def seek_ahead(self):
        rc, pos_int = self.player.query_position(Gst.Format.TIME)
        seek_ns = pos_int + 10 * 1000000000
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

    def stop_player(self):
        self.player.set_state(Gst.State.NULL)
        self.loop.quit()

    def quit_player(self):
        self.stop_player()
        sys.exit(0)
"""

