FROM ocrd/core-cuda
ARG VCS_REF
ARG BUILD_DATE
MAINTAINER unixprog@gmail.com
LABEL maintainer="https://ocr-d.de"
LABEL org.label-schema.vendor="DFG-Funded Initiative for Optical Character Recognition Development"
LABEL org.label-schema.name="ocrd_kraken"
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.vcs-url="https://github.com/OCR-D/ocrd_kraken"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.opencontainers.image.vendor="DFG-Funded Initiative for Optical Character Recognition Development"
LABEL org.opencontainers.image.title="ocrd_kraken"
LABEL org.opencontainers.image.description="Kraken bindings"
LABEL org.opencontainers.image.source="https://github.com/OCR-D/ocrd_kraken"
LABEL org.opencontainers.image.documentation="https://github.com/OCR-D/ocrd_kraken/blob/${VCS_REF}/README.md"
LABEL org.opencontainers.image.revision=$VCS_REF
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.base.name=ocrd/core-cuda

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

