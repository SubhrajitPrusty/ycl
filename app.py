from dotenv import load_dotenv
import os
import requests
import sys
import youtube_dl
from pick import pick

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
        print('Done downloading, now converting ...')

if len(sys.argv) > 1:
	q = " ".join(sys.argv[1:])
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

		options = [x["title"] for x in results]
		title = f"Search results for {q}"

		option, index = pick(options, title)

		url = f"{results[index]['url']}"
		print(url)

		options = ["Play", "Download"]
		title = "Choose what you want to do"
		option, index = pick(options, title)

		if option == "Download":
			YDL_OPTS = {
			'format' : 'bestvideo+bestaudio/best',
			'logger' : MyLogger(),
			'progress_hooks' : [my_hook],

			}
			
			with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
				ydl.download([url])

		elif option == "Play":
			print("Not implemented yet :(")
			sys.exit()
