import os
import sys
import click
import requests
import threading
import youtube_dl
from pick import Picker
from dotenv import load_dotenv

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

PAYLOAD = {
	"part": "snippet",
	"maxResults": 25,
	"key" : KEY
}

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
	else:
		percent_str = d['_percent_str']
		downloaded_bytes = d['downloaded_bytes']
		total_bytes = d['total_bytes']
		elapsed = d['elapsed']
		eta = d['eta']
		speed = d['speed']
		print(f"Downloaded: {percent_str} {speed_conv(downloaded_bytes)} of {speed_conv(total_bytes)}. Elapsed: {str(round(elapsed,2)).rjust(8)}s Speed: {speed_conv(speed)}/s ", end="\r", flush=True)

def search(query):
	q = " ".join(query)
	PAYLOAD["q"] = q
	r = requests.get(BASE_URL+"/search", params=PAYLOAD)

	items = r.json().get('items')

	results = []

	if items:
		for x in items:
			videoId = x.get("id")
			if videoId.get("kind") == "youtube#video":
				results.append({ "url": "https://youtube.com/watch?v=" + videoId.get("videoId"), 
							"title" : x["snippet"]["title"], 
						})
	else:
		print("Couldn't connect. Check your credentials.")
		sys.exit(1)

	return results

def speed_conv(b):
	if b > 10**6:
		return f"{round(b/10**6,2)} MB".rjust(10)
	elif b > 10**3:
		return f"{round(b/10**3,2)} KB".rjust(10)
	else:
		return f"{b} B".rjust(10)


def quit_pick(picker):
	sys.exit(0)

def extract_audio_url(yt_url):
	YDL_OPTS = {
		"format" : "bestaudio[acodec=opus]",
		'logger' : MyLogger(),
	}

	with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
		info = ydl.extract_info(yt_url, download=False)

		audio_url = info['formats'][0]['url']
		acodec = info['formats'][0]['acodec']
		return audio_url, acodec

def play_audio(url):
	music_stream_uri = extract_audio_url(url)[0]
	
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
	playing = True
	while control.lower() != "s":
		control = input("Press s to stop playing, p to toggle pause : ")

		if control.lower() == "p":
			if playing:
				player.set_state(Gst.State.PAUSED)
				playing = False
			else:
				player.set_state(Gst.State.PLAYING)
				playing = True

	player.set_state(Gst.State.NULL)
	loop.quit()


@click.command()
@click.argument("query", nargs=-1)

def cli(query):
	results = search(query)

	options = [x["title"] for x in results]
	title = f"Search results for {query} (q to quit)"

	picker = Picker(options, title)
	picker.register_custom_handler(ord('q'), quit_pick)
	option, index = picker.start()

	url = f"{results[index]['url']}"
	print(f"Selected : {url}")

	options = ["Play", "Download"]
	title = "Choose what you want to do (q to quit)"
	picker = Picker(options, title)

	picker.register_custom_handler(ord('q'), quit_pick)

	option, index = picker.start()

	if option == "Download":
		YDL_OPTS = {
		'format' : 'bestvideo+bestaudio/best',
		'logger' : MyLogger(),
		'progress_hooks' : [my_hook],
		'outtmpl' : r"%(title)s.%(ext)s",
		'updatetime' : False
		}
		
		with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
			ydl.download([url])

	elif option == "Play":
		if PLAY_SUPPORT:
			play_audio(url)
		else:
			print("Play support is not available for your system.")


if __name__ == '__main__':
	cli()