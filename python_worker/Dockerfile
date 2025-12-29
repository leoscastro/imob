# Usa a imagem oficial do Playwright (já tem os browsers e Python)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Define a pasta de trabalho
WORKDIR /app

# Copia a lista de bibliotecas e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala os navegadores do Playwright (garantia)
RUN playwright install chromium

# Copia o seu código para dentro do container
COPY ./app /app

# Comando para manter a API rodando (Ouvindo na porta 8000)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
