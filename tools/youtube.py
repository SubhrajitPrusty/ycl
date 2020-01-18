import os
import sys
import pickle
import requests
import youtube_dl
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

load_dotenv()

KEY=os.environ.get("KEY")
BASE_URL="https://www.googleapis.com/youtube/v3"

PAYLOAD = dict()

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

	if not qss:
		return False, None

	try:
		if urlType == "video":
			videoId = qss['v'].pop()

			PAYLOAD["id"] = videoId

			r = requests.get(BASE_URL+"/videos", params=PAYLOAD)
		else:
			playlistId = qss['list'].pop()
			
			PAYLOAD["id"] = playlistId

			r = requests.get(BASE_URL+"/playlists", params=PAYLOAD)

		# print(r.reason)
		found = r.json()['pageInfo']['totalResults']

		if found:
			details = r.json().get('items').pop()
			return True, details
	except Exception as e:
		err_name = type(e).__name__
		if err_name == "ConnectionError":
			print("Check your internet connection.")
			exit(1)
		else:
			raise e
	
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
	nextPageToken = r.json().get('nextPageToken')

	try:
		if items:
			totalItems += items
			while nextPageToken != None:
				PAYLOAD['pageToken'] = nextPageToken
				r = requests.get(BASE_URL+"/playlistItems", params=PAYLOAD)
				items = r.json().get('items')
				totalItems += items
				nextPageToken = r.json().get('nextPageToken')

			for x in totalItems:
				snippet = x.get("snippet")
				videoId = snippet.get("resourceId").get("videoId")
				yield { "url" : "https://youtube.com/watch?v=" + videoId,
										"id" : videoId,
										"title" : snippet.get("title"),
					}
				
		else:
			# print(r.json())
			print("Couldn't get playlist details. Try again")
			sys.exit(2)
	except Exception as e:
		print(f"Exception {e}")


class MyLogger(object):
	def debug(self, msg):
		pass

	def warning(self, msg):
		pass

	def error(self, msg):
		print(msg)

def print_hook(d):
	if d['status'] == 'finished':
		msg = "Downloaded {}".format(d['filename'])
	else:
		try:
			percent_str = d.get('_percent_str')
			downloaded_bytes = d.get('downloaded_bytes')
			total_bytes = d.get('total_bytes')
			elapsed = d.get('elapsed')
			eta = d.get('eta')
			speed = d.get('speed')
			msg = f"Downloaded: {percent_str} {speed_conv(downloaded_bytes)} of {speed_conv(total_bytes)}.\
			  Elapsed: {str(round(elapsed,2)).rjust(5)}s Speed: {speed_conv(speed)}/s "
		except Exception as e:
			msg = f"Downloaded: {percent_str} Unknown of Unknown.\
			  Elapsed: {str(round(elapsed,2)).rjust(5)}s Speed: Unknown/s "

	print(msg)
	print("\x1B[F\x1B[K", end="")

def return_hook(d):
	if d['status'] == 'finished':
		msg = "Downloaded finished"
	else:
		try:
			percent_str = d.get('_percent_str')
			downloaded_bytes = d.get('downloaded_bytes')
			total_bytes = d.get('total_bytes')
			elapsed = d.get('elapsed')
			eta = d.get('eta')
			speed = d.get('speed')
			msg = f"Downloaded: {percent_str} {speed_conv(downloaded_bytes)} of {speed_conv(total_bytes)}.\
			  Elapsed: {str(round(elapsed,2)).rjust(5)}s Speed: {speed_conv(speed)}/s "
		except Exception as e:
			msg = f"Downloaded: {percent_str} Unknown of Unknown.\
			  Elapsed: {str(round(elapsed,2)).rjust(5)}s Speed: Unknown/s "

	with open("/tmp/msg.pkl", "wb+") as fp:
		pickle.dump(msg, fp)

def speed_conv(b):
	if b > 10**6:
		return f"{round(b/10**6,2)} MB".rjust(10)
	elif b > 10**3:
		return f"{round(b/10**3,2)} KB".rjust(10)
	else:
		return f"{b} B".rjust(10)

def download_video(url, hook):

	msg = f"Downloading {url}"
	if hook == return_hook:
		with open("/tmp/msg.pkl", "wb+") as fp:
			pickle.dump(msg, fp)

	YDL_OPTS = {
		'format' : 'bestvideo+bestaudio/best',
		'logger' : MyLogger(),
		'progress_hooks' : [hook],
		'outtmpl' : r"%(title)s.%(ext)s",
		'ignore-errors': True,
		'updatetime' : False,
		'merge_output_format' : 'mkv'
	}
	
	try:
		with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
			ydl.download([url])
		#print()
	except Exception as e:
		print("Error :", e)
	except KeyboardInterrupt:
		print("Quitting.")
		sys.exit(1)
	
def extract_video_url(yt_url):
	YDL_OPTS = {
		"ignore-errors" : True,
		"format" : "best",
		'logger' : MyLogger(),
	}
	try:
		with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
			info = ydl.extract_info(yt_url, download=False)
			audio_url = info['formats'][-1]['url']
			acodec = info['formats'][-1]['acodec']
			return audio_url,acodec
	except Exception as e:
		print("Error :", e)
		return None, None

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
		
def parse_file(filename):
	playlist = []
	with open(filename) as f:
		for line in  f.readlines():
			# check if link or not
			valid, details = isValidURL(line)
			if valid:
				playlist.append({ "url": line.strip(),
								  "id" : details['id'],
							      "title" : details['snippet']['title']
								  })				
			else:
				result = search_video(line)
				if len(result) > 0:
						playlist.append(result[0])

	return playlist

