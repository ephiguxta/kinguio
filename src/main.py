'''
Esse script serve para realizar as requisições no SIGECAD,
através delas podemos obter dados sem fazer o login pelo navegador,
basta inserir as credenciais no arquivo "credentials.json" e mudar
o endpoint
'''

import json
import re
import sys
import requests

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

    raw_cookie = response_set_cookie.get('PLAY_SESSION')

    match = re.search(r'((\w){40})', raw_cookie, re.ASCII)
    cookies['play_session'] = match.group(0)

    if 'play_session' not in cookies:
        print("o PLAY_SESSION não foi obtido! Saindo...")
        sys.exit(1)

    match = re.search(r'(__AT=)((\w){40})', raw_cookie, re.ASCII)
    cookies['token'] = match.group(2)

    if 'token' not in cookies:
        print("O authenticityToken não foi obtido! Saindo...")
        sys.exit(1)

    return cookies

def get(url, endpoint="", cookies=None):
    '''
    Define os alguns parâmetros da requisição GET
    e "performa"
    '''
    if cookies is not None:
        req = requests.get(url + endpoint, cookies=cookies)
    else:
        req = requests.get(url + endpoint)

    return req

def post(url, response_cookies, user_credentials):
    '''
    Aqui fazemos um POST para realizar o login
    no sistema, os cookies que foram pegos
    anteriormente durante o GET são utilizados
    nessa função
    '''

    cookies = response_cookies['play_session']
    cookies += "-___AT=" + response_cookies['token']
    cookies = {"PLAY_SESSION": cookies}

    payload = {
            'authenticityToken': response_cookies['token'],
            'user.username': user_credentials['username'],
            'user.password': user_credentials['password'],
            'service': 'https://sigecad-academico.ufgd.edu.br/'
    }

    post_response = requests.post(url + "_form", data=payload,
                                  cookies=cookies)

    return post_response

def semester_id(cookies):
    '''
    Pega todos os ID dos semestres já
    feitos pelo aluno
    '''
    ENDPOINT = "/rest/periodosletivos"

    response_get = get(URL_SIGECAD, ENDPOINT, cookies)
    response_json = response_get.json()

    id_list = []

    for element in response_json:
        id_list.append(element['id'])

    return id_list

def classes(semester_id, cookies):
    '''
    Pega o ID de todas as disciplinas que estão
    sendo feitas, ou foram feitas, naquele semester_id
    '''
    ENDPOINT = "/rest/turmas?periodoLetivoID=" + str(semester_id)
    response_get = get(URL_SIGECAD, ENDPOINT, cookies)

    return response_get


# get para pegar o authenticityToken e o play_session
response_get = get(URL_PRE_LOGIN)

cookies_pre_login = get_cookies(response_get.cookies)
if cookies_pre_login is None:
    print("O cookie não foi pego! Saindo...")
    sys.exit(1)

# os cookies que serão utilizados para "navegar" no
# sistema, serão pegos após esse POST com credenciais válidas.
response_post = post(URL_PRE_LOGIN, cookies_pre_login, credentials)

cookies = response_post.cookies.values()
cookies = {
        "UFGDNET": cookies[0],
        "PLAY_ACADEMICO_SESSION": cookies[1]
}

# um exemplo só pra pegar as disciplinas do último
# semestre feito pelo aluno.
semester_id_list = semester_id(cookies)
last_semester_id = semester_id_list[0]

id_list = semester_id(cookies)

classes_list = classes(id_list[0], cookies)
print(classes_list.json())
