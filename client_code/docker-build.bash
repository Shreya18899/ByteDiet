#!/bin/bash
#
# Linux/Mac BASH script to build docker container
#
docker rmi client_code
docker build -t client_code .
