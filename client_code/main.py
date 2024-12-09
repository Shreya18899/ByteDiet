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

import requests  
import jsons 
import json

import uuid
import pathlib
import logging
import sys
import os
import base64
import time
import boto3 
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

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
  is_resized: bool

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
        break

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
        break

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
        break

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
    print("   2 => assets")
    print("   3 => convert image(s) to PDF") 
    print("   4 => Extract Text from image")

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

###################################################################
#
# assets
#
def assets(baseurl):
  """
  Prints out all the assets in the database
  
  Parameters
  ----------
  baseurl: baseurl for web service
  
  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/assets'
    url = baseurl + api

    # res = requests.get(url)
    res = web_service_get(url)

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
    # deserialize and extract assets:
    #
    body = res.json()
    #
    # let's map each dictionary into an Asset object:
    #
    assets = []
    for row in body["data"]:
      asset = jsons.load(row, ImageAsset)
      assets.append(asset)
    #
    # Now we can think OOP:
    #
    for asset in assets:
      print(asset.assetid)
      print(" ", asset.assetname)
      print(" ", asset.bucketkey)

  except Exception as e:
    logging.error("assets() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

###################################################################
#
# convert_to_pdf
#
def convert_to_pdf(baseurl):
    """
    Prompts the user for one or more asset IDs, retrieves their corresponding S3 keys,
    sends a request to the server to convert these images into a PDF, and handles the response.
    
    Parameters
    ----------
    baseurl: baseurl for web service
    
    Returns
    -------
    nothing
    """

    try:
        print("Enter asset ID(s) to include in PDF (separated by commas)>")
        asset_ids_input = input()
        asset_ids = [aid.strip() for aid in asset_ids_input.split(",") if aid.strip().isdigit()]
        
        if not asset_ids:
            print("No valid asset IDs entered.")
            return

        s3_keys = []
        for aid in asset_ids:
            # Assume there's an endpoint to get asset details by asset ID
            api = f'/image/{aid}'
            url = baseurl + api
            res = web_service_get(url)
            if res is None:
                print(f"Failed to retrieve details for asset ID {aid}.")
                continue

            if res.status_code != 200:
                print(f"Failed to retrieve asset ID {aid} with status code {res.status_code}.")
                try:
                    body = res.json()
                    print("Error message:", body.get("message", "No message provided"))
                except jsons.JSONDecodeError:
                    print("No JSON response received.")
                continue

            body = res.json()
            bucket_key = body.get("bucketkey")
            if bucket_key:
                s3_keys.append(bucket_key)
                print(f"Asset ID {aid} mapped to S3 key {bucket_key}.")
            else:
                print(f"No S3 key found for asset ID {aid}.")

        if not s3_keys:
            print("No valid S3 keys found for the provided asset IDs.")
            return

        print("Enter name for the PDF (without extension)>")
        pdf_name = input().strip()
        if not pdf_name:
            print("Invalid PDF name.")
            return

        # Prepare data for /image-to-pdf endpoint
        data = {
            "images": s3_keys,
            "pdfName": pdf_name
        }

        api = '/image-to-pdf'
        url = baseurl + api
        print("url being accessed is : ", url)

        res = web_service_post(url, data)
        if res is None:
            print("Failed to get a response from the server.")
            return

        if res.status_code != 200:
            # failed:
            print("Failed to convert images to PDF with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  # we'll have an error message
                try:
                    body = res.json()
                    print("Error message:", body.get("message", "No message provided"))
                except jsons.JSONDecodeError:
                    print("No JSON response received.")
            return

        # success, extract PDF URL
        body = res.json()
        pdf_url = body.get("pdfUrl")
        pdf_id = body.get("pdfId")
        if pdf_url and pdf_id != -1:
            print("PDF created successfully.")
            print(f"PDF ID: {pdf_id}")
            print(f"PDF URL: {pdf_url}")
        else:
            print("Failed to create PDF. Server did not return a valid PDF URL.")

    except Exception as e:
        logging.error("convert_to_pdf() failed:")
        logging.error(e)
        return


def extract_text_from_image(baseurl):
    """
    Prompts the user for an asset id, sends a request to the server to extract text from the image,
    and downloads the extracted text from S3.
    
    Parameters
    ----------
    baseurl: baseurl for web service
    
    Returns
    -------
    nothing
    """
    try:
        print("Enter asset ID to extract text from>")
        asset_id_input = input().strip()

        if not asset_id_input.isdigit():
            print("Invalid asset ID. It should be a number.")
            return

        asset_id = int(asset_id_input)

        # Prepare data for /extract-text-from-pdf endpoint
        data = {
            "assetid": asset_id
        }

        api = '/extract-text-from-image'
        url = baseurl + api
        print(f"Requesting text extraction from asset ID {asset_id}...")

        res = web_service_post(url, data)


        if res is None:
            print("Failed to get a response from the server.")
            return

        if res.status_code == 404:
                    print(f"Asset ID {asset_id} not found. Please enter a valid asset id")
                    return

        if res.status_code != 200:
            # failed:
            print("Failed to extract text from image with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  
                try:
                    body = res.json()
                    print("Error message:", body.get("message", "No message provided"))
                except json.JSONDecodeError:
                    print("No JSON response received.")
            return
        else:
           print("Job Completed. Check s3 folder textract_jobs for results")
    except Exception as e:
        logging.error("extract_text_from_image() failed:")
        logging.error(e)
        return

###################################################################
#
# extract_text_from_image
#
#########################################################################
# main
#
print('** Welcome to the Nutrition App. We look forward to help you with any specifications you might need on your food intake**')
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
    # resizing function
    upload(baseurl)
  elif cmd == 2:
    # list the assets
    assets(baseurl)
  elif cmd == 3:
    # convert image to pdf
    convert_to_pdf(baseurl)
  elif cmd == 4:
     # extract text from image
     extract_text_from_image(baseurl)
  else:
    print("** Unknown command, try again...")
  #
  cmd = prompt()

#
# done
#
print()
print('** done **')