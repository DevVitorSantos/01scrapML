import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import sqlite3  
import os
from dotenv import load_dotenv
import asyncio
from telegram import Bot
import psycopg2
from sqlalchemy import create_engine

load_dotenv()

# Configurações do bot do Telegram
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = Bot(token=TOKEN)

# Configurações do banco de dados PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_URL = os.getenv("POSTGRES_URL")


# Cria o engine do SQLAlchemy para o PostgreSQL
#DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(POSTGRES_URL)


def fetch_page():
    url = 'https://www.mercadolivre.com.br/iphone-17-pro-max-512gb-azul-profundo-distribuidor-autorizado/p/MLB1055308673#polycard_client=search-desktop&search_layout=grid&position=2&type=product&tracking_id=752673c0-eff0-4b81-ae9a-0d7677055491&wid=MLB5687348452&sid=search'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Erro ao buscar a página: {e}")
        return None

def parse_page(page_content):
    if not page_content:
        return None
        
    soup = BeautifulSoup(page_content, 'html.parser')
    
    title_tag = soup.find('h1', class_='ui-pdp-title')
    if not title_tag:
        print("Aviso: Título não encontrado. O site pode ter bloqueado o acesso ou o seletor mudou.")
        # Opcional: Salvar o HTML para debug
        # with open("debug.html", "w", encoding="utf-8") as f: f.write(page_content)
        return None

    product_name = title_tag.get_text(strip=True)
    
    precos = soup.find_all('span', class_='andes-money-amount__fraction')
    
    if len(precos) < 3:
        print(f"Aviso: Encontrado(s) apenas {len(precos)} preços. Esperávamos pelo menos 3.")
        # Tenta extrair o que for possível
        old_price = int(precos[0].get_text(strip=True).replace('.', '')) if len(precos) > 0 else 0
        new_price = int(precos[1].get_text(strip=True).replace('.', '')) if len(precos) > 1 else old_price
        installment_price = int(precos[2].get_text(strip=True).replace('.', '')) if len(precos) > 2 else 0
    else:
        old_price = int(precos[0].get_text(strip=True).replace('.', ''))
        new_price = int(precos[1].get_text(strip=True).replace('.', ''))
        installment_price = int(precos[2].get_text(strip=True).replace('.', ''))
        
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        'timestamp': timestamp,
        'product_name': product_name,
        'old_price': old_price,
        'new_price': new_price,
        'installment_price': installment_price
    }


def save_to_dataframe(product_info, df):
    new_row = pd.DataFrame([product_info])
    df = pd.concat([df, new_row], ignore_index=True)
    return df


## db connection

def create_connection():
    """Cria uma conexão com o banco de dados PostgreSQL."""
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    return conn

def setup_database(conn):
    #create table if not exists
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            timestamp TEXT,
            product_name TEXT,
            old_price INTEGER,
            new_price INTEGER,
            installment_price INTEGER
        )
    ''')
    conn.commit()

def save_to_database(product_info, table_name='products'):
    """Salva uma linha de dados no banco de dados PostgreSQL usando pandas e SQLAlchemy."""
    df = pd.DataFrame([product_info])
    # Usa SQLAlchemy para salvar os dados no PostgreSQL
    df.to_sql(table_name, engine, if_exists='append', index=False)

    
def get_max_price(conn):
    """Consulta o maior preço registrado até o momento com o timestamp correspondente."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT new_price, timestamp 
        FROM products 
        WHERE new_price = (SELECT MAX(new_price) FROM products);
    """)
    result = cursor.fetchone()
    cursor.close()
    if result and result[0] is not None:
        return result[0], result[1]
    return None, None

async def send_telegram_message(text):
    """Envia uma mensagem para o Telegram."""
    await bot.send_message(chat_id=CHAT_ID, text=text)

async def main():
     # Configuração do banco de dados
    conn = create_connection()
    setup_database(conn)
    
    
    try:
        while True:
            # Faz a requisição e parseia a página
            page_content = fetch_page()
            product_info = parse_page(page_content)
            current_price = product_info['new_price']

            

             # Obtém o maior preço já salvo
            max_price, max_price_timestamp = get_max_price(conn)

            

            # Comparação de preços
            if max_price is None or current_price > max_price:
                message = f"Novo preço maior detectado: {current_price}"
                print(message)
                await send_telegram_message(message)
                max_price = current_price
                max_price_timestamp = product_info['timestamp']
            else:
                message = f"O maior preço registrado é {max_price} em {max_price_timestamp}"
                print(message)
                await send_telegram_message(message)

            
            # Salva os dados no banco de dados PostgreSQL
            save_to_database(product_info)
            print("Dados salvos no banco:", product_info)
            
            # Aguarda 10 segundos antes da próxima execução
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("Parando a execução...")
    finally:
        conn.close()

asyncio.run(main())