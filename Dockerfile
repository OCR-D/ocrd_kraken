ARG DOCKER_BASE_IMAGE
FROM $DOCKER_BASE_IMAGE
ARG VCS_REF
ARG BUILD_DATE
LABEL \
    maintainer="https://ocr-d.de/kontakt" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/OCR-D/ocrd_kraken" \
    org.label-schema.build-date=$BUILD_DATE \
    org.opencontainers.image.vendor="DFG-Funded Initiative for Optical Character Recognition Development" \
    org.opencontainers.image.title="ocrd_kraken" \
    org.opencontainers.image.description="Kraken bindings" \
    org.opencontainers.image.source="https://github.com/OCR-D/ocrd_kraken" \
    org.opencontainers.image.documentation="https://github.com/OCR-D/ocrd_kraken/blob/${VCS_REF}/README.md" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE \
    org.opencontainers.image.base.name=ocrd/core-cuda

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

