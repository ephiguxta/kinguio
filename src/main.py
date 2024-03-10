'''
Esse script serve para realizar as requisições no SIGECAD,
através delas podemos obter dados sem fazer o login pelo navegador,
basta inserir as credenciais no arquivo "credentials.json" e mudar
o endpoint
'''

import json
import re
import gzip
import sys
from io import BytesIO
from os import remove
import certifi
import pycurl

buffer = BytesIO()

URL_PRE_LOGIN = "https://login.app.ufgd.edu.br/login"
URL_POST_LOGIN = "https://ufgdnet.app.ufgd.edu.br"

URL_SIGECAD = "https://sigecad-academico.ufgd.edu.br"

USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
USERAGENT += " AppleWebKit/537.36 (KHTML, like Gecko)"
USERAGENT += " Chrome/121.0.6167.85 Safari/537.36"

credentials = []
# crie um arquivo json válido, com as suas
# credenciais de acesso.
# ex: { "username": "test", "password": "test" }
#
with open("credentials.json", encoding='utf-8') as f:
    credentials = json.load(f)

headers = {}
def header_func(header_line):
    '''
    Callback para as requisições, aqui tratamos os
    cabeçalhos e atribuímos numa lista
    '''

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
    '''
    Há um token quando inserimos um login e senha válida,
    esse token serve para fazer requisições após o login.
    Então utilizamos um regex para capturar esse token.
    '''

    ufgdnet = ''

    for element in set_cookie:
        pattern = r'(UFGDNET=)(((\w){40})-([0-9]{11}))'
        match = re.search(pattern, element, re.ASCII)

        if match is not None and len(match.group(2)) == 52:
            ufgdnet = match.group(2)
            break

    return ufgdnet

def get_cookies(response_set_cookie):
    '''
    Há dois cookies importantes quando se está fazendo
    requisições no sistema, o "___AT" e o "PLAY_SESION",
    esses cookies servem para requisições futuras após
    o login no sistema
    '''

    cookies = {}

    # passa pelos elementos do set_cookie procurando o play_session
    for element in response_set_cookie:
        match = re.search(r'(PLAY_SESSION=)((\w){40})', element, re.ASCII)

        if match is not None and len(match.group(2)) == 40:
            cookies['play_session'] = match.group(2)
            break

    if 'play_session' not in cookies:
        print("O PLAY_SESSION não foi obtido! Saindo...")
        sys.exit(1)

    # faz o mesmo que o loop acima mas procurando pelo authenticityToken,
    for element in response_set_cookie:
        match = re.search(r'(__AT=)((\w){40})', element, re.ASCII)

        if match is not None and len(match.group(2)) == 40:
            cookies['token'] = match.group(2)
            break

    if 'token' not in cookies:
        print("O authenticityToken não foi obtido! Saindo...")
        sys.exit(1)

    return cookies

def get(url, endpoint=""):
    '''
    Define os alguns parâmetros da requisição GET
    e "performa"
    '''

    req.setopt(req.URL, url + endpoint)
    req.setopt(req.HEADERFUNCTION, header_func)
    req.perform()
    # req.setopt(req.VERBOSE, True)

def post(url, response_cookies, user_credentials):
    '''
    Aqui fazemos um POST para realizar o login
    no sistema, os cookies que foram pegos
    anteriormente durante o GET são utilizados
    nessa função
    '''

    req.setopt(req.URL, url + "_form")

    req.setopt(req.HEADERFUNCTION, header_func)

    data_fmt = "authenticityToken=" + response_cookies['token']
    data_fmt += "&user.username=" + user_credentials['username']
    data_fmt += "&user.password=" + user_credentials['password']

    req.setopt(req.POSTFIELDS, data_fmt)
    # req.setopt(req.VERBOSE, True)

    req.perform()

req = pycurl.Curl()

req.setopt(req.USERAGENT, USERAGENT)
req.setopt(req.COOKIEFILE, 'cookies.txt')
req.setopt(req.COOKIEJAR, 'cookies.txt')
req.setopt(req.WRITEDATA, buffer)
req.setopt(req.CAINFO, certifi.where())

# get para pegar o authenticityToken e o play_session
get(URL_PRE_LOGIN)

body = buffer.getvalue()
cookies_pre_login = get_cookies(headers['set-cookie'])
if cookies_pre_login is None:
    print("O cookie não foi pego! Saindo...")
    sys.exit(1)

post(URL_PRE_LOGIN, cookies_pre_login, credentials)
body = buffer.getvalue()

ufgdnet_token = get_ufgdnet(headers['set-cookie'])

# GET para obter o json dos períodos letivos,
# ele é feito num endpoint /rest/...
# req.setopt(req.VERBOSE, True)
req.setopt(req.HTTPGET, 1)

ENDPOINT = "/rest/periodosletivos"
# endpoint = "/rest/dadosacademico"

get(URL_SIGECAD, ENDPOINT)
# o segundo serve para fazer uma requisição com os
# cookies já setados
REFERER = "https://sigecad-academico.ufgd.edu.br/rest/periodosletivos"
req.setopt(req.HTTPHEADER, ["Referer: " + REFERER])
# req.setopt(req.HTTPHEADER, ["Accept: application/json"])
req.setopt(req.HTTPHEADER, ["Accept-Encoding: gzip"])
req.setopt(req.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
get(URL_SIGECAD, ENDPOINT)

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
