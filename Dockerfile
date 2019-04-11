FROM ubuntu:latest
MAINTAINER Subhrajit Prusty "subhrajit1997@gmail.com"
RUN apt update -y
RUN apt install -y python3-pip python3-dev build-essential 
RUN apt install -y gstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good
ENV LANG=C.UTF-8
ADD . /ycl
WORKDIR /ycl
RUN pip3 install -e .
CMD [ "bash" ]