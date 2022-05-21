import curses
import os
from argparse import ArgumentParser

from loguru import logger

from ycl.tools import tui
from ycl.tools.pick import Picker
from ycl.tools.player import play_audio
from ycl.tools.youtube import (download_video, extract_playlist_data,
                               is_connected, isValidURL, parse_file,
                               print_hook, search_pl, search_video)

logger.remove(0)
logger.add('stderr', level='WARNING')


def _quit_pick(picker):
    exit(0)


def cli(query=None, playlistsearch=False, video=None, playlist=None, interactive=False, export=False, output=None):
    LOCAL_PLAYLIST = False

    if not is_connected():
        print("Check your internet connection.")
        exit(1)

    if interactive:
        tui.main()
    else:
        if not query:
            _msg = "Error: Enter a search query"
            print(_msg)
            exit(1)

        query = " ".join(query)
        choice = {}

        if video:
            isValid, details = isValidURL(query, urlType="video")
            if isValid:
                choice['id'] = details['id']
                choice['url'] = query
                choice['title'] = details['snippet']['title']
            else:
                print("Invalid URL")
                exit(3)
        elif playlist:
            isValid, details = isValidURL(query, urlType="playlist")
            if isValid:
                choice['id'] = details['id']
                choice['url'] = query
                choice['title'] = details['snippet']['title']
            else:
                if os.path.exists(query):
                    LOCAL_PLAYLIST = parse_file(query)
                else:
                    print("ERROR: Wrong link or file path")
                    exit(3)
        elif export:
            isValid, details = isValidURL(query, urlType="playlist")
            if isValid:
                video_list = '\n'.join(
                    [f"{play_list['url']},{play_list['title']}"
                        for play_list in extract_playlist_data(query)])
                SAVE_FILE = details['snippet']['title'] + ".ycl"
                handle = open(SAVE_FILE, "w", encoding="utf8")
                handle.write(video_list)
                handle.close()
                print(f"Playlist saved to {SAVE_FILE} ")
                exit()
            else:
                print("ERROR: Invalid URL")
                exit(3)
        else:
            if playlistsearch:
                results = search_pl(query)
            else:
                results = search_video(query)

            if len(results) < 1:
                print("No results found.")
                exit(3)

            options = [x["title"] for x in results]
            title = f"Search results for {query} (q to quit)"
            picker = Picker(options, title)
            picker.register_custom_handler(ord('q'), _quit_pick)
            option, index = picker.start()

            choice = results[index]

        selected = query if LOCAL_PLAYLIST else choice['url']
        print(f"Selected : {selected}")

        options = ["Play", "Download"]
        title = "Choose what you want to do (q to quit)"
        picker = Picker(options, title)

        picker.register_custom_handler(ord('q'), _quit_pick)

        curses.initscr().clear()
        option, index = picker.start()
        curses.endwin()
        if playlist or playlistsearch:

            if LOCAL_PLAYLIST:
                playlist_list = LOCAL_PLAYLIST
            else:
                playlist_list = extract_playlist_data(choice['url'])

            for video in playlist_list:
                if option == "Download":
                    print(f"\x1B[1KDownload: {video['title']}\n")
                    download_video(video['url'], print_hook, output_format=output)
                elif option == "Play":
                    play_audio(video['url'], video['title'])
        else:
            if option == "Download":
                print(f"\x1B[1KDownload: {choice['title']}\n")
                download_video(choice['url'], print_hook, output_format=output)
            elif option == "Play":
                play_audio(choice['url'], choice['title'])


def main():
    arg_parser = ArgumentParser(description="YCL - Youtube Command Line")
    arg_parser.add_argument('query', nargs='?', help="Search query")
    arg_parser.add_argument("--playlistsearch", "-ps", action='store_true', default=False, help="Searches for playlists")
    arg_parser.add_argument("--video", "-v", action='store_true', default=False, help="Use a direct video link")
    arg_parser.add_argument("--playlist", "-pl", action='store_true', default=False, help="Use a direct playlist link or file")
    arg_parser.add_argument("--interactive", "-i", action='store_true', default=False, help="Starts an interactive Terminal UI session")
    arg_parser.add_argument("--export", "-e", action='store_true', default=False, help="Export A playlist to a local file")
    arg_parser.add_argument("--output", "-o", action='store_true', default="mkv", help="Set output format container, eg: mp4, mkv")

    args = arg_parser.parse_args()
    logger.debug(args.query)
    cli(args.query, args.playlistsearch, args.video, args.playlist, args.interactive, args.export, args.output)


if __name__ == "__main__":
    main()
