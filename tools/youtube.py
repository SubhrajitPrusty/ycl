import re
import os
import sys
import pickle
import requests
import youtube_dl
from loguru import logger
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

load_dotenv()

KEY = os.environ.get("KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

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
    # logger.debug(f"{parsed}: {qss}")

    if not qss:
        return False, None

    try:
        if urlType == "video":
            videoId = qss['v'].pop()

            PAYLOAD["id"] = videoId

            r = requests.get(BASE_URL + "/videos", params=PAYLOAD)
        else:
            playlistId = qss['list'].pop()

            PAYLOAD["id"] = playlistId

            r = requests.get(BASE_URL + "/playlists", params=PAYLOAD)

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

    r = requests.get(BASE_URL + "/search", params=PAYLOAD)

    items = r.json().get('items')

    results = []

    if items:
        for x in items:
            videoId = x.get("id")
            if videoId.get("kind") == "youtube#video":
                results.append(
                    {
                        "url": f"https://youtube.com/watch?v={videoId.get('videoId')}",  # noqa : E501
                        "id": videoId.get("videoId"),
                        "title": x["snippet"]["title"],
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

    r = requests.get(BASE_URL + "/search", params=PAYLOAD)

    items = r.json().get('items')

    results = []

    if items:
        for x in items:
            playlistId = x.get("id")
            if playlistId.get("kind") == "youtube#playlist":
                results.append(
                    {
                        "url": f"https://youtube.com/playlist?list={playlistId.get('playlistId')}",  # noqa : E501
                        "id": playlistId.get("playlistId"),
                        "title": x["snippet"]["title"],
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

    r = requests.get(BASE_URL + "/playlistItems", params=PAYLOAD)

    items = r.json().get('items')

    # playlistItems = []
    totalItems = []

    # totalResults = r.json()['pageInfo']['totalResults']
    nextPageToken = r.json().get('nextPageToken')

    try:
        if items:
            totalItems += items
            while nextPageToken is not None:
                PAYLOAD['pageToken'] = nextPageToken
                r = requests.get(BASE_URL + "/playlistItems", params=PAYLOAD)
                items = r.json().get('items')
                totalItems += items
                nextPageToken = r.json().get('nextPageToken')

            for x in totalItems:
                snippet = x.get("snippet")
                videoId = snippet.get("resourceId").get("videoId")
                yield {"url": "https://youtube.com/watch?v=" + videoId,
                       "id": videoId,
                       "title": snippet.get("title"),
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
    filename = ".".join(d['filename'].split(".")[:-2] + ["mkv"])
    if d['status'] == 'finished':
        print("\x1B[FDownloaded {}".format(filename))
    elif d['status'] == 'downloading':
        try:
            percent_str = d.get('_percent_str')
            print(percent_str, end='\r')
        except Exception:
            pass
    elif d['status'] == 'error':
        print("err")
        return


def return_hook(d):
    if d['status'] == 'finished':
        msg = "Downloaded {}".format(d['filename'])
    else:
        try:
            percent_str = d.get('_percent_str')
            downloaded_bytes = d.get('downloaded_bytes')
            total_bytes = d.get('total_bytes')
            elapsed = d.get('elapsed')
            speed = d.get('speed')
            msg = f"Downloading: {percent_str}\
                 {speed_conv(downloaded_bytes)}\
                 of {speed_conv(total_bytes)}.\
                 Elapsed: {str(round(elapsed,2)).ljust(5)}s\
                 Speed: {speed_conv(speed)}/s "
        except Exception:
            msg = f"Downloading: {percent_str}\
                 NA of NA.\
                 Elapsed: {str(round(elapsed,2)).ljust(5)}s\
                 Speed: Unknown/s "

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
        'format': 'bestvideo+bestaudio',
        'logger': MyLogger(),
        'progress_hooks': [hook],
        'outtmpl': r"%(title)s.%(ext)s",
        'ignore-errors': True,
        'updatetime': False,
        'merge_output_format': 'mkv',
    }

    try:
        with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([url])
        # print()
    except Exception as e:
        print("Error :", e)
    except KeyboardInterrupt:
        print("Quitting.")
        sys.exit(1)


def extract_video_url(yt_url):
    YDL_OPTS = {
        "ignore-errors": True,
        "format": "best",
        'logger': MyLogger(),
    }
    try:
        with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            audio_url = info['formats'][-1]['url']
            acodec = info['formats'][-1]['acodec']
            return audio_url, acodec
    except Exception as e:
        print("Error :", e)
        return None, None


def extract_audio_url(yt_url):
    YDL_OPTS = {
        "ignore-errors": True,
        "format": "bestaudio[acodec=opus]",
        'logger': MyLogger(),
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


@logger.catch
def extract_video_sublink(yt_url):
    YDL_OPTS = {
        "ignore-errors": True,
        'logger': MyLogger(),
        "writeautomaticsub": True,
    }
    try:
        with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
            if (info := ydl.extract_info(yt_url, download=False)) is not None:
                if (req_subs := info.get('requested_subtitles')) is not None:
                    if (subtitle := req_subs.get('en')) is not None:
                        sub_url = subtitle.get('url')
                        _ = subtitle.get('ext')
                        return sub_url
            else:
                return None
    except Exception as e:
        logger.error(e)
        return None


def parse_file(filename):
    playlist = []
    with open(filename, encoding='utf8') as f:
        for line in f.readlines():
            # check if link or not
            url, title = parse_line(line)
            # logger.debug(f"{line}: {valid}")
            valid, details = isValidURL(url)
            # logger.debug(f"valid={valid} | url={url} | title={title}")

            if valid:
                playlist.append({"url": line.strip(),
                                 "id": details['id'],
                                 "title": details['snippet']['title']
                                 })
            else:
                result = search_video(line)
                if len(result) > 0:
                    playlist.append(result[0])

    return playlist


def parse_line(line):
    split_line = line.split(',')
    regex = re.compile('^http[s]?://.*')
    if len(split_line) == 1:
        url = split_line[0]
        title = ''
    else:
        url = split_line[0]
        title = ','.join(split_line[1:])

    # check if actually url
    reg_match = regex.match(url)
    # logger.debug(f'regex_match={reg_match}')
    if not reg_match:
        return None, line

    return url, title
