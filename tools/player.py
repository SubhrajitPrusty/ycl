import sys
import time
import curses
from .youtube import *
from time import sleep
from loguru import logger
from tools.lyrics import *
from ffpyplayer.player import MediaPlayer


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

    return "{:02d}:{:02d}/{:02d}:{:02d}".format(
        mins_curr, secs_curr, mins_tot, secs_tot), seconds_curr, seconds_tot


def create_player(url):
    music_stream_uri = extract_video_url(url)[0]
    if not music_stream_uri:
        print("Failed to get audio")
        sys.exit(1)

    ff_opts = {"vn": True, "sn": True}  # only audio

    player = MediaPlayer(music_stream_uri, ff_opts=ff_opts, loglevel='debug')

    # refer : https://github.com/kivy/kivy/blob/52d12ebf33e410c9f4798674a93cbd0db8038bf1/kivy/core/audio/audio_ffpyplayer.py#L116  # noqa: E501
    # method to prevent crash on load - since the stream hasn't been
    # downloaded sufficiently yet

    player.toggle_pause()
    s = time.perf_counter()
    while (player.get_metadata()['duration']
           is None and time.perf_counter() - s < 10.):
        time.sleep(0.005)

    return player


def get_vol(player):
    vol = int(player.get_volume() * 100)
    if vol < 100:
        return str(vol) + " "
    else:
        return str(vol)


def get_sub(subtitle, time):
    for subs in subtitle:
        if time > subs['start'] and time < subs['end']:
            return subs['text']
    return ""


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
    suburl = extract_video_sublink(url)
    if suburl:
        subtitle = fetch_sub_from_link(suburl)
        subtext = " " * w
    player = create_player(url)
    player.toggle_pause()
    state = "Playing"
    if title:
        stdscr.addstr(1, 1, f"Playing {title}")
    try:
        LOOP = False
        while True:
            pos_str, pos, dur = get_player_pos(player)
            stdscr.addstr(3, 1, f"{state}: {pos_str}\
                \t\tVolume: {get_vol(player)}\
                \t\tLoop: {' on' if LOOP else 'off'}")
            stdscr.hline(4, 1, curses.ACS_HLINE, int(curses.COLS))
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
            # stdscr.addstr(15, 2, "Subtitles")
            if suburl:
                stdscr.hline(14, 1, curses.ACS_HLINE, int(curses.COLS))
                stdscr.addstr(17, 5, subtext)
            control = stdscr.getch()

            if control == ord("s"):
                player.set_pause(True)
                player.close_player()
                break

            elif control == ord(" "):
                if state == "Playing":
                    player.set_pause(True)
                    # NOTE Added space here to pad Paused as same width as
                    # Playing
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
            elif control == ord('l'):
                LOOP = not LOOP
            elif control == ord('q'):
                player.set_pause(True)
                player.close_player()
                del player  # just to be safe
                curses.endwin()
                # print("Quitting...\n\n")
                sys.exit(0)
            elif pos >= dur - 1:
                sleep(1)
                if LOOP:
                    rewind_callback(player, start=True)
                else:
                    player.close_player()
                    break
            if suburl:
                subtext = get_sub(subtitle, pos)
                subtext += " " * (w - len(subtext))
    finally:
        curses.endwin()
