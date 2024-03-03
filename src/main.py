import json
import pycurl
import certifi
import urllib
import re

from io import BytesIO
from os import remove

buffer = BytesIO()

url = "https://login.ufgd.edu.br/"

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
useragent += " AppleWebKit/537.36 (KHTML, like Gecko)"
useragent += " Chrome/121.0.6167.85 Safari/537.36"

credentials = []
# crie um arquivo json válido, com as suas
# credenciais de acesso.
# ex: { "username": "test", "password": "test" }
#
with open("credentials.json") as f:
    credentials = json.load(f)

headers = {}
def header_func(header_line):
    header_line = header_line.decode('iso-8859-1')

    if ':' not in header_line:
        return

    name, value = header_line.split(':', 1)

    name = name.strip()
    value = value.strip()

    name = name.lower()

    headers[name] = value

def get_ufgdnet(set_cookie):
    ufgdnet = re.search(r'(UFGDNET=)(((\w){40})-([0-9]{11}))', set_cookie, re.ASCII)
    ufgdnet = ufgdnet.group(2)
    return str(ufgdnet)

def get_cookies(set_cookie):
    # TODO: tratar se o match é valido
    #
    cookies = {}

    token = re.search(r'(__AT=)((\w){40})', set_cookie, re.ASCII)
    cookies['token'] = token.group(2)

    play_session = re.search(r'(PLAY_SESSION=)((\w){40})', set_cookie, re.ASCII)
    cookies['play_session'] = play_session.group(2)

    return cookies

def get():
    req.setopt(req.URL, url);
    req.setopt(req.HEADERFUNCTION, header_func)
    req.perform()

def post(cookies, credentials):
    req.setopt(req.URL, url + 'login_form');

    req.setopt(req.HEADERFUNCTION, header_func)

    data_fmt = "authenticityToken=" + cookies['token']
    data_fmt += "&user.username=" + credentials['username']
    data_fmt += "&user.password=" + credentials['password']

    req.setopt(req.POSTFIELDS, data_fmt)
    # req.setopt(req.VERBOSE, True)

    req.perform()

req = pycurl.Curl()

req.setopt(req.USERAGENT, useragent)
req.setopt(req.COOKIEFILE, 'cookies.txt')
req.setopt(req.COOKIEJAR, 'cookies.txt')
req.setopt(req.WRITEDATA, buffer);
req.setopt(req.CAINFO, certifi.where())

get()

body = buffer.getvalue()

cookies = get_cookies(headers['set-cookie'])

post(cookies, credentials)
body = buffer.getvalue()

ufgdnet_token = get_ufgdnet(headers['set-cookie'])
print(ufgdnet_token)

req.close()
remove("cookies.txt")
