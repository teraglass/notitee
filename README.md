
Automated notifier for market indicators using Python.

Features

- Fetches S&P500 200-day moving average via yfinance
- Fetches CNN Fear & Greed index
- Fetches USD index and USD/KRW exchange rate
- Sends notifications via Slack
- GitHub Actions workflow to run daily and commit state changes

Quickstart

1. Create a virtualenv and install:

```bash
python -m venv .venv
source .venv/bin/activate      # on Windows use .venv\Scripts\activate
pip install -r requirements.txt
```

2. Set environment variables for notifications (one or both):

- Slack: `SLACK_TOKEN`

3. Run locally:

```bash
# Simple way (recommended)
python run.py

# Or with module path
# On Windows
set PYTHONPATH=src
python -m notitee.main

# On Unix/macOS
export PYTHONPATH=src
python -m notitee.main
```

GitHub Actions

The workflow is in `.github/workflows/daily-fetcher.yml`. It runs daily and on manual dispatch. Store your secrets in the repo settings (`SLACK_WEBHOOK`, `SMTP_HOST`, etc.). 

# notitee
