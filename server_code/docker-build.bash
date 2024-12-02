#!/bin/bash
#
# Linux/Mac BASH script to build docker container
#
docker rmi server_code
docker build -t server_code .
