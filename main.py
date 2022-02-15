import os
import json
import requests
from datetime import datetime as dt
from urllib.parse import unquote




br = True
try:
   import brotlicffi
except:
   try:
      import brotli
   except:
      # cannot decompress br
      br = False

def wget(url, cookies="", headers=""):
      file = url.split('://', 1)[1]
      file = unquote(file)
      dir = os.path.dirname(file)
      base = os.path.basename(file)
      if base == '':
         base = 'index.html'
      base = base.split('?', 1)[0]
      file = os.path.join(dir, base)
      if os.path.isfile(file):
         return
      try:
         os.makedirs(dir, exist_ok=True)
      except OSError as e:
         print(e)
         return
      print(file)
      with session.get(url, stream=True, cookies=cookies, headers=headers) as r:
         print(r.status_code)
         # r.raise_for_status()
         content = r.content
         try:
            with open(file, 'wb') as f:
               f.write(content)
         except OSError as e:
            print(e)
            return
         try:
            utime = r.headers['last-modified']
            utime = dt.strptime(utime, '%a, %d %b %Y %H:%M:%S GMT').timestamp()
         except:
            utime = ""
            pass
      if utime:
         os.utime(file, (utime, utime))


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

def dl(i):
   if i["response"]["_error"] == "net::ERR_BLOCKED_BY_CLIENT":
      return
   r = i['request']
   url = r['url']
   cookies = conv(r['cookies'])
   headers = conv(r['headers'])
   # headers = headers | { 'accept-encoding': 'identity' } # i dont know how to make requests decode gzip
   # headers = headers | { 'accept-encoding': ', '.join( ['gzip', 'deflate'] + ( ['br'] if br else [] ) ) }
   headers.pop('if-modified-since', None) # avoid 304 code
   headers.pop('if-none-match', None) # avoid 304 code
   headers.pop('range', None) # avoid 206 code
   #print(cookies)
   #print(headers)
   wget(url, cookies, headers)

if __name__ == '__main__':
   session = requests.Session()
   ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
   session.headers.update({'User-Agent': ua})
   if os.path.isfile("u.json"):
      text = open("u.json","r").read()
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
      dl(i)
