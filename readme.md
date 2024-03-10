## kinguio

### Como utilizar

Crie um arquivo JSON, chamado `credentials.json` com o seguinte esquema:

```json
{
    "username": "seu_username",
    "password": "sua_senha"
}
```

Crie um ambiente virtual com python: `python -m venv env`.

Habilite o ambiente: `source env/bin/active`

Instale a biblioteca **requests**: `pip install requests`

Após a criação do arquivo com as credenciais e a instalação do pacote

requests, basta executar o script (`python main.py`) em instantes verá

no console um JSON com informações a respeito das disciplinas

feitas no semestre atual.
