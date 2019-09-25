# ycl
Search, Play, Download Youtube videos from the terminal

## Requirements

* Python 3.6 and above
* Requires Gstreamer and its plugins

```bash
sudo apt install gstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 
```

## Install

```
pip3 install pycairo
pip3 install PyGobject
pip3 install -e .
```

## Usage

```
Usage: ycl [OPTIONS] [QUERY]...

Options:
  -ps, --playlistsearch  Searches for playlists
  -v, --video            Use a direct video link
  -pl, --playlist        Use a direct playlist link
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


