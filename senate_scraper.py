import requests, time, json, pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

FILE_PATH = Path(__file__).parent

BASE = "https://efdsearch.senate.gov"

def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    s.get(f"{BASE}/search/home/")
    # accept terms of service
    csrftoken = s.cookies.get("csrftoken")
    s.post(f"{BASE}/search/home/", data={
        "prohibition_agreement": "1",
        "csrfmiddlewaretoken": csrftoken,
    }, headers={"Referer": f"{BASE}/search/home/"})
    return s

def fetch_ptr_list(session, offset=0, limit=100):
    payload = {
        "start": offset,
        "length": limit,
        "report_types": "[11]",      # 11 = Periodic Transaction Report
        "filer_types": "[]",
        "submitted_start_date": "01/01/2012 00:00:00",
        "submitted_end_date": "12/31/2026 00:00:00",
        "candidate_state": "",
        "senator_state": "",
        "office_id": "",
        "first_name": "",
        "last_name": "",
    }
    headers = {
        "X-CSRFToken": session.cookies.get("csrftoken"),
        "Referer": f"{BASE}/search/",
    }
    r = session.post(f"{BASE}/search/report/data/", data=payload, headers=headers)
    r.raise_for_status()
    return r.json()

def fetch_all_ptrs(session):
    first = fetch_ptr_list(session, offset=0)
    total = first["recordsTotal"]
    records = first["data"]
    print(f"Total PTRs: {total}")
    
    offset = 100
    while offset < total:
        batch = fetch_ptr_list(session, offset=offset)
        records.extend(batch["data"])
        print(f"Fetched {len(records)}/{total}")
        offset += 100
        time.sleep(0.5)   # seemed to work but could change if needed
    return records

def parse_ptr_page(session, ptr_url):
    headers = {
        "Referer": f"{BASE}/search/",
        "X-CSRFToken": session.cookies.get("csrftoken"),
    }
    r = session.get(ptr_url, headers=headers)

    # Check we got the actual filing, not a redirect to home
    if "<title>eFD: Home</title>" in r.text:
        print(f"Session expired or redirect — refreshing session")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tbody tr")
    trades = []
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) >= 8:
            trades.append({
                "row_num":    cols[0],
                "tx_date":    cols[1],
                "owner":      cols[2],
                "ticker":     cols[3],
                "asset_name": cols[4],
                "asset_type": cols[5],
                "tx_type":    cols[6],
                "amount":     cols[7],
                "comment":    cols[8] if len(cols) > 8 else "",
            })
    return trades

def parse_ptr_list_entry(entry):
    if len(entry) == 6:
        # newer format: [first, last, office, report_type, date, link_html]
        link_html = entry[5]
        date_received = entry[4]
    elif len(entry) == 5:
        # older format: [first, last, office, link_html, date]
        link_html = entry[3]
        date_received = entry[4]
    else:
        print(f"Unknown format ({len(entry)} cols): {entry}")
        return None

    soup = BeautifulSoup(link_html, "html.parser")
    link = soup.find("a")
    if not link:
        return None

    href = link["href"]
    is_paper = "/paper/" in href   # PDF scan which well skip later

    return {
        "first_name":    entry[0],
        "last_name":     entry[1],
        "office":        entry[2],
        "date_received": date_received,
        "ptr_url":       BASE + href,
        "is_paper":      is_paper,
    }

def fetch_meta_and_trades(session, entry):
    meta = parse_ptr_list_entry(entry)
    if not meta or meta["is_paper"]:
        return []
    time.sleep(0.1)
    trades = parse_ptr_page(session, meta["ptr_url"])
    if trades is None:
        return []
    return [{**meta, **tx} for tx in trades]

def scrape_all(out_path="senate_trades.json", max_records=None):
    session = get_session()
    raw_ptrs = fetch_all_ptrs(session)
    if max_records is not None:
        raw_ptrs = raw_ptrs[:max_records]

    all_records = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_meta_and_trades, session, entry): i
                   for i, entry in enumerate(raw_ptrs)}
        for i, future in enumerate(as_completed(futures)):
            records = future.result()
            all_records.extend(records)
            if i % 50 == 0:
                print(f"[{i}/{len(raw_ptrs)}] fetched so far: {len(all_records)} trades")
                with open(out_path, "w") as f:
                    json.dump(all_records, f)

    with open(out_path, "w") as f:
        json.dump(all_records, f)

    return pd.DataFrame(all_records)


df = scrape_all(FILE_PATH / "senate_trades.json")
print(df.shape)
print(df.head())
df.to_csv(FILE_PATH / "senate_trades.csv", index=False)