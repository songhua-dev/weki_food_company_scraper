import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
from src.utils_logger import log_message, log_loading

# File path configuration
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'food_companies.csv')



def fetch_food_companies():
    """
    Scrapes the Wikipedia list of food companies and returns a DataFrame.
    """
    url = "https://en.wikipedia.org/wiki/List_of_food_companies"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    log_message("Starting scrape process from Wikipedia...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        log_message(f"Network request failed: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    all_elements = soup.find_all(['h2', 'ul', 'div'])
    
    companies = []
    seen = set()
    current_country = None
    nav_noise = {"Contents", "References", "See also", "External links", "Notes", "Further reading"}

    for element in all_elements:
        if element.name == "h2":
            text = element.get_text(strip=True).replace("[edit]", "")
            if text in nav_noise:
                current_country = None
                continue
            if text not in nav_noise and not any(char.isdigit() for char in text):
                current_country = text
            continue
            
        elif current_country and (element.name == "ul" or (element.name == "div" and "div-col" in element.get("class", []))):
            if element.find_parent(class_=['navbox', 'catlinks', 'sidebar', 'mw-footer']):
                continue
            
            uls = element.find_all("ul") if element.name == "div" else [element]
            for ul in uls:
                for li in ul.find_all("li", recursive=False):
                    link = li.find("a")
                    raw_text = li.get_text(strip=True)
                    
                    match = re.match(r'^(.*?)\s*\((.*)\)$', raw_text)
                    if match:
                        company_name = match.group(1).strip()
                        remark = match.group(2).strip()
                        final_name = f"{company_name} ({remark})"
                    else:
                        final_name = raw_text
                    
                    wiki_url = f"https://en.wikipedia.org{link.get('href')}" if link else "N/A"
                    is_valid = link and not ("/wiki/List_of" in link.get("href", ""))
                    
                    if is_valid and (current_country, final_name) not in seen:
                        companies.append({
                            "country": current_country,
                            "company": final_name,
                            "wiki_url": wiki_url
                        })
                        seen.add((current_country, final_name))

    df = pd.DataFrame(companies)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    log_message(f"Process complete. Scraped {len(df)} records.")
    log_message(f"Data saved to {OUTPUT_FILE}")
    log_message("="*50)
    
    return df

if __name__ == "__main__":
    df = fetch_food_companies()
    if df is not None:
        log_loading("Scraper Result Complete.")