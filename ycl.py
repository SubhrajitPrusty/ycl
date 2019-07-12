import os
import sys
import click
from tools.youtube import *
from pick import Picker

PLAY_SUPPORT=True

try:
	from tools import tui
	from tools.player import *
except Exception as e:
	PLAY_SUPPORT=False

def quit_pick(picker):
	sys.exit(0)

@click.command()
@click.argument("query", nargs=-1)
@click.option("--playlistsearch", "-ps", default=False, is_flag=True, help="Searches for playlists")
@click.option("--video", "-v", default=False, is_flag=True, help="Use a direct video link")
@click.option("--playlist", "-pl", default=False, is_flag=True, help="Use a direct playlist link")
@click.option("--interactive", "-i", default=False, is_flag=True, help="Starts an interactive Terminal UI session")

def cli(query, playlistsearch, video, playlist, interactive):
	if interactive:
		tui.main()
	else:
		if not query:
			print("Error: Enter a search query")
			sys.exit(1)

		query = " ".join(query)

		url = ""
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
			url = query
			if isValid:
				# print(f"Selected : {url}")
				choice['id'] = details['id']
				choice['url'] = query
				choice['title'] = details['snippet']['title']
			else:
				print("Invalid URL")
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
			
		print(f"Selected : {choice['url']}")
		
		options = ["Play", "Download"]
		title = "Choose what you want to do (q to quit)"
		picker = Picker(options, title)

		picker.register_custom_handler(ord('q'), quit_pick)

		option, index = picker.start()
			
		if playlist or playlistsearch:
			if option == "Download":
				for playlist_item in extract_playlist_data(choice['url']):
					print(f"Downloading {playlist_item['title']}")
					download_video(playlist_item['url'], print_hook)
			elif option == "Play":
				if not PLAY_SUPPORT:
					print("Play support is not available for your system.")
					sys.exit(2)
				else:
					for playlist_item in extract_playlist_data(choice['url']):
						# print(f"Playing {playlist_item['title']}")
						play_audio(playlist_item['url'], playlist_item['title'])
		else:
			if option == "Download":
					print(f"Downloading {choice['title']}")
					download_video(choice['url'], print_hook)
			elif option == "Play":
				if not PLAY_SUPPORT:
					print("Play support is not available for your system.")
					sys.exit(2)
				else:
					# print(f"Playing {choice['title']}")
					play_audio(choice['url'], choice['title'])


if __name__ == '__main__':
	cli()
