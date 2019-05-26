import os
import sys
import click
import requests
import threading
import youtube_dl
from pick import Picker
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

PLAY_SUPPORT=True

try:
	import gi
	gi.require_version('Gst', '1.0')
	gi.require_version('GstBase', '1.0')
	from gi.repository import GObject, Gst
	GObject.threads_init()
	Gst.init(None)
except Exception as e:
	PLAY_SUPPORT=False

load_dotenv()

KEY=os.environ.get("KEY")
BASE_URL="https://www.googleapis.com/youtube/v3"

PAYLOAD = dict()

class MyLogger(object):
	def debug(self, msg):
		pass

	def warning(self, msg):
		pass

	def error(self, msg):
		print(msg)

def my_hook(d):
	if d['status'] == 'finished':
		print("\nDownload finished. Now converting...", end="\r")
		print("Downloaded {}".format(d['filename']))
	else:
		try:
			percent_str = d.get('_percent_str')
			downloaded_bytes = d.get('downloaded_bytes')
			total_bytes = d.get('total_bytes')
			elapsed = d.get('elapsed')
			eta = d.get('eta')
			speed = d.get('speed')
			print(f"Downloaded: {percent_str} {speed_conv(downloaded_bytes)} of {speed_conv(total_bytes)}.\
			  Elapsed: {str(round(elapsed,2)).rjust(8)}s Speed: {speed_conv(speed)}/s ", end="\r", flush=True)
		except Exception as e:
			print(f"Downloaded: {percent_str} Unknown of Unknown.\
			  Elapsed: {str(round(elapsed,2)).rjust(8)}s Speed: Unknown/s ", end="\r", flush=True)

def isValidURL(url, urlType="video"):
	"""
	Parameters:
		url : url as string
		urlType : video/playlist

	Returns:
		if valid : True, details - a dict with relevant details
		else : False, None

	"""
	PAYLOAD['key'] = KEY
	PAYLOAD["part"] = "snippet"

	parsed = urlparse(url)
	qss = parse_qs(parsed.query)

	try:
		if urlType == "video":
			videoId = qss['v'].pop()

			PAYLOAD["id"] = videoId

			r = requests.get(BASE_URL+"/videos", params=PAYLOAD)
		else:
			playlistId = qss['list'].pop()
			
			PAYLOAD["id"] = playlistId

			r = requests.get(BASE_URL+"/playlists", params=PAYLOAD)

		found = r.json()['pageInfo']['totalResults']

		if found:
			details = r.json().get('items').pop()
			return True, details
	except Exception as e:
		pass
	
	return False, None


def search_video(query):
	"""
	Parameters:
		query : query string

	Returns:
		results : list of dictionaries
		{
			"url" : "",
			"id" : "",
			"title": "",				
		}
	"""

	PAYLOAD['key'] = KEY

	PAYLOAD["part"] = "snippet"
	PAYLOAD["maxResults"] = 25
	PAYLOAD["q"] = query

	r = requests.get(BASE_URL+"/search", params=PAYLOAD)

	items = r.json().get('items')

	results = []

	if items:
		for x in items:
			videoId = x.get("id")
			if videoId.get("kind") == "youtube#video":
				results.append({ "url": "https://youtube.com/watch?v=" + videoId.get("videoId"), 
								"id": videoId.get("videoId"),
								"title" : x["snippet"]["title"], 
						})
	else:
		print("Couldn't connect.")
		sys.exit(1)

	return results

def search_pl(query):
	PAYLOAD['key'] = KEY

	PAYLOAD['part'] = "snippet"
	PAYLOAD["maxResults"] = 25
	PAYLOAD["q"] = query

	r = requests.get(BASE_URL+"/search", params=PAYLOAD)

	items = r.json().get('items')

	results = []

	if items:
		for x in items:
			playlistId = x.get("id")
			if playlistId.get("kind") == "youtube#playlist":
				results.append({ "url": "https://youtube.com/playlist?list=" + playlistId.get("playlistId"),
								"id": playlistId.get("playlistId"), 
								"title" : x["snippet"]["title"],
						})
	else:
		print("Couldn't connect.")
		sys.exit(1)

	return results

def extract_playlist_data(url):
	PAYLOAD = dict()
	PAYLOAD['key'] = KEY
	PAYLOAD["maxResults"] = 50
	parsed = urlparse(url)
	qss = parse_qs(parsed.query)

	PAYLOAD['part'] = "snippet"
	PAYLOAD['playlistId'] = qss['list'].pop()
	PAYLOAD['pageToken'] = ""

	r = requests.get(BASE_URL+"/playlistItems", params=PAYLOAD)

	items = r.json().get('items')

	playlistItems = []
	totalItems = []

	totalResults = r.json()['pageInfo']['totalResults']

	if items:
		totalItems += items
		while len(totalItems) < totalResults:
			nextPageToken = r.json()['nextPageToken']
			PAYLOAD['pageToken'] = nextPageToken
			r = requests.get(BASE_URL+"/playlistItems", params=PAYLOAD)
			items = r.json().get('items')
			totalItems += items

		for x in totalItems:
			snippet = x.get("snippet")
			videoId = snippet.get("resourceId").get("videoId")
			playlistItems.append({ "url" : "https://youtube.com/watch?v=" + videoId,
									"id" : videoId,
									"title" : snippet.get("title"),
				})
	else:
		# print(r.json())
		print("Couldn't get playlist details. Try again")
		sys.exit(2)

	return playlistItems

def speed_conv(b):
	if b > 10**6:
		return f"{round(b/10**6,2)} MB".rjust(10)
	elif b > 10**3:
		return f"{round(b/10**3,2)} KB".rjust(10)
	else:
		return f"{b} B".rjust(10)

def download_video(url):
	YDL_OPTS = {
		'format' : 'bestvideo+bestaudio/best',
		'logger' : MyLogger(),
		'progress_hooks' : [my_hook],
		'outtmpl' : r"%(title)s.%(ext)s",
		'ignore-errors': True,
		'updatetime' : False
	}
	
	try:
		with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
			ydl.download([url])
	except Exception as e:
		print("Error :", e)
	

def quit_pick(picker):
	sys.exit(0)

def extract_audio_url(yt_url):
	YDL_OPTS = {
		"ignore-errors" : True,
		"format" : "bestaudio[acodec=opus]",
		'logger' : MyLogger(),
	}

	try:
		with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
			info = ydl.extract_info(yt_url, download=False)

			audio_url = info['formats'][0]['url']
			acodec = info['formats'][0]['acodec']		
			return audio_url, acodec
	except Exception as e:
		print("Error :", e)
		return None, None
		
def rewind_callback(player):
	rc, pos_int = player.query_position(Gst.Format.TIME)
	seek_ns = pos_int - 10 * 1000000000
	if seek_ns < 0:
		seek_ns = 0
	player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)
		
def forward_callback(player):
	rc, pos_int = player.query_position(Gst.Format.TIME)
	seek_ns = pos_int + 10 * 1000000000
	player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

def create_player(url):
	music_stream_uri = extract_audio_url(url)[0]

	if not music_stream_uri:
		return
	
	# Create a custom bin element, that will serve as audio sink to
	# player bin. Audio filters will be added to this sink.
	audio_sink = Gst.Bin.new('audiosink')
	
	# Create element to attenuate/amplify the signal
	amplify = Gst.ElementFactory.make('audioamplify')
	amplify.set_property('amplification', 1)
	audio_sink.add(amplify)

	# Create element to play the pipeline to hardware
	sink = Gst.ElementFactory.make('autoaudiosink')
	audio_sink.add(sink)

	amplify.link(sink)
	audio_sink.add_pad(Gst.GhostPad.new('sink', amplify.get_static_pad('sink')))

	# Create playbin and add the custom audio sink to it
	player = Gst.ElementFactory.make("playbin", "player")
	player.props.audio_sink = audio_sink

	#set the uri
	player.set_property('uri', music_stream_uri)

	loop = GObject.MainLoop()

	return player, loop


def play_audio(url):
	music_stream_uri = extract_audio_url(url)[0]

	if not music_stream_uri:
		return
	
	# Create a custom bin element, that will serve as audio sink to
	# player bin. Audio filters will be added to this sink.
	audio_sink = Gst.Bin.new('audiosink')
	
	# Create element to attenuate/amplify the signal
	amplify = Gst.ElementFactory.make('audioamplify')
	amplify.set_property('amplification', 1)
	audio_sink.add(amplify)

	# Create element to play the pipeline to hardware
	sink = Gst.ElementFactory.make('autoaudiosink')
	audio_sink.add(sink)

	amplify.link(sink)
	audio_sink.add_pad(Gst.GhostPad.new('sink', amplify.get_static_pad('sink')))

	# Create playbin and add the custom audio sink to it
	player = Gst.ElementFactory.make("playbin", "player")
	player.props.audio_sink = audio_sink

	#set the uri
	player.set_property('uri', music_stream_uri)

	# Start playing
	player.set_state(Gst.State.PLAYING)

	# Listen for metadata
	bus = player.get_bus()
	bus.enable_sync_message_emission()
	bus.add_signal_watch()
	# bus.connect('message::tag', on_tag)

	loop = GObject.MainLoop()
	threading.Thread(target=loop.run).start()

	# Let user stop player gracefully
	control = " "
	state = "Playing"
	
	while True:
		control = input(f"{state}: STOP/PLAY-PAUSE/FF/RR/QUIT (s/p/l/j/q) : ")
		
		if control.lower() == "s" or control.lower() == "":
			player.set_state(Gst.State.NULL)
			loop.quit()
			break

		elif control.lower() == "p":
			if state == "Playing":
				player.set_state(Gst.State.PAUSED)
				state = "Paused"
			else:
				player.set_state(Gst.State.PLAYING)
				state = "Playing"
		elif control.lower() == 'l':
			forward_callback(player)
		elif control.lower() == 'j':
			rewind_callback(player)
		elif control.lower() == 'q':
			player.set_state(Gst.State.NULL)
			loop.quit()
			sys.exit(0)		
		

@click.command()
@click.argument("query", nargs=-1)
@click.option("--playlistsearch", "-ps", default=False, is_flag=True, help="Searches for playlists")
@click.option("--video", "-v", default=False, is_flag=True, help="Use a direct video link")
@click.option("--playlist", "-pl", default=False, is_flag=True, help="Use a direct playlist link")

def cli(query, playlistsearch, video, playlist):
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
				download_video(playlist_item['url'])
		elif option == "Play":
			if not PLAY_SUPPORT:
				print("Play support is not available for your system.")
				sys.exit(2)
			else:
				for playlist_item in extract_playlist_data(choice['url']):
					print(f"Playing {playlist_item['title']}")
					play_audio(playlist_item['url'])
	else:
		if option == "Download":
				print(f"Dowloading {choice['title']}")
				download_video(choice['url'])
		elif option == "Play":
			if not PLAY_SUPPORT:
				print("Play support is not available for your system.")
				sys.exit(2)
			else:
				print(f"Playing {choice['title']}")
				play_audio(choice['url'])


if __name__ == '__main__':
	cli()
