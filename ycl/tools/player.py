import curses
import os
from time import sleep

import vlc
from loguru import logger

from ycl.tools import lyrics, youtube


class VLCMediaPlayer():
    """Object that emulates the vlc media player
    """

    def __init__(self, audio_url, *args):
        self.url = audio_url
        self.create_player(*args)

    def create_player(self, *args):
        """Initialize player with the audio URL
        """
        music_stream_uri = youtube.extract_video_url(self.url)[0]
        if not music_stream_uri:
            print("Failed to get audio")
            exit(1)

        instance = vlc.Instance(*args)
        self.media = instance.media_new_location(music_stream_uri)
        self.player = instance.media_player_new()
        self.player.set_media(self.media)

    def play(self):
        """Start the player
        """
        self.player.play()
        sleep(0.5)

    def pause(self):
        """Pause the player
        """
        self.player.pause()

    def toggle_pause(self):
        """Toggle the play/pause
        """
        self.player.pause()

    def stop(self):
        """Stop the player
        """
        self.player.stop()
        sleep(0.5)

    def repeat(self):
        """Repeat the track
        """
        self.player.set_position(0.0)
        self.player.play()

    def seek_forward(self):
        """Go forward 5 sec"""
        self.player.set_time(self.player.get_time() + 5000)

    def seek_backward(self):
        """Go backward 5 sec"""
        self.player.set_time(self.player.get_time() - 5000)

    def increase_volume(self):
        """Increase volume by 5%
        """
        curr_vol = self.player.audio_get_volume()
        curr_vol += 5
        curr_vol = 100 if curr_vol > 100 else curr_vol
        self.player.audio_set_volume(curr_vol)

    def decrease_volume(self):
        """Decrease volume by 5%
        """
        curr_vol = self.player.audio_get_volume()
        curr_vol -= 5
        curr_vol = 0 if curr_vol < 0 else curr_vol
        self.player.audio_set_volume(curr_vol)

    def toggle_mute(self):
        """Toggle mute
        """
        self.player.audio_toggle_mute()

    @property
    def is_playing(self):
        """Check is player is paused
        """
        return self.player.is_playing()

    @property
    def is_mute(self):
        """Check if player is muted
        """
        return self.player.audio_get_mute()

    @property
    def total_duration(self):
        """Total duraion in ms
        """
        return self.player.get_length()

    @property
    def current_duration(self):
        """Current duration in ms
        """
        return self.player.get_time()

    @property
    def position(self):
        """Get position as percentage between 0.0 and 1.0
        """
        return self.player.get_position()

    @property
    def volume(self):
        """Get current volume
        """
        return self.player.audio_get_volume()

    def get_sub(self, subtitle, time):
        # legacy
        for subs in subtitle:
            if time > subs['start'] and time < subs['end']:
                return subs['text']
        return ""

    @property
    def will_play(self):
        """Check if player will be able to play
        """
        return self.player.will_play()

    @property
    def state(self):
        """Get player state
        """
        _player_state = self.player.get_state()
        _state = str(_player_state)[6:].ljust(8)
        return _state

    @property
    def formatted_position(self):
        """Get the current player time in a format
        """
        seconds_curr = self.current_duration / 1000.0
        seconds_tot = self.total_duration / 1000.0

        mins_curr = int(seconds_curr // 60)
        secs_curr = int(seconds_curr % 60)

        mins_tot = int(seconds_tot // 60)
        secs_tot = int(seconds_tot % 60)

        return "{:02d}:{:02d}/{:02d}:{:02d}".format(mins_curr, secs_curr, mins_tot, secs_tot)


@logger.catch
def play_audio(url, title=None):

    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    stdscr.clear()
    stdscr.keypad(True)
    stdscr.nodelay(1)

    _, w = stdscr.getmaxyx()
    # Let user stop player gracefully
    control = " "

    suburl = youtube.extract_video_sublink(url)
    if suburl:
        subtitle = lyrics.fetch_sub_from_link(suburl)
        subtext = " " * w

    player = VLCMediaPlayer(url, '--no-video')
    player.play()

    player.pause()
    if title:
        stdscr.addstr(1, 1, f"Playing {title}")
    try:
        LOOP = False
        while True:
            stdscr.addstr(3, 1, f"{player.state}: {player.formatted_position}\tVolume: {player.volume}\tLoop: {'on'.ljust(3) if LOOP else 'off'}")
            stdscr.hline(4, 1, curses.ACS_HLINE, int(curses.COLS))
            # TODO: Move this into a separate curses page
            stdscr.addstr(5, 1, "CONTROLS: ")
            stdscr.addstr(6, 1, "s       : STOP (Start next song in playlist)")
            stdscr.addstr(7, 1, "SPACE   : Toggle PLAY/PAUSE")
            stdscr.addstr(8, 1, "→       : Seek 10 seconds forward")
            stdscr.addstr(9, 1, "←       : Seek 10 seconds backward")
            stdscr.addstr(10, 1, "↑       : Increase Volume")
            stdscr.addstr(11, 1, "↓       : Decrease Volume")
            stdscr.addstr(12, 1, "L       : Toggle loop")
            stdscr.addstr(13, 1, "q       : Quit")
            stdscr.hline(14, 1, curses.ACS_HLINE, int(curses.COLS))
            stdscr.addstr(15, 1, "Subtitles")
            if suburl:
                stdscr.hline(14, 1, curses.ACS_HLINE, int(curses.COLS))
                stdscr.addstr(17, 5, subtext)
            control = stdscr.getch()

            if control == ord("s"):
                player.pause()
                sleep(0.5)
                player.stop()
                break

            elif control == ord(" "):
                player.toggle_pause()
            elif control == curses.KEY_RIGHT:
                player.seek_forward()
            elif control == curses.KEY_LEFT:
                player.seek_backward()
            elif control == curses.KEY_UP:
                player.increase_volume()
            elif control == curses.KEY_DOWN:
                player.decrease_volume()
            elif control == ord('l'):
                LOOP = not LOOP
            elif control == ord('m'):
                player.toggle_mute()
            elif control == ord('q'):
                player.pause()
                sleep(0.5)
                player.stop()
                del player  # just to be safe
                os.system('cls' if os.name == 'nt' else 'clear')
                curses.endwin()
                exit(0)
            elif player.state.strip() == 'Ended':
                sleep(0.5)
                if LOOP:
                    player.repeat()
                else:
                    player.stop()
                    break

            if suburl:
                subtext = lyrics.get_sub(subtitle, player.current_duration / 1000.0)
                subtext += " " * (w - len(subtext))
    finally:
        os.system('cls' if os.name == 'nt' else 'clear')
        curses.endwin()
