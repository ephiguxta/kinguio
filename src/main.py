import json
import pycurl
import certifi
import urllib
import re

from io import BytesIO

buffer = BytesIO()
url = "https://login.ufgd.edu.br/"

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

def get_token(set_cookie):
    match = re.search(r'(__AT=)((\w){40})', set_cookie, re.ASCII)

    # TODO: tratar se o match é valido
    return match.group(2)

req = pycurl.Curl()
req.setopt(req.URL, url);
req.setopt(req.WRITEDATA, buffer);
req.setopt(req.CAINFO, certifi.where())
req.setopt(req.HEADERFUNCTION, header_func)

req.perform()

body = buffer.getvalue()
authenticity_token = get_token(headers['set-cookie'])

print(authenticity_token)
