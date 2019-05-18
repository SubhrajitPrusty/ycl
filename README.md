# ycl
Search, Play(audio), Download Youtube videos from the terminal

## Requirements

* Requires Gstreamer and its plugins

```bash
sudo apt install gstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
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

## Install

```
pip3 install -e .
```


## Usage

```bash
Usage: ycl [OPTIONS] [QUERY]...

Options:
  -pl, --playlist  Searches for playlists
  --help           Show this message and exit.
```