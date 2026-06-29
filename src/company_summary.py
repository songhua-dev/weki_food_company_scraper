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
FILE_LINKED = os.path.join(DATA_DIR, 'food_companies_with_sites_final.csv')
FILE_FINAL = os.path.join(DATA_DIR, 'food_companies_with_summary.csv')


def fetch_company_summary(wiki_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(wiki_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        content_div = soup.find('div', class_='mw-content-ltr')
        if not content_div: return "No summary found"

        summaries = []
        count = 0
        for element in content_div.children:
            if element.name == 'div' and 'mw-heading2' in element.get('class', []): break
            if element.name == 'p':
                text = element.get_text().strip()
                text = re.sub(r'\[.*?\]', '', text)
                if text:
                    summaries.append(text)
                    count += 1
            if count >= 2: break
        
        final_text = " ".join(summaries)
        final_text = re.sub(r'\s+', ' ', final_text).strip()
        return final_text[:300] + "..." if len(final_text) > 300 else (final_text if final_text else "No summary found")
    except Exception as e:
        return f"Error: {e}"

def process_and_add_summary(input_csv=FILE_LINKED, output_csv=FILE_FINAL):
    log_message(f"Starting process: Loading data from {input_csv}...")
    
    if not os.path.exists(input_csv):
        log_message(f"Error: Input file not found at {input_csv}")
        return
    
    df = pd.read_csv(input_csv)
    
    if 'status_note' not in df.columns:
        log_message("Error: 'status_note' column not found.")
        return

    # Ensure company_summary column exists, initialize if not
    if 'company_summary' not in df.columns:
        df['company_summary'] = None

    total = len(df)
    success_count = 0
    
    for index, row in df.iterrows():
        # Skip if summary already exists
        if pd.notna(df.at[index, 'company_summary']) and df.at[index, 'company_summary'] != "No summary found":
            continue
            
        summary = fetch_company_summary(row['wiki_url'])
        df.at[index, 'company_summary'] = summary
        
        if summary != "No summary found" and not summary.startswith("Error"):
            success_count += 1
        
        time.sleep(1) # Delay to avoid rate limiting
        
        # Save progress every 10 iterations
        if (index + 1) % 10 == 0:
            df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            log_message(f"Progress saved at index {index + 1}")
    
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    log_message(f"Process complete. Successfully fetched: {success_count}/{total}.")
    log_message(f"Results saved to {output_csv}")
    log_message("="*50)
    return df


if __name__ == "__main__":
    df = process_and_add_summary(FILE_LINKED, FILE_FINAL)
    if df is not None:
        log_loading(df, "Company Summary Result")