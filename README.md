# Scraping Mercado Livre 🚀

Este projeto é um web scraper simples desenvolvido em Python para monitorar preços de produtos no Mercado Livre em tempo real.

## 📋 Sobre o Projeto

O script acessa periodicamente a página de um produto específico (atualmente configurado para um iPhone no Mercado Livre), extrai informações relevantes como nome do produto e preços (original, com desconto e parcelado) e exibe os dados no console com um timestamp.

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **Requests**: Para realizar as requisições HTTP.
- **BeautifulSoup4**: Para o parsing e extração de dados do HTML.
- **Time**: Para gerenciar o intervalo entre as capturas.

## 🚀 Como Executar

### 1. Clonar o repositório
```bash
git clone <url-do-repositorio>
cd 01scrapML
```

### 2. Configurar o ambiente virtual
```bash
python -m venv .venv

# No Windows:
.\.venv\Scripts\activate

# No Linux/Mac:
source .venv/bin/activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Rodar o script
```bash
python app.py
```

## 🔍 Funcionalidades

- Captura automatizada a cada 60 segundos.
- Extração de:
  - Nome do produto.
  - Preço original.
  - Preço atual (com desconto).
  - Preço das parcelas.
- Logs formatados no console com data e hora.

## ⚠️ Observação
Este projeto foi desenvolvido para fins educacionais de Engenharia de Dados. O uso de scrapers deve respeitar os termos de serviço das plataformas.
