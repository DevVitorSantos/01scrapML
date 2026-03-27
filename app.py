import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import sqlite3  
import os
from dotenv import load_dotenv
import asyncio
from telegram import Bot

load_dotenv()

# Configurações do bot do Telegram
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = Bot(token=TOKEN)


def fetch_page():
    url = 'https://www.mercadolivre.com.br/iphone-17-pro-max-512gb-azul-profundo-distribuidor-autorizado/p/MLB1055308673#polycard_client=search-desktop&search_layout=grid&position=2&type=product&tracking_id=752673c0-eff0-4b81-ae9a-0d7677055491&wid=MLB5687348452&sid=search'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers).text
    
    return response

def parse_page(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    
    
    title = soup.find('h1', class_='ui-pdp-title')
    product_name = title.get_text(strip=True)
    precos = soup.find_all('span', class_='andes-money-amount__fraction')
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

def create_connection(db_name='products.db'):
    conn = sqlite3.connect(db_name)
    return conn

def setup_database(conn):
    #create table if not exists
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            product_name TEXT,
            old_price INTEGER,
            new_price INTEGER,
            installment_price INTEGER
        )
    ''')
    conn.commit()

def save_to_database(product_info, conn):
    new_row = pd.DataFrame([product_info])
    new_row.to_sql('products', conn, if_exists='append', index=False)

    
def get_max_price(conn):
    """Consulta o maior preço registrado até o momento."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(new_price), timestamp FROM products")
    result = cursor.fetchone()
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
            if max_price < current_price:
            
                message = f"Preço maior detectado é novo: {current_price} em {max_price_timestamp}"
                print(message)
                await send_telegram_message(message)

            else:
            
                message = f"O maior preço registrado é antigo {max_price} em {max_price_timestamp}"
                print(message)
                await send_telegram_message(message)

            
            # salva geral no banco de dados sqlite

            save_to_database(product_info, conn)
            print("Dados salvos no banco:", product_info)
            
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("Parando a execução...")
    finally:
        conn.close()

asyncio.run(main())