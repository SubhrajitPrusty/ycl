import re
import requests

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) \
             AppleWebKit/537.343 (KHTML, like Gecko) \
             Chrome/53.0.2785.143 \
             Safari/537.43"


def cleanhtml(raw_html):
    cleantext = re.sub('<.*?>|<div.*', '', raw_html)
    return(cleantext)


def fetch_lyrics(song):
    song = song.replace(' ', '+')
    url = 'https://www.google.com/search?q=' + song + '+lyrics'
    r = requests.get(
        url,
        headers={'user-agent': USER_AGENT}
    )

    song = scrape(str(r.text))
    return song


def scrape(text):
    p1 = text.find('<span jsname')
    p2 = text.find('>Source:&nbsp;<a href', p1) - 1
    lines = text[p1:p2].split('<br>')
    lyrics = []
    for line in lines:
        if "YS01Ge" in line:
            lyrics.append(line)
    lyrics = cleanhtml('\n'.join(lyrics))
    return lyrics


def padlyrics(start, lyrics, size):
    lyrics = lyrics[start:]
    if size <= len(lyrics):
        lyrics = lyrics[:size]
    return lyrics


def fetch_sub_from_link(url):
    r = requests.get(
        url,
        headers={'user-agent': USER_AGENT}
    )

    sub = str(r.text).split('\n')[4:]
    subtitle = []
    i = -1
    for x in sub:
        if x.strip() == '':
            continue
        if '-->' in x:
            start, end = x.split('-->')
            start = start.split('.')[0].strip()
            end = end.split('.')[0].strip()
            # subtitle.append({'start':start,'end':end,'text':''})
            start = start.split(':')
            start = int(start[0]) * 3600 + int(start[1]) * 60 + int(start[2])
            end = end.split(':')
            end = int(end[0]) * 3600 + int(end[1]) * 60 + int(end[2])
            subtitle.append({'start': start, 'end': end, 'text': ''})
            i += 1
        else:
            subtitle[i]['text'] += " " + x.strip()
    return subtitle
