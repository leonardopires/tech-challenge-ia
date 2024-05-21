from typing import MutableMapping

import requests
from flask import Flask, jsonify, request, Response
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pandas as pd
from io import StringIO

from pandas.errors import ParserError

app = Flask(__name__)
api = Api(app)

# Configure a chave secreta JWT
app.config['JWT_SECRET_KEY'] = 'sua-chave-secreta-aqui'

# Inicialize o gerenciador JWT
jwt = JWTManager(app)


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {"message": self.message, "status_code": self.status_code}


class APIResponse:
    def __init__(self, data: object, status_code: int = 200):
        self.data = data
        self.status_code = status_code

    def to_dict(self):
        return {"status_code": self.status_code, "data": self.data}

    @classmethod
    def empty(cls):
        return cls("OK", 200)

    @classmethod
    def not_found(cls):
        return cls("Não encontrado", 404)

    @classmethod
    def wrap_error(cls, error: BaseException, status_code: int = 400):
        return cls(error.__dict__, status_code)


class CSVDownloaderResource(Resource):
    def __init__(self):
        self.sitemap: dict = {
            "processamento": {
                "viniferas": {"resource": "ProcessaViniferas", "delimiter": "\t"},
                "americanasehibridas": {"resource": "ProcessaAmericanas", "delimiter": "\t"},
                "americanas": {"resource": "ProcessaAmericanas", "delimiter": "\t"},
                "hibridas": {"resource": "ProcessaAmericanas", "delimiter": "\t"},
                "uvasdemesa": {"resource": "ProcessaMesa", "delimiter": "\t"},
                "mesa": {"resource": "ProcessaMesa", "delimiter": "\t"},
                "semclassificacao": {"resource": "ProcessaSemclass", "delimiter": "\t"},
                "index": {"resource": "ProcessaSemclass", "delimiter": "\t"},
            },
            "comercializacao": {
                "index": {"resource": "Comercio", "delimiter": ";"},
            },
            "importacao": {
                "vinhosdemesa": {"resource": "ImpVinhos", "delimiter": ";"},
                "vinhos": {"resource": "ImpVinhos", "delimiter": ";"},
                "espumantes": {"resource": "ImpEspumantes", "delimiter": ";"},
                "uvasfrescas": {"resource": "ImpFrescas", "delimiter": ";"},
                "uvas": {"resource": "ImpFrescas", "delimiter": ";"},
                "frescas": {"resource": "ImpFrescas", "delimiter": ";"},
                "uvaspassas": {"resource": "ImpPassas", "delimiter": ";"},
                "passas": {"resource": "ImpPassas", "delimiter": ";"},
                "sucodeuva": {"resource": "ImpSuco", "delimiter": ";"},
                "suco": {"resource": "ImpSuco", "delimiter": ";"},
            },
            "exportacao": {
                "vinhosdemesa": {"resource": "ExpVinho", "delimiter": ";"},
                "vinhos": {"resource": "ExpVinho", "delimiter": ";"},
                "espumantes": {"resource": "ExpEspumantes", "delimiter": ";"},
                "uvasfrescas": {"resource": "ExpUva", "delimiter": ";"},
                "uvas": {"resource": "ExpUva", "delimiter": ";"},
                "frescas": {"resource": "ExpUva", "delimiter": ";"},
                "sucodeuva": {"resource": "ExpSuco", "delimiter": ";"},
                "suco": {"resource": "ExpSuco", "delimiter": ";"},
            }
        }

        self.base_url = "http://vitibrasil.cnpuv.embrapa.br/download"

    def process_csv(self, url: str, delimiter: str = ';') -> list[MutableMapping]:
        response = requests.get(url)
        if response.status_code != 200:
            raise APIError("Não foi possível obter os dados", response.status_code)

        response_data = response.content.decode('utf-8')
        print(f"Resposta recebida: \n{response_data}")
        csv_data = StringIO(response_data)
        df = pd.read_csv(csv_data, delimiter=delimiter)
        return df.to_dict(orient='records')

    def get(self, action: str, type: str = "index") -> tuple[dict, int]:
        result = APIResponse.empty()

        if action not in self.sitemap:
            result = APIResponse.not_found()

        if type not in self.sitemap[action]:
            result = APIResponse.not_found()

        try:
            item = self.sitemap[action][type]
            resource = item['resource']
            delimiter = item['delimiter'] or ";"
            processed_csv = self.process_csv(f"{self.base_url}/{resource}.csv", delimiter)
            result = APIResponse(processed_csv)
        except ParserError as parserError:
            result = APIResponse.wrap_error(parserError, 400)
        except APIError as apiEx:
            result = APIResponse.wrap_error(apiEx, apiEx.status_code)
        except BaseException as ex:
            result = APIResponse.wrap_error(ex)

        return result.to_dict(), result.status_code


# Adicionando recursos à API
api.add_resource(
    CSVDownloaderResource,
    '/<string:action>/<string:type>',
    '/<string:action>/<string:type>/',
    '/<string:action>',
    '/<string:action>/')


# Endpoint para login
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if username != 'zorzi' or password != 'biguxo':
        return jsonify({"msg": "Usuário ou Senha inválidos"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)


# Endpoint protegido
@app.route('/protegido', methods=['GET'])
@jwt_required()
def protegido():
    current_user = get_jwt_identity()
    return jsonify(logado_como=current_user), 200


# Página inicial
@app.route('/')
def home():
    return "Fragile Consulting! Wearing the Shirt!"


if __name__ == '__main__':
    app.run(debug=True)
