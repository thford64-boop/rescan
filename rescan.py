import requests
import random
import time
import zipfile
import io
from datetime import datetime, timezone
import asyncio
import httpx

# --- CONFIG ---
# Batch size to limit how many domains we pass to httpx at once
BATCH_SIZE = 1000 
KEYWORDS = ["stf", "adm", "pnl", "admin", "login", "portal", "panel", "staff", "manage"]
OUTPUT_FILE = "found_domains.txt"

def get_real_websites():
    print(f"Downloading 1,000,000 domains and searching for {KEYWORDS}...")
    
    # Using the Cisco Umbrella Top 1 Million list (S3 Zip link)
    url = "https://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = z.namelist()[0]
                with z.open(csv_filename) as f:
                    found_domains = []
                    for line in f:
                        decoded_line = line.decode('utf-8').strip().lower()
                        if "," in decoded_line:
                            domain = decoded_line.split(',')[-1]
                            if any(k in domain for k in KEYWORDS) and "." in domain:
                                found_domains.append(domain)
                    
                    if found_domains:
                        random.shuffle(found_domains)
                        return [f"http://{d}" for d in found_domains]
    except Exception as e:
        print(f"Download or Parsing Error: {e}")
    
    return []

async def check_active_domains(domains, limit=50):
    print(f"\nChecking {len(domains)} domains for active HTTP status (Max {limit} concurrent)...")
    semaphore = asyncio.Semaphore(limit)

    async def probe(url):
        async with semaphore:
            try:
                # Disguise our request as a standard web browser
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                
                async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, headers=headers) as client:
                    response = await client.get(url)
                    # We only care about pages that actually load
                    if response.status_code == 200:
                        print(f" [+] [LIVE] {url}")
                        return url
            except Exception:
                return None

    # Gather all concurrent tasks
    tasks = [probe(url) for url in domains]
    results = await asyncio.gather(*tasks)
    
    # Filter out the None values where the connection failed or timed out
    return [r for r in results if r]

def save_to_file(websites):
    # Changed to 'a' (append) so the continuous loop doesn't overwrite previous hits
    with open(OUTPUT_FILE, "a") as f:
        for site in websites:
            f.write(site + "\n")
    print(f"--- SUCCESS: {len(websites)} LIVE domains appended to {OUTPUT_FILE} ---")

async def main():
    while True:
        # Step 1: Get the massive list of matches
        websites = get_real_websites()
        
        if websites:
            # Step 2: Slice to our batch limit so we don't crash our network connection
            batch_to_scan = websites[:BATCH_SIZE]
            
            # Step 3: Check which ones are actually alive
            active_websites = await check_active_domains(batch_to_scan, limit=50)
            
            if active_websites:
                save_to_file(active_websites)
            else:
                print("None of the tested domains were active.")
        else:
            print("No domains found. Retrying in 60s...")

        print(f"\nFinished cycle at {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC")
        print("Waiting 60 seconds for next random batch...\n")
        
        # Use asyncio.sleep instead of time.sleep in an async loop
        await asyncio.sleep(60)

if __name__ == "__main__":
    # Run the async event loop
    asyncio.run(main())