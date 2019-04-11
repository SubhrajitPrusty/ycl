# ycl
Search, Play(audio), Download Youtube videos from the terminal

## Requirements

* Requires Youtube API

  Get it [here](https://developers.google.com/youtube/v3/getting-started)

  Add it as `export KEY=[YOUR YOUTUBE API TOKEN]` or store it in an `.env` file.

* Requires Gstreamer and its plugins

```bash
sudo apt install gstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good
```

## Docker

```bash
docker build -t ycl:latest .
docker run -it ycl:latest --device /dev/snd
```
Inside the container

```
export KEY=[YOUR_YOUTUBE_API_KEY]
ycl
```

## Install

```
pip3 install -e .
```


## Usage

```bash
ycl [QUERY]
```