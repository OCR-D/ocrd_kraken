FROM ocrd/core
ARG VCS_REF
ARG BUILD_DATE
LABEL \
    maintainer="https://ocr-d.de/kontakt" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/OCR-D/ocrd_tesserocr" \
    org.label-schema.build-date=$BUILD_DATE

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PIP pip3

# avoid HOME/.local/share (hard to predict USER here)
# so let XDG_DATA_HOME coincide with fixed system location
# (can still be overridden by derived stages)
ENV XDG_DATA_HOME /usr/local/share

WORKDIR /build-ocrd
COPY setup.py .
COPY ocrd_kraken ./ocrd_kraken
COPY ocrd_kraken/ocrd-tool.json .
COPY README.md .
COPY requirements.txt .
COPY Makefile .
RUN make deps-ubuntu \
    && make deps install \
    && rm -fr /build-ocrd

WORKDIR /data
VOLUME /data

