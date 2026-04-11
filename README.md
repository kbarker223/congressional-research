# Congressional Portfolio Construction

This project builds a stock portfolio using congressional trading disclosures 
as an alpha signal. The idea is simple: members of Congress sometimes trade 
stocks in ways that suggest they have access to information the public does not. 
This project tries to identify the most informative of those trades and use them 
to construct a portfolio.

## How It Works

1. **Collect trades** from Senate and House financial disclosures (STOCK Act filings)
2. **Calculate abnormal returns** for each trade using CAPM-adjusted event study methodology
3. **Build a signal** by weighting trades based on member track record, coordinated buying, and trade size
4. **Clean the covariance matrix** using Random Matrix Theory (Marchenko-Pastur)
5. **Optimize a portfolio** using mean-variance optimization with a 5% position cap
6. **Backtest** the strategy against SPY from 2016 to 2024

## Results

The strategy approximately tracks SPY with a mean annual alpha of -0.93%. 
Excluding 2022, which was a difficult year for growth stocks, the mean alpha 
improves to +1.07%. The strongest finding is that trades by top-performing 
members and coordinated purchases by multiple members generate statistically 
significant positive abnormal returns.

## Setup

1. Clone the repo
2. Install dependencies
3. Create a `.env` file in the project folder: LAMBDA_KEY=your_key_here (needed from lambda finance)
4. download existing data:
   - https://www.kaggle.com/datasets/heresjohnnyv/congress-investments
   - https://www.kaggle.com/datasets/shabbarank/congressional-trading-inception-to-march-23
   - https://www.kaggle.com/datasets/lukekerbs/us-senate-financial-disclosures-stocks-and-options
   - https://www.kaggle.com/datasets/jakewright/9000-tickers-of-stock-market-data-full-history
6. Run the scripts in order:
   - `senate_scraper.py` -- gets senate trades from gov website
   - `lambda_api_collection.py` -- uses lambda finance api to collect trades
   - `data_cleaning_and_analysis.ipynb` -- combines, cleans, and does correct calculations and analysis

## Data Sources

- Senate EFTS electronic filing system (scraped directly)
- Lambda Finance congressional trading API
- Prior dataset from Barker and Ichiba (2025)
- Price data from yfinance
- Risk-free rate from FRED (3-month T-bill)

## Research Paper

This project is the second part of a two-paper research series on congressional 
trading. The write-up is included in the repo as `Congressional_Portfolio_Construction.pdf`. 
The first part of the research is available as `Congressional_Trading_Research.pdf`.
