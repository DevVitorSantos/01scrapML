import requests
from bs4 import BeautifulSoup
import time

def fetch_page(url):
    
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

    return {
        'timestamp': time.ctime(time.time()),
        'product_name': product_name,
        'old_price': old_price,
        'new_price': new_price,
        'installment_price': installment_price
    }
if __name__ == "__main__":
    while True:
        url = 'https://www.mercadolivre.com.br/iphone-17-pro-max-512gb-azul-profundo-distribuidor-autorizado/p/MLB1055308673#polycard_client=search-desktop&search_layout=grid&position=2&type=product&tracking_id=752673c0-eff0-4b81-ae9a-0d7677055491&wid=MLB5687348452&sid=search'
        page_content = fetch_page(url)
        product_info = parse_page(page_content)
        print(product_info)
        time.sleep(60)
    
