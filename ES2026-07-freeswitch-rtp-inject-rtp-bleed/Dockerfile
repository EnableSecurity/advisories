# Build exact public FreeSWITCH release tags without private images or package credentials.
FROM debian:bookworm
ARG DEBIAN_FRONTEND=noninteractive
ARG TAG
ARG REF

RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake build-essential ca-certificates cmake git libtool libtool-bin \
      pkg-config libssl-dev libcurl4-openssl-dev zlib1g-dev uuid-dev \
      libpcre3-dev libsqlite3-dev libedit-dev libspeex-dev libspeexdsp-dev \
      libopus-dev libsndfile1-dev libjpeg-dev libtiff-dev libldns-dev \
      libglib2.0-dev libpng-dev procps \
    && rm -rf /var/lib/apt/lists/*

ENV PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib/x86_64-linux-gnu/pkgconfig

RUN git clone --depth 1 --branch v3.1.1 https://github.com/freeswitch/spandsp.git /tmp/spandsp \
    && cd /tmp/spandsp && ./bootstrap.sh && ./configure --prefix=/usr/local \
    && make -j2 && make install \
    && git clone --depth 1 --branch v1.13.18 https://github.com/freeswitch/sofia-sip.git /tmp/sofia-sip \
    && cd /tmp/sofia-sip && ./bootstrap.sh && ./configure --prefix=/usr/local \
    && make -j2 && make install && ldconfig \
    && rm -rf /tmp/spandsp /tmp/sofia-sip

COPY modules.conf /tmp/modules.conf
RUN test -n "$TAG" && test -n "$REF" \
    && git clone --depth 1 --branch "$TAG" https://github.com/signalwire/freeswitch.git /usr/src/freeswitch \
    && cd /usr/src/freeswitch \
    && test "$(git rev-parse HEAD)" = "$REF" \
    && cp /tmp/modules.conf modules.conf \
    && ./bootstrap.sh -j \
    && ./configure --with-erlang=no --disable-dependency-tracking --disable-libvpx --disable-libyuv \
    && make -j2 && make install && ldconfig

WORKDIR /usr/local/freeswitch
ENTRYPOINT ["/usr/local/freeswitch/bin/freeswitch"]
CMD ["-nf", "-nonat"]
