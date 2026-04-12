import requests, time, pandas as pd, os
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("LAMBDA_KEY")
BASE = "https://www.lambdafin.com"

DATA_DIR = r'C:\Users\kaian\OneDrive\Desktop\RMT Finance Project\data'

#get trades
def fetch_all_congressional_trades():
    headers = {"Authorization": f"Bearer {KEY}"}
    all_trades = []
    page = 1

    while True:
        r = requests.get(
            f"{BASE}/api/congressional/trades",
            headers=headers,
            params={"page": page, "limit": 500}
        )
        data = r.json()

        trades = data.get("trades", [])
        has_more = data.get("hasMore", False)

        all_trades.extend(trades)
        print(f"Page {page}: {len(trades)} trades | total so far: {len(all_trades)}")

        if not has_more:
            print(f"hasMore=False — stopping at page {page}")
            break

        page += 1
        time.sleep(0.1)

    return pd.DataFrame(all_trades)

df_lambda = fetch_all_congressional_trades()
print(f"\nLambda raw shape: {df_lambda.shape}")
print(f"Lambda columns: {df_lambda.columns.tolist()}")

# standardize column names
df_lambda = df_lambda.rename(columns={
    "symbol":          "ticker",
    "representative":  "member",
    "transactionDate": "transaction_date",
    "disclosureDate":  "date_received",
    "type":            "transaction_type",
    "chamber":         "chamber",
})

# save
out_path = rf"{DATA_DIR}\lambda_trades.csv"
df_lambda.to_csv(out_path, index=False)
print(f"\nSaved {len(df_lambda):,} rows -> {out_path}")
