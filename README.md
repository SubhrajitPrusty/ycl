# ycl
Search, Play, Download Youtube videos from the terminal

## Requirements

* Python 3.6 and above
* FFMPEG (or videos wont get merged)

## Install

```
pip3 install -e .
```

Windows

> To properly setup ffpyplayer, follow instructions [here](http://matham.github.io/ffpyplayer/installation.html)


## Usage

```
Usage: ycl [OPTIONS] [QUERY]...

Options:
  -ps, --playlistsearch  Searches for playlists
  -v, --video            Use a direct video link
  -pl, --playlist        Use a direct playlist link or file
  -i, --interactive      Starts an interactive Terminal UI session
  -e, --export           Export A playlist to a local file
  -o, --output TEXT      Set output format container, eg: mp4, mkv
  --help                 Show this message and exit.```
```

> If you have problems with search, try replacing API KEY in `.env` file with your own.


## Docker

```bash
docker build -t ycl:latest .
docker run -it --device /dev/snd:/dev/snd ycl:latest
```

Inside the container

```
ycl --help
```

> May not work on Windows