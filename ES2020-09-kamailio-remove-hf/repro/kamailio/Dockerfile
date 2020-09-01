FROM ubuntu:18.04

ARG KAMAILIO_VERSION

RUN echo "Building Kamailio ${KAMAILIO_VERSION}"

RUN printf "APT::Get::Assume-Yes \"true\";\nAPT::Get::force-yes \"true\";" > /etc/apt/apt.conf.d/90forceyes
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update

RUN apt-get install -y libpcre2-dev htop software-properties-common git bison gdb libssl-dev netcat inotify-tools net-tools sudo wget build-essential libmysqlclient-dev libunistring-dev autoconf flex screen rtpproxy g++ subversion gnuplot python libtool libxml2-dev vim tcpdump

WORKDIR /usr/local/src

COPY __download.sh __download.sh
RUN ./__download.sh

WORKDIR /usr/local/src/kamailio

COPY __buildsequence.sh __buildsequence.sh
RUN ./__buildsequence.sh

FROM ubuntu:18.04
COPY --from=0 /opt/kamailio/ /opt/kamailio/

RUN printf "APT::Get::Assume-Yes \"true\";\nAPT::Get::force-yes \"true\";" > /etc/apt/apt.conf.d/90forceyes
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update

RUN apt-get install -y libssl1.1 iproute2

COPY config/ /opt/kamailio/etc/kamailio/

WORKDIR /opt/run/kamailio

COPY run.sh run.sh

CMD [ "./run.sh" ]