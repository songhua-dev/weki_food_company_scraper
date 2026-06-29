import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import time
from utils_logger import log_message, print_data_summary

# File path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, 'food_companies_with_infobox.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'food_companies_final.csv')

EMPLOYEES_KEYS = ['Employees', 'employees', 'Number of employees', 'Staff']
REVENUE_KEYS = ['Revenue', 'revenue']
MAX_RETRIES = 2

def clean_value(text):
    text = re.sub(r'\[.*?\]', '', text).strip()
    return text if len(text) >= 3 else None

def count_none_fields(row):
    fields = ['employees', 'revenue']
    return sum(1 for f in fields if pd.isna(row.get(f)) or str(row.get(f)).strip() in ('', 'None'))

def fetch_numeric_data(wiki_url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(wiki_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            infobox = soup.find('table', class_='infobox')
            if not infobox:
                return None, None

            employees = None
            revenue = None

            for row in infobox.find_all('tr'):
                header = row.find('th')
                data = row.find('td')
                if not header or not data:
                    continue

                key = header.get_text(strip=True)
                value = data.get_text(separator=' ', strip=True)

                if key in EMPLOYEES_KEYS and employees is None:
                    employees = clean_value(value)

                if key in REVENUE_KEYS and revenue is None:
                    revenue = clean_value(value)

            return employees, revenue

        except Exception as e:
            log_message(f"Attempt {attempt}/{MAX_RETRIES} failed for {wiki_url}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)

    return None, None

def process_and_add_numeric(input_csv=INPUT_FILE, output_csv=OUTPUT_FILE):
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
        df['employees'] = None
        df['revenue'] = None
    else:
        log_message("Error: Input file not found.")
        return

    total = len(df)
    success_count = 0

    for index, row in df.iterrows():
        if count_none_fields(row) < 2:
            continue

        employees, revenue = fetch_numeric_data(row['wiki_url'])

        df.at[index, 'employees'] = employees
        df.at[index, 'revenue'] = revenue

        if any([employees, revenue]):
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
    df = process_and_add_numeric()
    if df is not None:
        print_data_summary(df, "Add Numeric Result")