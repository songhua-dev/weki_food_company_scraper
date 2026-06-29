import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import time
from src.utils_logger import log_message, log_loading

# File path configuration
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'food_companies_with_summary.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'food_companies_with_infobox.csv')

FOUNDED_KEYS = ['Founded', 'founded', 'Founded year', 'Foundation', 'formation', 'Formed']
HQ_KEYS = ['Headquarters', 'headquarters', 'Location', 'location']
PRODUCTS_KEYS = ['Products', 'products', 'Product', 'product']
MAX_RETRIES = 2


def extract_year(text):
    match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', text)
    return int(match.group()) if match else None

def clean_headquarters(text):
    parts = [p.strip() for p in text.split(',') if p.strip()]
    return ', '.join(parts[-4:]) if parts else None

def count_none_fields(row):
    fields = ['founded_year', 'headquarters', 'products']
    return sum(1 for f in fields if pd.isna(row.get(f)) or str(row.get(f)).strip() in ('', 'None'))

def fetch_infobox_data(wiki_url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(wiki_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            infobox = soup.find('table', class_='infobox')
            if not infobox:
                return None, None, None

            founded_year = None
            headquarters = None
            products = None

            for row in infobox.find_all('tr'):
                header = row.find('th')
                data = row.find('td')
                if not header or not data:
                    continue

                key = header.get_text(strip=True)
                value = data.get_text(separator=', ', strip=True)
                value = re.sub(r'\[.*?\]', '', value).strip()

                if key in FOUNDED_KEYS and founded_year is None:
                    founded_year = extract_year(value)

                if key in HQ_KEYS and headquarters is None:
                    headquarters = clean_headquarters(value)

                if key in PRODUCTS_KEYS and products is None:
                    products = value

            return founded_year, headquarters, products

        except Exception as e:
            log_message(f"Attempt {attempt}/{MAX_RETRIES} failed for {wiki_url}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)

    return None, None, None

def process_and_add_infobox(input_csv=INPUT_FILE, output_csv=OUTPUT_FILE):
    if os.path.exists(output_csv):
        log_message(f"Loading existing progress: {output_csv}")
        df = pd.read_csv(output_csv)
        pending = df[df.apply(lambda r: count_none_fields(r) >= 2, axis=1)]
        if pending.empty:
            log_message(f"Output file already complete ({len(df)} rows). Skipping.")
            return
        log_message(f"Resuming: {len(pending)} rows still pending.")
    elif os.path.exists(input_csv):
        log_message(f"Loading data: {input_csv}")
        df = pd.read_csv(input_csv)
        df['founded_year'] = None
        df['headquarters'] = None
        df['products'] = None
    else:
        log_message("Error: Input file not found.")
        return

    total = len(df)
    success_count = 0

    for index, row in df.iterrows():
        if count_none_fields(row) < 2:
            continue

        founded_year, headquarters, products = fetch_infobox_data(row['wiki_url'])

        df.at[index, 'founded_year'] = founded_year if founded_year is not None else 'N/A'
        df.at[index, 'headquarters'] = headquarters if headquarters is not None else 'N/A'
        df.at[index, 'products'] = products if products is not None else 'N/A'

        if any([founded_year, headquarters, products]):
            success_count += 1

        time.sleep(1.5)

        if (index + 1) % 20 == 0:
            df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            log_message(f"Progress saved at index {index + 1}")

    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    log_message(f"Process complete. At least 1 field fetched: {success_count}/{total}.")
    log_message("="*50)
    return df

if __name__ == "__main__":
    df = process_and_add_infobox()
    if df is not None:
        log_loading(df, "Add Infobox Result")