#
# Client-side python app for photoapp, this time working with
# web service, which in turn uses AWS S3 and RDS to implement
# a simple photo application for photo storage and viewing.
#
# Authors:
#   
#   Chanipa Sangphet
#
#   Starter code: Prof. Joe Hummel
#   Northwestern University
#

import requests  # calling web service
import jsons  # relational-object mapping

import uuid
import pathlib
import logging
import sys
import os
import base64
import time

from configparser import ConfigParser

# doesn't work in docker (not easily):
# import matplotlib.pyplot as plt
# import matplotlib.image as img


###################################################################
#
# classes
#

class ImageAsset:
  assetid: int  # these must match columns from DB table
  assetname: str
  bucketkey: str
  height: int  
  width: int  
  is_compressed: bool

class BucketItem:
  Key: str
  LastModified: str
  ETag: str
  Size: int
  StorageClass: str


###################################################################
#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 400, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    
def web_service_put(url,data):
  try:
    retries = 0
    
    while True:
      response = requests.put(url,json=data)
      if response.status_code in [200, 400, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_put() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None

def web_service_post(url,data):
  try:
    retries = 0
    
    while True:
      response = requests.post(url,json=data)
      # print(f'response.status_code :{response.status_code}')
      if response.status_code in [200,400, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_post() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
  
###################################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number
  
  Parameters
  ----------
  None
  
  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """

  try:
    print()
    print(">> Enter a command:")
    print("   0 => end")
    print("   1 => upload")

    cmd = int(input())
    return cmd

  except Exception as e:
    print("ERROR")
    print("ERROR: invalid input")
    print("ERROR")
    return -1

###################################################################
#
# upload
#
def upload(baseurl):
  """
  Prompts the user for a local filename and user id, 
  and uploads that asset (image) to the user's folder 
  in the bucket. The asset is given a random, unique 
  name. The database is also updated to record the 
  existence of this new asset in S3.
  
  Parameters
  ----------
  baseurl: baseurl for web service
  
  Returns
  -------
  nothing
  """

  try:
    print("Enter local filename>")
    local_filename = input()

    if not pathlib.Path(local_filename).is_file():
      print("Local file '", local_filename, "' does not exist...")
      return

    print("Enter resize width>")
    width = input()
    
    print("Enter resize height>")
    height = input()
    #
    # build the data packet:
    #
    infile = open(local_filename, "rb")
    bytes = infile.read()
    infile.close()

    #
    # now encode the image as base64. Note b64encode returns
    # a bytes object, not a string. So then we have to convert
    # (decode) the bytes -> string, and then we can serialize
    # the string as JSON for upload to server:
    #
    data = base64.b64encode(bytes)
    datastr = data.decode()

    data = {"assetname": local_filename, "data": datastr,"width":width, "height":height}

    #
    # call the web service:
    #
    api = '/image'
    url = baseurl + api

    res = web_service_post(url, data)
    print(f'res--- {res.json()}')
    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code in [400, 500]:  # we'll have an error message
        body = res.json()
        print("Error message:", body["message"])
      #
      return

    #
    # success, extract userid:
    #
    body = res.json()

    assetid = body["assetid"]

    print("Image uploaded, asset id =", assetid)

  except Exception as e:
    logging.error("upload() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


#########################################################################
# main
#
print('** Welcome to PhotoApp v2 **')
print()

# eliminate traceback so we just get error message:
sys.tracebacklimit = 0

#
# what config file should we use for this session?
#
config_file = 'client_config.ini'
# config_file = 'ec2-client-config.ini'

print("What config file to use for this session?")
print("Press ENTER to use default (client_config.ini),")
print("otherwise enter name of config file>")
s = input()

if s == "":  # use default
  pass  # already set
else:
  config_file = s

#
# does config file exist?
#
if not pathlib.Path(config_file).is_file():
  print("**ERROR: config file '", config_file, "' does not exist, exiting")
  sys.exit(0)

#
# setup base URL to web service:
#
configur = ConfigParser()
configur.read(config_file)
baseurl = configur.get('client', 'webservice')

#
# make sure baseurl does not end with /, if so remove:
#
if len(baseurl) < 16:
  print("**ERROR**")
  print("**ERROR: baseurl '", baseurl, "' in .ini file is empty or not nearly long enough, please fix")
  sys.exit(0)

if baseurl.startswith('https'):
  print("**ERROR**")
  print("**ERROR: baseurl '", baseurl, "' in .ini file starts with https, which is not supported (use http)")
  sys.exit(0)

lastchar = baseurl[len(baseurl) - 1]
if lastchar == "/":
  baseurl = baseurl[:-1]

# print(baseurl)

#
# main processing loop:
#
cmd = prompt()

while cmd != 0:
  #

  if cmd == 1:
    upload(baseurl)
  else:
    print("** Unknown command, try again...")
  #
  cmd = prompt()

#
# done
#
print()
print('** done **')
