## Como funciona:

### 1. Obtendo um token JWT:

- Abra o endpoint `[POST] /api/auth`

- Clique no botão `Try it out`

- Edite o JSON para colocar seu usuário e senha
    ```json
    {
      "username": "zorzi",
      "password": "biguxo"
    }
    ```

- Clique no botão `Execute`
  - Você verá uma resposta como essa na parte com o nome `Response body`, numa região com subtítulo `Server response`:
    ```json
    {
      "access_token": "SEU_TOKEN"
    }
    ```

- Selecione o valor do `access_token` e copie. 
  - No caso, o valor seria: `SEU_TOKEN`

### 2. Usando o token de autenticação:

- Volte ao topo da página e clique em `Authorize`
- No campo que vai aparecer, digite: `Bearer SEU_TOKEN`
- Clique no botão `Authorize`
- Clique no botão `Close`

### 3. Testando seu token

- Vá no endpoint `[GET] /api/auth/profile`
- Clique em `Try it out`
- Clique em `Execute`
- Veja o resultado:

    - Você verá uma resposta como essa na parte com o nome `Response body`, numa região com subtítulo `Server response`:
    ```json
    {
      "user": "zorzi"
    }
    ```

### 4. Fazendo chamadas na API
Para fazer outras chamadas na API, siga o mesmo princípio. Depois de autenticar, vá na seção do endpoint desejado, 
clique em `Try it out`, edite os parâmetros de entrada, e clique em `Execute`.
O resultado aparecerá na região com o subtítulo `Server response`. 
