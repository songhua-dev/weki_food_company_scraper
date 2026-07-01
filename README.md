# Company Data Extraction Pipeline

Extracts and structures company information (name, country, official website, 
business summary) from Wikipedia's List of Global Food Companies, with a 
gap-filling enrichment stage for incomplete entries.

## Highlights

- **Infobox-first extraction**: prioritizes structured Wikipedia infobox data 
  over free-text parsing, improving accuracy on inconsistent page layouts.
- **Two-tier confidence tracking**: confirmed websites are extracted directly 
  from Wikipedia infoboxes; unconfirmed candidates are flagged separately 
  rather than merged, avoiding false positives in the final dataset.
- **Precision-over-recall enrichment**: a secondary pass (`retry_enrich_data.py`) 
  fills gaps in the first pass using targeted noise-removal rules and a domain 
  blocklist — entries that can't be confidently resolved are flagged for 
  manual review rather than filled with low-confidence guesses.
- **Clean CSV output**: ready for direct use in Excel, Sheets, or CRM import.

## Tech Stack

Python · requests · BeautifulSoup4 · pandas

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Sample Output

| Company | Country | Website | Status | Summary |
|---|---|---|---|---|
| Ganong Bros. | Canada | http://www.ganong.com/ | Confirmed | Canadian chocolate and confectionery company founded 1873, the oldest company in its industry in Canada. |
| Earth's Own Food Company | Canada | *(unconfirmed — see possible_official_sites)* | Potential | Vegan food company and Canada's largest soy beverage company, based in Burnaby. |
| Gay Lea | Canada | *(not found — flagged for manual check)* | Manual Check Required | Dairy products co-operative producing butter, sour cream, cottage cheese and more. |
| McCain Foods | Canada | http://www.mccain.ca | Confirmed | World's largest manufacturer of frozen potato products, founded 1957. |

Out of 1,278 companies processed: **61.7% Confirmed**, 20.3% Potential, 
18.0% flagged for Manual Check — full breakdown reflects Wikipedia's own data 
completeness rather than extraction failures.

Full dataset: [`data/food_companies_final.csv`](./data/food_companies_final.csv)

---
Open to custom data extraction projects — feel free to reach out.