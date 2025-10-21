# Define a imagem base do Python
FROM python:3.11.13-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências para o diretório de trabalho
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para o diretório de trabalho
COPY . .

# Expõe a porta que o Streamlit usa
EXPOSE 8501

# Define o comando para iniciar a aplicação quando o container for executado
CMD ["streamlit", "run", "main.py"]