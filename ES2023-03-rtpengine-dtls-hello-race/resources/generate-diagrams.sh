#!/bin/bash

docker run --rm -u "$(id -u):$(id -g)" \
    -v ./:/data minlag/mermaid-cli \
    -i valid.mmd -o valid.png

docker run --rm -u "$(id -u):$(id -g)" \
    -v ./:/data minlag/mermaid-cli \
    -i dos.mmd -o dos.png
