# ycl
Search, Play(audio), Download Youtube videos from the terminal

## Requirements

* Requires Youtube API

  Get it [here](https://developers.google.com/youtube/v3/getting-started)

  Add it as `export KEY=[YOUR YOUTUBE API TOKEN]` or store it in an `.env` file.

* Requires Gstreamer and its plugins

```bash
sudo apt install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
 gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools \
 gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-pulseaudio
```

## Install

```
pip3 install -e .
```


## Usage

```bash
ycl [QUERY]
```