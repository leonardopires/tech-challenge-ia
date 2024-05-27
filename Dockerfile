# Use a imagem base do Python
FROM python:3.9-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copie o arquivo de requisitos para o diretório de trabalho
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da aplicação para o diretório de trabalho
COPY . .

# Exponha a porta em que a aplicação será executada
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
