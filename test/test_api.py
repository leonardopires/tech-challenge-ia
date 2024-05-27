import unittest
import requests

BASE_URL = "http://localhost"


class TestAPIEmbrapa(unittest.TestCase):

    def setUp(self):
        self.base_url = BASE_URL
        self.login_url = f"{self.base_url}/api/login"
        self.protegido_url = f"{self.base_url}/api/protegido"
        self.endpoints = {
            "processamento": ["viniferas", "americanasehibridas", "americanas", "hibridas", "uvasdemesa", "mesa",
                              "semclassificacao"],
            "comercializacao": ["todos"],
            "importacao": ["vinhosdemesa", "vinhos", "espumantes", "uvasfrescas", "uvas", "frescas", "uvaspassas",
                           "passas", "sucodeuva", "suco"],
            "exportacao": ["vinhosdemesa", "vinhos", "espumantes", "uvasfrescas", "uvas", "frescas", "sucodeuva",
                           "suco"]
        }
        self.username = "zorzi"
        self.password = "biguxo"

    def test_login(self):
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = requests.post(self.login_url, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.access_token = response.json()["access_token"]

    def test_protegido_without_token(self):
        response = requests.get(self.protegido_url)
        self.assertEqual(response.status_code, 401)

    def test_protegido_with_token(self):
        self.test_login()
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(self.protegido_url, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("logado_como", response.json())
        self.assertEqual(response.json()["logado_como"], self.username)

    def test_get_csv_downloader_resource(self):
        for action, types in self.endpoints.items():
            for type_ in types:
                with self.subTest(action=action, type_=type_):
                    url = f"{self.base_url}/api/embrapa/{action}/{type_}"
                    print(f"Chamando URL: {url}")
                    response = requests.get(url)
                    status_code = response.status_code

                    print(f"Resposta: {url} ({status_code})")
                    if status_code == 200:
                        self.assertIsInstance(response.json()["data"], list)
                    else:
                        self.assertIn(status_code, [404, 500])


if __name__ == '__main__':
    unittest.main()
