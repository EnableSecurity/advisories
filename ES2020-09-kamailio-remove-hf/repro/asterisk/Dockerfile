FROM ubuntu:18.04

ARG ASTERISK_VERSION

RUN echo "Building Asterisk ${ASTERISK_VERSION}"

RUN printf "APT::Get::Assume-Yes \"true\";\nAPT::Get::force-yes \"true\";" > /etc/apt/apt.conf.d/90forceyes
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update

RUN apt-get install -y libpopt-dev libnewt-dev ethtool libpq-dev libbluetooth-dev python-dev doxygen autoconf wget screen libusb-dev libspeex-dev aptitude libsqlite0-dev libsnmp-dev uuid lua5.1 libopus-dev build-essential inotify-tools libxslt1-dev subversion libfreeradius-dev libtool libspandsp-dev freetds-dev uuid-dev libvpb-dev libsqlite3-dev portaudio19-dev liblua5.3-dev software-properties-common tcpdump libxml2-dev libedit-dev libopusfile-dev bison libvorbis-dev libasound2-dev libjack-dev g++ libjansson-dev liblua5.1-0-dev vim binutils-dev libtermkey-dev gdb unixodbc-dev gnuplot htop libogg-dev flex libiksemel-dev libgsm1-dev ncurses-dev libgtk2.0-dev python libical-dev netcat git libsrtp-dev libssl-dev net-tools

WORKDIR /usr/local/src

COPY __download.sh __download.sh
RUN ./__download.sh

WORKDIR /usr/local/src/asterisk

COPY __buildsequence.sh __buildsequence.sh
RUN ./__buildsequence.sh

FROM ubuntu:18.04
COPY --from=0 /opt/asterisk/ /opt/asterisk/

RUN printf "APT::Get::Assume-Yes \"true\";\nAPT::Get::force-yes \"true\";" > /etc/apt/apt.conf.d/90forceyes
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update

RUN apt-get install -y libxml2 libjansson4 libsqlite3-0 libxslt1.1 libncurses5 openssl uuid liburiparser1 libbinutils libedit2 libgsm1 iproute2 libcap2

COPY config/* /opt/asterisk/etc/asterisk/

WORKDIR /opt/run/asterisk

COPY run.sh run.sh

CMD [ "./run.sh" ]