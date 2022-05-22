# ycl
Simple application to search, play, download Youtube videos from the terminal

![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/subhrajitprusty/ycl/Tests/master?label=Tests&style=for-the-badge&logo=pytest)

## Requirements

* Python 3.6+
* [VLC](https://www.videolan.org/vlc/)
* [Youtube Data API v3 Key](https://www.slickremix.com/docs/get-api-key-for-youtube/)
  > Due to Google limiting quota on Youtube API, you should get your own key.

## Install

```
pip install -e .
```

Set your Youtube API Key:

_Linux_

Put this in your `~/.bashrc` or `~/.bash_profile`
```bash
export YOUTUBE_KEY="AIzaSyAZQ2vf2Y5wfDxj**************"
```

_Windows_

```cmd
setx YOUTUBE_KEY "AIzaSyAZQ2vf2Y5wfDxj**************"
```
> Note the environment variable will be available for the subsequent command prompts/terminals.


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
  --help                 Show this message and exit.
```


## Docker (Deprecated)

> Linux only

```bash
docker build -t ycl:latest .
docker run -it --device /dev/snd:/dev/snd ycl:latest
```

Inside the container

```bash
ycl --help
```

---
