import os
import sys
import click
from tools import tui
from pick import Picker
from tools.player import *
from tools.youtube import *
import curses


def quit_pick(picker):
    sys.exit(0)


@logger.catch
@click.command()
@click.argument("query", nargs=-1)
@click.option("--playlistsearch", "-ps", default=False,
              is_flag=True, help="Searches for playlists")
@click.option("--video", "-v", default=False,
              is_flag=True, help="Use a direct video link")
@click.option("--playlist", "-pl", default=False, is_flag=True,
              help="Use a direct playlist link or file")
@click.option("--interactive", "-i", default=False, is_flag=True,
              help="Starts an interactive Terminal UI session")
@click.option("--export", "-e", default=False, is_flag=True,
              help="Export A playlist to a local file")
def cli(query, playlistsearch, video, playlist, interactive, export):
    LOCAL_PLAYLIST = False

    if interactive:
        tui.main()
    else:
        if not query:
            print("Error: Enter a search query")
            sys.exit(1)

        query = " ".join(query)

        choice = dict()

        if video:
            isValid, details = isValidURL(query, urlType="video")
            if isValid:
                # print(f"Selected : {url}")
                choice['id'] = details['id']
                choice['url'] = query
                choice['title'] = details['snippet']['title']
            else:
                print("Invalid URL")
                sys.exit(3)
        elif playlist:
            isValid, details = isValidURL(query, urlType="playlist")
            if isValid:
                # print(f"Selected : {url}")
                choice['id'] = details['id']
                choice['url'] = query
                choice['title'] = details['snippet']['title']
            else:
                if os.path.exists(query):
                    LOCAL_PLAYLIST = parse_file(query)
                else:
                    print("ERROR: Wrong link or file path")
                    sys.exit(3)
        elif export:
            isValid, details = isValidURL(query, urlType="playlist")
            if isValid:
                # print(f"Selected : {url}")
                video_list = '\n'.join(
                    [f"{play_list['url']},{play_list['title']}"
                        for play_list in extract_playlist_data(query)])
                SAVE_FILE = details['snippet']['title'] + ".ycl"
                handle = open(SAVE_FILE, "w", encoding="utf8")
                handle.write(video_list)
                handle.close()
                print(f"Playlist saved to {SAVE_FILE} ")
                sys.exit()
            else:
                print("ERROR: Invalid URL")
                sys.exit(3)
        else:
            if playlistsearch:
                results = search_pl(query)
            else:
                results = search_video(query)

            if len(results) < 1:
                click.secho("No results found.", fg="red")
                sys.exit(3)

            options = [x["title"] for x in results]
            title = f"Search results for {query} (q to quit)"
            picker = Picker(options, title)
            picker.register_custom_handler(ord('q'), quit_pick)
            option, index = picker.start()

            choice = results[index]

        selected = query if LOCAL_PLAYLIST else choice['url']
        print(f"Selected : {selected}")

        options = ["Play", "Download"]
        title = "Choose what you want to do (q to quit)"
        picker = Picker(options, title)

        picker.register_custom_handler(ord('q'), quit_pick)

        option, index = picker.start()
        curses.initscr()
        if playlist or playlistsearch:

            if LOCAL_PLAYLIST:
                playlist_list = LOCAL_PLAYLIST
            else:
                playlist_list = extract_playlist_data(choice['url'])

            for video in playlist_list:
                if option == "Download":
                    print(f"\x1B[1KDownload: {video['title']}\n")
                    download_video(video['url'], print_hook)
                    # print()
                elif option == "Play":
                    play_audio(video['url'], video['title'])
        else:
            if option == "Download":
                print(f"\x1B[1KDownload: {choice['title']}\n")
                download_video(choice['url'], print_hook)
            elif option == "Play":
                play_audio(choice['url'], choice['title'])


if __name__ == '__main__':
    cli()
