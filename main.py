from src import scraper
from src import process_link
from src import final_process_link
from src import company_summary
from src import get_infobox_simple
from src import get_infobox_numeric
from src.utils_logger import print_data_summary
import os

# Workflow flags
SKIP_SCRAPER = False
SKIP_PROCESS_LINK = False
SKIP_FINAL_PROCESS_LINK = False
SKIP_SUMMARY = False
SKIP_INFOBOX = False
SKIP_NUMERIC = False
SKIP_CLEANUP = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def cleanup_intermediate_files():
    files = [
        os.path.join(DATA_DIR, 'food_companies_with_sites.csv'),
        os.path.join(DATA_DIR, 'food_companies_with_sites_final.csv'),
        os.path.join(DATA_DIR, 'food_companies_with_summary.csv'),
        os.path.join(DATA_DIR, 'food_companies_with_infobox.csv'),
    ]
    for f in files:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted: {f}")

def run_pipeline():
    # 1. Scraper
    if not SKIP_SCRAPER:
        print(">>> Starting: Scraping...")
        scraper.fetch_food_companies()

    # 2. Process Link
    if not SKIP_PROCESS_LINK:
        print(">>> Starting: Process Links...")
        process_link.process_links()

    # 3. Final Enrichment
    if not SKIP_FINAL_PROCESS_LINK:
        print(">>> Starting: Final Enrichment...")
        final_process_link.final_enrich()

    # 4. Summary
    if not SKIP_SUMMARY:
        print(">>> Starting: Fetch Summaries...")
        company_summary.process_and_add_summary()

    #5. Infobox    
    if not SKIP_INFOBOX:
        print(">>> Starting: Fetch Infobox...")
        get_infobox_simple.process_and_add_infobox()
    
    #6. Numeric
    if not SKIP_NUMERIC:
        print(">>> Starting: Fetch Numeric Data...")
        get_infobox_numeric.process_and_add_numeric()
    
    #7. Cleanup files     
    if not SKIP_CLEANUP:
        print(">>> Cleaning up intermediate files...")
        cleanup_intermediate_files()


if __name__ == "__main__":
    run_pipeline()