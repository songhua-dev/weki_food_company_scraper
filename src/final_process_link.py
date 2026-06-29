import pandas as pd
import time
import os
import requests
from bs4 import BeautifulSoup
import re
from src.utils_logger import log_message, print_data_summary

# File paths configuration
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'food_companies_with_sites.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'food_companies_with_sites_final.csv')


def get_possible_site(wiki_url, company_name):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(wiki_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        tokens = [t for t in re.findall(r'\w+', company_name.lower()) if len(t) > 2]
        content_div = soup.find('div', class_='mw-content-ltr')
        if not content_div: return None

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

                        if "official" in li_text or "website" in li_text:
                            return href

                        if any(t in li_text for t in tokens):
                            return href
        return None
    except Exception as e:
        log_message(f"Error fetching site for {company_name}: {e}")
        return None
    
def final_enrich():
    # Load the output file if it exists to resume progress, otherwise load the input
    target_file = OUTPUT_FILE if os.path.exists(OUTPUT_FILE) else INPUT_FILE
    
    if not os.path.exists(target_file):
        log_message("Error: No input file found.")
        return
        
    df = pd.read_csv(target_file)
    column_order = ['country', 'company', 'wiki_url', 'official_sites', 'possible_official_sites', 'status_note']
    for col in column_order:
        if col not in df.columns:
            df[col] = None
    df = df[column_order]

    # Initialize 'possible_official_sites' if it doesn't exist
    if 'possible_official_sites' not in df.columns:
        df['possible_official_sites'] = None
    
    # Identify companies needing enrichment
    # We use status_note to determine if the item has already been processed
    mask = (df['official_sites'].isna() | (df['official_sites'].astype(str).str.strip() == "")) & \
           (df['status_note'].isna() | (df['status_note'].astype(str).str.strip() == "")) & \
           df['wiki_url'].notna()
           
    missing_items = df[mask]
    total = len(missing_items)
    
    log_message(f"Starting final enrichment process for {total} companies...")
    
    success_count = 0
    # Process only the filtered rows
    for index, row in missing_items.iterrows():
        # Defensive check: skip if status_note is already populated
        if pd.notna(df.at[index, 'status_note']) and str(df.at[index, 'status_note']).strip() != "":
            continue 

        site = get_possible_site(row['wiki_url'], row['company'])
        
        if site:
            df.at[index, 'possible_official_sites'] = site
            df.at[index, 'status_note'] = 'Potential'
            success_count += 1
        else:
            df.at[index, 'status_note'] = 'Manual Check Required'
            
        time.sleep(2)
        
        # Save progress every 10 iterations
        if (index + 1) % 10 == 0:
            df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            log_message(f"Progress saved at index {index + 1}")
    
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    log_message(f"Final processing completed. Successfully identified: {success_count}/{total}.")
    log_message("="*50)
    return df

if __name__ == "__main__":
    df = final_enrich()
    if df is not None:
        print_data_summary(df, "Final Enrich Result")