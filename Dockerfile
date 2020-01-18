FROM python:3.7-slim
ENV LANG=C.UTF-8
ADD . /ycl
WORKDIR /ycl
RUN pip install --no-cache-dir -e .
CMD [ "/bin/bash" ]
