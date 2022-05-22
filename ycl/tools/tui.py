"""TUI helper functions
"""
import curses
import os
import sys
from time import sleep

from loguru import logger

from ycl.tools import lyrics
from ycl.tools import player as _player
from ycl.tools import youtube
from ycl.tools.pick import Picker


class Window():
    """Custom TUI object
    """
    def __init__(self):
        self.APP_NAME = " YCL - Youtube Command Line "
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        self.reset()

    def draw_bounds(self):
        """Draw the bounds of the window
        """
        self.stdscr.box()
        self.draw(0, 10, self.APP_NAME)
        self.stdscr.refresh()

    def clear(self):
        """Clear the screen
        """
        self.stdscr.clear()

    def reset(self):
        """Reset the screen
        """
        self.clear()
        self.draw_bounds()

    def draw(self, y, x, text, attr=0):
        """Draw text on the screen
        """
        self.stdscr.addstr(y, x, text, attr)
        self.stdscr.refresh()

    def take_input(self, y, x, input_text):
        """Take input from user
        """
        curses.echo()
        self.draw(y, x, input_text, curses.color_pair(1) | curses.A_BOLD)
        s = self.stdscr.getstr(y, len(input_text) + 2, 30)
        self.stdscr.refresh()
        curses.noecho()
        return s.decode()

    def quit(self):
        """Quit the window
        """
        self.stdscr.clear()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
        sys.exit(0)


# TODO: Move to a helper file
def get_sub(subtitle, time):
    """Get the subtitle at the given time
    """
    for subs in subtitle:
        if time > subs['start'] and time < subs['end']:
            return subs['text']
    return ""


@logger.catch
def play_audio_tui(screen, url, title=None):
    """Play audio from URL in a TUI
    """
    stdscr = screen.stdscr
    stdscr.nodelay(1)

    _, w = stdscr.getmaxyx()
    suburl = youtube.extract_video_sublink(url)
    if suburl:
        w -= 3
        subtitle = lyrics.fetch_sub_from_link(suburl)
        subtext = " " * w

    control = " "

    player = _player.VLCMediaPlayer(url, '--no-video')
    player.play()
    if title:
        stdscr.addstr(2, 2, f"Playing {title}", curses.color_pair(1) | curses.A_BOLD)

    LOOP = True
    while True:
        stdscr.refresh()
        stdscr.addstr(3, 2, f"{player.state} : {player.formatted_position} \tVolume: {player.volume}\tLoop: {' on' if LOOP else 'off'}", curses.color_pair(1))
        stdscr.hline(4, 2, curses.ACS_HLINE, curses.COLS - 4)
        # TODO: Move this into a separate curses page
        stdscr.addstr(6, 2, "CONTROLS : ", curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(7, 2, "s             : STOP / NEXT ", curses.color_pair(3))
        stdscr.addstr(8, 2, "SPACE         : Toggle PLAY/PAUSE ", curses.color_pair(3))
        stdscr.addstr(9, 2, "→             : Seek 10 seconds forward ", curses.color_pair(3))
        stdscr.addstr(10, 2, "←             : Seek 10 seconds backward ", curses.color_pair(3))
        stdscr.addstr(11, 2, "↑             : Increase Volume", curses.color_pair(3))
        stdscr.addstr(12, 2, "↓             : Decrease Volume", curses.color_pair(3))
        stdscr.addstr(12, 1, "L             : Toggle Repeat", curses.color_pair(3))
        stdscr.addstr(13, 1, "M             : Toggle Mute", curses.color_pair(3))
        stdscr.addstr(14, 2, "q             : Quit ", curses.color_pair(3))
        stdscr.hline(15, 2, curses.ACS_HLINE, curses.COLS - 4)
        stdscr.addstr(16, 2, "Subtitles")
        if suburl:
            stdscr.hline(17, 2, curses.ACS_HLINE, curses.COLS - 4)
            stdscr.addstr(20, 2, subtext, curses.color_pair(4))

        control = stdscr.getch()

        if control == ord("s"):
            player.pause()
            stdscr.refresh()
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
            screen.quit()
            del player  # just to be safe
            os.system('cls' if os.name == 'nt' else 'clear')
            curses.endwin()
            exit(0)
        elif control == ord('r'):
            sleep(0.5)
            player.repeat()

        elif player.state.strip() == "Ended":
            sleep(0.5)
            if LOOP:
                player.repeat()
            else:
                player.stop()
                break
        if suburl:
            subtext = get_sub(subtitle, player.current_duration / 1000.0)
            subtext += " " * (w - len(subtext))


def main():
    """Main event loop
    """
    scr = Window()

    def search_page():
        try:
            scr.reset()
            scr.draw(curses.LINES - 4, 2, "Ctrl+C to exit")
            query = scr.take_input(2, 2, "Search : ")
            scr.reset()
            while len(query) < 1:
                scr.reset()
                scr.draw(
                    2,
                    2,
                    "You did not enter a valid query",
                    curses.color_pair(2))
                scr.draw(curses.LINES - 4, 2, "Ctrl+C to exit")
                sleep(2)
                scr.reset()
                scr.draw(curses.LINES - 4, 2, "Ctrl+C to exit")
                query = scr.take_input(2, 2, "Search : ")

        except KeyboardInterrupt:
            scr.quit()

        return query

    def make_search():
        query = search_page()
        title = "Search for playlists? : (q to quit)"
        options = ["No", "Yes"]
        picker = Picker(options, title, indicator="=>")
        picker.register_custom_handler(ord('q'), scr.quit)
        _, index = picker._start(scr.stdscr)
        scr.reset()
        curses.curs_set(0)
        try:
            if index == 1:
                results = youtube.search_pl(query)
                isPlaylist = True
            else:
                results = youtube.search_video(query)
                isPlaylist = False
        except Exception as e:
            logger.error(e)
            # scr.draw(curses.LINES - 4, 2, f"ERROR: {str(e)}")
            scr.draw(
                2,
                2,
                "Oops! Make sure you are connected to the internet",
                curses.color_pair(2))
            sleep(2)
            scr.quit()

        return results, query, isPlaylist

    results, query, isPlaylist = make_search()

    while len(results) < 1:
        scr.draw(2, 2, "No results found!", curses.color_pair(2))
        sleep(2)
        results, query, isPlaylist = make_search()

    # Pick results
    title = f"You searched for {query}. Search results: (q to quit)"
    options = [r['title'] for r in results]
    picker = Picker(options, title, indicator="=>")
    picker.register_custom_handler(ord('q'), scr.quit)
    option, index = picker._start(scr.stdscr)
    choice = results[index]
    scr.reset()

    # Pick action
    title = f"You selected {option}. Choose what you want to do: (q to quit)"
    options = ["Play", "Download"]
    picker = Picker(options, title, indicator="=>")
    picker.register_custom_handler(ord('q'), scr.quit)
    option, index = picker._start(scr.stdscr)
    scr.reset()

    # Perform action
    if index == 0:
        try:
            if isPlaylist:
                for video in youtube.extract_playlist_data(choice['url']):
                    scr.reset()
                    play_audio_tui(scr, video['url'], video['title'])
            else:
                play_audio_tui(scr, choice['url'], choice['title'])
        except Exception as e:
            logger.error(e)
            scr.draw(
                2,
                2,
                "Oops! Check your internet connection",
                curses.color_pair(2))
            sleep(2)
            scr.quit()

    else:
        curses.endwin()
        if isPlaylist:
            for video in youtube.extract_playlist_data(choice['url']):
                print(f"Downloading {video['title']}")
                youtube.download_video(video['url'], youtube.print_hook)
        else:
            print(f"Downloading {choice['title']}")
            youtube.download_video(choice['url'], youtube.print_hook)

    sleep(2)
    scr.quit()


if __name__ == "__main__":
    main()
