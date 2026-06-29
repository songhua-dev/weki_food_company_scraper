import pandas as pd
import time
import os
import requests
from bs4 import BeautifulSoup
import re
from src.utils_logger import log_message, log_loading

# File paths configuration
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'food_companies.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'food_companies_with_sites.csv')


def fetch_official_website(wiki_url, company_name):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(wiki_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        target_name = company_name.lower().strip()
        clean_name = re.sub(r'\(.*?\)', '', target_name).strip()
        name_tokens = [t for t in re.findall(r'\w+', clean_name) if len(t) > 2]

        content_div = soup.find('div', class_='mw-content-ltr')
        if not content_div: return None, None

        headings = content_div.find_all(class_='mw-heading2')
        for i, heading in enumerate(headings):
            next_heading = headings[i + 1] if i + 1 < len(headings) else None
            for sibling in heading.find_next_siblings():
                if sibling == next_heading: break
                targets = [sibling] if sibling.name == 'ul' else sibling.find_all('ul')
                for ul in targets:
                    for li in ul.find_all('li', recursive=False):
                        li_text = li.get_text().lower()
                        a = li.find('a', href=True)
                        if not a: continue
                        href = a['href']
                        if not href.startswith('http'): continue
                        is_match = any(token in li_text for token in name_tokens) and "website" in li_text
                        if "official website" in li_text or is_match:
                            return href, "Confirmed"
        return None, None
    except Exception as e:
        log_message(f"Error parsing {wiki_url}: {e}")
        return None, None

def process_links():
    if os.path.exists(OUTPUT_FILE):
        log_message(f"Loading existing progress: {OUTPUT_FILE}")
        df = pd.read_csv(OUTPUT_FILE)
        pending = df[df['official_sites'].isna() | (df['official_sites'].astype(str).str.strip() == "")]
        if pending.empty:
            log_message(f"Output file already complete ({len(df)} rows). Skipping crawl.")
            return
        else:
            log_message(f"Resuming: {len(pending)} rows still pending.")
    elif os.path.exists(INPUT_FILE):
        log_message(f"Loading raw data: {INPUT_FILE}")
        df = pd.read_csv(INPUT_FILE)
        df['official_sites'] = None
    else:
        log_message("Error: Input file not found.")
        return

    if 'status_note' not in df.columns: df['status_note'] = None

    log_message(f"Starting crawl for {len(df)} companies...")
    
    success_count = 0
    total = len(df)
    
    for index, row in df.iterrows():
        if pd.notna(row.get('official_sites')) and str(row['official_sites']).strip() != "":
            continue
            
        url, status = fetch_official_website(row['wiki_url'], row['company'])
        
        if url:
            df.at[index, 'official_sites'] = url
            df.at[index, 'status_note'] = status
            success_count += 1
            
        time.sleep(1.5)
        
        if (index + 1) % 20 == 0:
            df.to_csv(OUTPUT_FILE, index=False)
            log_message(f"Progress saved at index {index + 1}")

    df.to_csv(OUTPUT_FILE, index=False)
    log_message(f"Process complete. Successfully fetched: {success_count}/{total}.")
    log_message("="*50)
    return df

if __name__ == "__main__":
    df = process_links() 
    if df is not None:
        log_loading("Process Link Result Complete.")