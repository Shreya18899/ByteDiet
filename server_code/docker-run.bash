#!/bin/bash
#
# Linux/Mac BASH script to run docker container
#
docker run -it -u user -w /home/user -v .:/home/user -p 8081:8081 --rm server_code bash
