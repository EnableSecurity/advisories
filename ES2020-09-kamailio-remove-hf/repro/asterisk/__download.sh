#!/bin/bash

if [ ! -f "asterisk-${ASTERISK_VERSION}.tar.gz" ]; then
  wget "http://downloads.asterisk.org/pub/telephony/asterisk/releases/asterisk-${ASTERISK_VERSION}.tar.gz"
fi

if [ ! -d "asterisk-${ASTERISK_VERSION}" ]; then
  tar xzvf "asterisk-${ASTERISK_VERSION}.tar.gz"
  mv "asterisk-${ASTERISK_VERSION}" asterisk
fi

