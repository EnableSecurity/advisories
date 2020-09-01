#!/bin/bash

if [ ! -f "kamailio-${KAMAILIO_VERSION}_src.tar.gz" ]; then
  wget "https://www.kamailio.org/pub/kamailio/${KAMAILIO_VERSION}/src/kamailio-${KAMAILIO_VERSION}_src.tar.gz"
fi

if [ ! -d "kamailio-${KAMAILIO_VERSION}_src" ]; then
  tar xzvf kamailio-${KAMAILIO_VERSION}_src.tar.gz
  mv "kamailio-${KAMAILIO_VERSION}" kamailio
fi

