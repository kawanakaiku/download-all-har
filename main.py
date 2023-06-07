#!/usr/bin/env python3
import sys
import os
import json
import requests
import datetime
from urllib.parse import unquote
import base64
import dateutil.parser


br = True
try:
   import brotlicffi
except:
   try:
      import brotli
   except:
      # cannot decompress br
      br = False

def filename(url, response):
      file = url.split('://', 1)[1]
      dir = os.path.dirname(file)
      base = os.path.basename(file)
      dir = unquote(dir)
      base = base.split('?', 1)[0]
      base = unquote(base)
      if base == '':
         base = 'index.html'
      type = response['content-type'] if 'content-type' in response else ''
      if 'text/html' in type:
         if not base.endswith(('.html', '.htm', '.php', '.asp', '.aspx', '.jsp')):
            base = base + '.html'
      file = os.path.join(dir, base)
      return file, dir, base

def save_file(file, dir, content, response_headers):
      if os.path.isfile(file):
         return True
      try:
         os.makedirs(dir, exist_ok=True)
      except OSError as e:
         print(e)
         return True
      print(file)
      try:
         with open(file, 'wb') as f:
            f.write(content)
      except OSError as e:
         print(e)
         return
      utime_file(file, response_headers)
      return True



def utime_file(file, headers):
   try:
      utime = headers['last-modified']
      # utime = datetime.datetime.strptime(utime, '%a, %d %b %Y %H:%M:%S GMT').replace(tzinfo=datetime.timezone.utc).timestamp()
      utime = dateutil.parser.parse(headers["last-modified"]).replace(tzinfo=None).timestamp()
      os.utime(file, (utime, utime))
   except Exception as e:
      pass


## convert list to dicts

def conv(dicts):
   dict = {}
   for d in dicts:
      name = d['name']
      value = d['value']
      if name.startswith(':'):
         continue
      dict = dict | { name.lower() : value }
   return dict

def content_download(request):
   url = request['url']
   cookies = conv(request['cookies'])
   headers = conv(request['headers'])
   # headers = headers | { 'accept-encoding': 'identity' } # i dont know how to make requests decode gzip
   headers = headers | { 'accept-encoding': ', '.join( ['gzip', 'deflate'] + ( ['br'] if br else [] ) ) }
   headers.pop('if-modified-since', None) # avoid 304 code
   headers.pop('if-none-match', None) # avoid 304 code
   headers.pop('range', None) # avoid 206 code
   with session.get(url, stream=True, cookies=cookies, headers=headers) as r:
      # print(r.status_code)
      # r.raise_for_status()
      return r.status_code, r.content, r.headers

def content_from_har(content):
   text = content['text']
   try:
      content['encoding']
      return base64.b64decode(text)
   except:
      return text.encode('utf-8')
   

def save(i):
   request = i['request']
   # request_headers = conv(request['headers'])
   response = i['response']
   response_headers = conv(response['headers'])
   if response["_error"] == "net::ERR_BLOCKED_BY_CLIENT":
      return True
   url = request['url']
   file, dir, _ = filename(url, response_headers)
   if os.path.isfile(file):
      return True
   try:
      content = content_from_har(response['content'])
   except (PermissionError, OSError) as e:
      # file creation fail
      return False
   except:
      try:
         status_code, content, response_headers = content_download(request)
         if str(status_code)[0] == "4":
             print(f"Error downloading status_code {status_code}")
             return False
      except:
         return False
   save_file(file, dir, content, response_headers)
   return True

if __name__ == '__main__':
   har = sys.argv[1]
   session = requests.Session()
   ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
   session.headers.update({'User-Agent': ua})
   if os.path.isfile(har):
      text = open(har, "r", encoding='utf-8').read()
   else:
      print("Paste your json below and press enter.")
      text = ""
      while True:
         line = input()
         if line:
            text += '\n' + line
         else:
            break
   for i in json.loads(text)["log"]["entries"]:
      save(i)
