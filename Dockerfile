FROM python:3.7-slim
RUN apt update && \
    apt install -y gstreamer1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 && \
    rm -rf /var/lib/apt/lists/*
ENV LANG=C.UTF-8
ADD . /ycl
WORKDIR /ycl
RUN pip install --no-cache-dir -e .
CMD [ "/bin/bash" ]
