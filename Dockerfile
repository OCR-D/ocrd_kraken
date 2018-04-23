FROM ocrd/core
MAINTAINER OCR-D
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

WORKDIR /build-ocrd
COPY setup.py .
COPY requirements.txt .
COPY README.rst .
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
    ca-certificates \
    make \
    git
COPY ocrd_kraken ./ocrd_kraken
RUN pip3 install --upgrade pip
RUN make deps-pip install

ENTRYPOINT ["/bin/sh", "-c"]
