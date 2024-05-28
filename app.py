import io
import os
from typing import MutableMapping

import requests
from flask import Flask, request
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_restx import Resource, Api, fields, Namespace
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, verify_jwt_in_request
import pandas as pd
from io import StringIO

from pandas.errors import ParserError

from config.sitemap import SITEMAP
from framework.web.APIError import APIError
from framework.web.APIResponse import APIResponse

authorizations = {
    'jwt': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Digite na caixa *'Value'*: **'Bearer &lt;JWT&gt;'**, onde JWT é o token que você recebe chamando o método /api/auth",
    }
}

path = os.path.dirname(os.path.realpath(__file__))
readme = io.open(f"{path}/doc/README.md", encoding="utf-8").read()

app = Flask(__name__)
api = Api(app, version='1.0', title='API de dados de produção vitivinícola.',
          description=f'Baixa e processa os dados direto do site da Embrapa.\n{readme}',
          security="jwt", authorizations=authorizations, lang="pt-BR", )

ns = Namespace('api', description='API com as operações de extração dos dados do site da Embrapa.')

api.add_namespace(ns)

# Configure a chave secreta JWT
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "sua-chave-secreta-aqui")
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'

# Inicialize o gerenciador JWT
jwt = JWTManager(app)

# Definindo modelos de dados para a documentação do Swagger
login_model = ns.model('Login', {
    'username': fields.String(required=True, description='Nome de usuário'),
    'password': fields.String(required=True, description='Senha do usuário')
})

token_model = ns.model('Token', {
    'access_token': fields.String(description='Token JWT de acesso')
})


# Endpoint para login
@ns.route('/auth')
class AuthResource(Resource):
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
            return {"message": "Usuário ou Senha inválidos"}, 401

        access_token = create_access_token(identity=username)
        return {'access_token': access_token}, 200

@ns.route('/auth/profile')
class ProfileResource(Resource):
    @ns.response(200, 'Success', fields.Raw)
    @ns.response(403, 'Forbidden')
    @ns.response(401, 'Unauthorized')
    @ns.expect(ns.header('Authorization', 'Token JWT', required=True))
    def get(self):
        """
        Endpoint protegido que retorna a identidade do usuário autenticado.
        """
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            return {'user': current_user}, 200
        except NoAuthorizationError as ex:
            return APIResponse.wrap_error(ex, 401).to_dict(), 401

def get_types(sitemap):
    result = list()
    for first_level_key in sitemap:
        result.append(f" - {first_level_key}")
        items = list(sitemap[first_level_key])
        items.sort()
        for second_level_key in items:
            if second_level_key == 'index':
                second_level_key = f"{second_level_key} (ou valor vazio)"
            result.append(f"\t* {second_level_key}")
    return result


def get_actions(sitemap):
    result = set()
    for first_level_key in sitemap:
        result.add(f" - {first_level_key}")

    result_list = list(result)
    result_list.sort()
    return result


def get_unique_types(sitemap):
    result = set()
    for first_level_key in sitemap:
        for second_level_key in sitemap[first_level_key]:
            result.add(second_level_key)
    result_list = list(result)
    result_list.sort()
    return result_list


actions = '\n'.join(get_actions(SITEMAP))
types = '\n'.join(get_types(SITEMAP))


@ns.route('/embrapa/<string:action>/<string:type>')
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
        'action': {'description': f"Tipo de dado a ser retornado:", 'enum': list(SITEMAP.keys()), 'required': True},
        'type': {'description': f'O tipo de produto analisado (varia de acordo com o tipo de ação): \n{types}',
                 'enum': get_unique_types(SITEMAP), 'required': True}
    })
    @ns.response(200, 'Success', [fields.Raw])
    @ns.response(404, 'Not Found')
    @ns.response(500, 'Internal Server Error')
    @ns.response(403, 'Forbidden')
    @ns.response(401, 'Unauthorized')
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
                verify_jwt_in_request()
                item = self.sitemap[action][type]
                resource = item['resource']
                delimiter = item['delimiter'] or ";"
                processed_csv = self.process_csv(f"{self.base_url}/{resource}.csv", delimiter)
                result = APIResponse(processed_csv)
            except ParserError as parserError:
                result = APIResponse.wrap_error(parserError, 400)
            except NoAuthorizationError as authEx:
                result = APIResponse.wrap_error(authEx, 401)
            except APIError as apiEx:
                result = APIResponse.wrap_error(apiEx, apiEx.status_code)
            except BaseException as ex:
                result = APIResponse.wrap_error(ex)

        return result.to_dict(), result.status_code


@app.errorhandler(500)
def on_error(error):
    return {"status_code": 500, "message": "Erro Interno", "error": str(error)}, 500


@app.errorhandler(NoAuthorizationError)
def unauthorized(error):
    return {"status_code": 401, "message": "Cabeçalho de autorização ausente", "error": str(error)}, 401


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
