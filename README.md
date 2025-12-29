# 🏙️ BIM-O: Bot Imobiliário Open-Source (DSR Project)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)
![PostGIS](https://img.shields.io/badge/PostGIS-Geospatial-green.svg)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow.svg)

## 📋 Sobre o Projeto
O **BIM-O** é um sistema de monitoramento imobiliário autônomo desenvolvido seguindo a metodologia **Design Science Research (DSR)**. O objetivo é resolver a assimetria de informações no mercado imobiliário, capturando, estruturando e georreferenciando dados de grandes portais para análise de investimento.

## 🏗️ Arquitetura (Microsserviços)
O projeto opera em containers Docker orquestrados:
* **Orquestrador:** n8n (Gerencia fluxo e gatilhos).
* **Worker:** Python + Playwright + FastAPI (Extração de dados).
* **Database:** PostgreSQL + PostGIS (Armazenamento espacial).
* **Visualização:** Metabase & NocoDB.

## 🚀 Como Rodar

### 1. Clone o repositório
```bash
git clone [https://github.com/leoscastro/BIM-O.git](https://github.com/leoscastro/BIM-O.git)
cd BIM-O

### 2. Configure as Variáveis
Renomeie o arquivo de exemplo e edite com suas senhas:

Bash

cp .env.example .env
nano .env
### 3. Suba os Containers
Bash

docker compose up -d

## 🤝 Contribuição
Este é um projeto de aprendizado aberto. O foco atual está na Engenharia de Dados Geoespaciais. Pull Requests são bem-vindos!

## 📄 Licença
Distribuído sob a licença MIT.
