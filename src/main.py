import json
import pycurl
import certifi
import urllib
import re
import gzip

from io import BytesIO
from os import remove

buffer = BytesIO()

url_pre_login = "https://login.app.ufgd.edu.br/login"
url_post_login = "https://ufgdnet.app.ufgd.edu.br"

url_sigecad = "https://sigecad-academico.ufgd.edu.br"

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

    if name in headers:
        if isinstance(headers[name], list):
            headers[name].append(value)
        else:
            headers[name] = [headers[name], value]
    else:
        headers[name] = value

def get_ufgdnet(set_cookie):
    ufgdnet = ''

    for element in set_cookie:
        pattern = r'(UFGDNET=)(((\w){40})-([0-9]{11}))'
        match = re.search(pattern, element, re.ASCII)

        if match is not None and len(match.group(2)) == 52:
            ufgdnet = match.group(2)
            break

    return ufgdnet

def get_cookies(set_cookie):
    # TODO: tratar se o match é valido
    #
    cookies = {}

    # passa pelos elementos do set_cookie procurando o play_session
    for element in set_cookie:
        match = re.search(r'(PLAY_SESSION=)((\w){40})', element, re.ASCII)

        if match is not None and len(match.group(2)) == 40:
            cookies['play_session'] = match.group(2)
            break

    # faz o mesmo que o loop acima mas procurando pelo authenticityToken,
    # TODO: código redundante em relação ao loop acima
    for element in set_cookie:
        match = re.search(r'(__AT=)((\w){40})', element, re.ASCII)

        if match is not None and len(match.group(2)) == 40:
            cookies['token'] = match.group(2)
            break

    return cookies

def get(url, endpoint=""):
    req.setopt(req.URL, url + endpoint);
    req.setopt(req.HEADERFUNCTION, header_func)
    req.perform()
    # req.setopt(req.VERBOSE, True)

def post(url, cookies, credentials):
    req.setopt(req.URL, url + "_form");

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

# get para pegar o authenticityToken e o play_session
get(url_pre_login)

body = buffer.getvalue()
cookies = get_cookies(headers['set-cookie'])

post(url_pre_login, cookies, credentials)
body = buffer.getvalue()

ufgdnet_token = get_ufgdnet(headers['set-cookie'])

# GET para obter o json dos períodos letivos,
# ele é feito num endpoint /rest/...
# req.setopt(req.VERBOSE, True)
req.setopt(req.HTTPGET, 1)

endpoint = "/rest/periodosletivos"
# endpoint = "/rest/dadosacademico"

get(url_sigecad, endpoint)
# o segundo serve para fazer uma requisição com os
# cookies já setados
referer = "https://sigecad-academico.ufgd.edu.br/rest/periodosletivos"
req.setopt(req.HTTPHEADER, ["Referer: " + referer])
# req.setopt(req.HTTPHEADER, ["Accept: application/json"])
req.setopt(req.HTTPHEADER, ["Accept-Encoding: gzip"])
req.setopt(req.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
get(url_sigecad, endpoint)

body = buffer.getvalue()
with open("response.gz", "wb") as f:
    f.write(body)

# TODO: arranque apenas o gzip da resposta, esse é o
#       motivo pelo qual o script funcione as vezes apenas.

with gzip.open("response.gz", mode="rt") as f:
    try:
        file_content = f.read()
        print(file_content)

    except gzip.BadGzipFile:
        print("Erro!")

req.close()

remove("cookies.txt")
remove("response.gz")
