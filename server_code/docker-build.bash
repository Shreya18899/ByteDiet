#!/bin/bash
#
# Linux/Mac BASH script to build docker container
#
docker rmi server_code
docker build -t server_code .
# docker build -t server_code .
# docker build --no-cache -t nodejs-express-server-app . --progress=plain