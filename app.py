from dotenv import load_dotenv
import os
import requests
import sys
from pick import pick

load_dotenv()

KEY=os.environ.get("KEY")
BASE_URL="https://www.googleapis.com/youtube/v3"



PAYLOAD = {
	"part": "snippet",
	"maxResults": 25,
	"key" : KEY
}

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

		cmd = f"youtube-dl {results[index]['url']}"
		print(cmd)
		os.system(cmd)