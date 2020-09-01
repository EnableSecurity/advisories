#!/bin/bash
make PREFIX="/opt/kamailio" include_modules="" cfg
make all
make install
