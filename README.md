# ycl
Search, Play, Download Youtube videos from the terminal

## Requirements

* Python 3.6 and above

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
  -i, --interactive      Starts an interactive session
  --help                 Show this message and exit.```
```

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