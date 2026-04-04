import requests
import random
import time
import zipfile
import io
from datetime import datetime, timezone

# --- CONFIG ---
# Batch size for onscreen display, but it will process the full 1,000,000 file
BATCH_SIZE = 1000 
KEYWORDS = ["stf", "adm", "pnl", "admin", "login", "portal", "panel", "staff", "manage"]
OUTPUT_FILE = "found_domains.txt"

def get_real_websites():
    print(f"Downloading 1,000,000 domains and searching for {KEYWORDS}...")
    
    # Using the Cisco Umbrella Top 1 Million list (S3 Zip link)
    # This is often faster and more stable than other sources
    url = "https://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            # Extracting the CSV from the ZIP file in memory
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # The file inside the zip is usually 'top-1m.csv'
                csv_filename = z.namelist()[0]
                with z.open(csv_filename) as f:
                    found_domains = []
                    for line in f:
                        decoded_line = line.decode('utf-8').strip().lower()
                        if "," in decoded_line:
                            # Format is "Rank,Domain"
                            domain = decoded_line.split(',')[-1]
                            if any(k in domain for k in KEYWORDS) and "." in domain:
                                found_domains.append(domain)
                    
                    if found_domains:
                        random.shuffle(found_domains)
                        return [f"http://{d}" for d in found_domains]
    except Exception as e:
        print(f"Download or Parsing Error: {e}")
    
    return []

def save_to_file(websites):
    with open(OUTPUT_FILE, "w") as f:
        for site in websites:
            f.write(site + "\n")
    print(f"--- SUCCESS: {len(websites)} clean domains saved to {OUTPUT_FILE} ---")

def main():
    while True:
        websites = get_real_websites()
        
        if websites:
            save_to_file(websites)
            print("\nPreview of clean URLs found:")
            for site in websites[:10]:
                print(f" [+] {site}")
        else:
            print("No domains found. Retrying in 60s...")

        print(f"\nFinished at {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC")
        print("Waiting 60 seconds for next random batch...\n")
        time.sleep(60)

if __name__ == "__main__":
    main()
