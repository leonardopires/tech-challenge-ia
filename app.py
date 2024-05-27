import os
from typing import MutableMapping

import requests
from flask import Flask, jsonify, request
from flask_restx import Resource, Api, fields, Namespace
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, exceptions
import pandas as pd
from io import StringIO

from pandas.errors import ParserError

app = Flask(__name__)
api = Api(app, version='1.0', title='API de dados de produção vitivinícola.',
          description='Baixa e processa os dados direto do site da Embrapa.')
ns = Namespace('api', description='API com as operações de extração dos dados do site da Embrapa.')
api.add_namespace(ns)

# Configure a chave secreta JWT
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "sua-chave-secreta-aqui")


@app.errorhandler(exceptions.NoAuthorizationError)
def unauthorized(error):
    return jsonify({"status_code": 403, "message": "Acesso negado", "error": error.__dict__}), 403


@app.errorhandler(500)
def on_error(error):
    return jsonify({"status_code": 500, "message": "Erro Interno", "error": error.__dict__}), 500


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
        return cls(str(error), status_code)


SITEMAP: dict = {
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


def get_types(sitemap):
    second_level_keys = set()
    for first_level_key in sitemap:
        for second_level_key in sitemap[first_level_key]:
            second_level_keys.add(second_level_key)
    return list(second_level_keys)


actions = ', '.join(SITEMAP.keys())
types = ', '.join(get_types(SITEMAP))


class CSVDownloaderResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sitemap: dict = SITEMAP

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

    @ns.doc(params={
        'action': {'description': f"Tipo de ação ({actions})", 'type': 'string', 'required': True},
        'type': {'description': f'O tipo de produto analisado ({types})', 'type': 'string', 'required': False,
                 'default': 'index'}
    })
    @ns.response(200, 'Success', [fields.Raw])
    @ns.response(404, 'Not Found')
    @ns.response(500, 'Internal Server Error')
    def get(self, action: str, type: str = "index") -> tuple[dict, int]:
        """
        Baixa e processa os dados CSV para a ação e o tipo especificados.
        """
        result = APIResponse.empty()

        if action not in self.sitemap:
            result = APIResponse.not_found()
        elif type not in self.sitemap[action]:
            result = APIResponse.not_found()
        else:
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
ns.add_resource(
    CSVDownloaderResource,
    '/<string:action>/<string:type>',
    '/<string:action>')

# Definindo modelos de dados para a documentação do Swagger
login_model = ns.model('Login', {
    'username': fields.String(required=True, description='Nome de usuário'),
    'password': fields.String(required=True, description='Senha do usuário')
})

token_model = ns.model('Token', {
    'access_token': fields.String(description='Token JWT de acesso')
})


# Endpoint para login
@ns.route('/login')
class Login(Resource):
    @ns.expect(login_model)
    @ns.response(200, 'Success', token_model)
    @ns.response(401, 'Unauthorized')
    def post(self):
        """
        Autentica o usuário e retorna um token JWT.
        """
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if username != 'zorzi' or password != 'biguxo':
            return jsonify({"msg": "Usuário ou Senha inválidos"}), 401

        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)


# Endpoint protegido
@ns.route('/protegido')
class Protegido(Resource):
    @jwt_required()
    @ns.response(200, 'Success', fields.Raw)
    @ns.response(403, 'Forbidden')
    def get(self):
        """
        Endpoint protegido que retorna a identidade do usuário autenticado.
        """
        current_user = get_jwt_identity()
        return jsonify(logado_como=current_user), 200


# Página inicial
@app.route('/')
def home():
    return "Fragile Consulting! Wearing the Shirt!"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
