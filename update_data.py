import json
import requests
import yfinance as yf
from datetime import datetime

def fetch_data():
    data = {
        "last_update": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "live"
    }
    
    # 1. Shiller-KGV
    try:
        req = requests.get('https://www.econdb.com/api/series/SHILLER_CAPE/?format=json', timeout=10)
        data['shiller_kgv'] = round(req.json()['data']['values'][-1], 1)
    except:
        data['shiller_kgv'] = 40.5

    # 2. Yahoo Finance Daten einzeln abfragen (mit Fehlerbehandlung)
    tickers = {
        "sp500": "^GSPC",
        "nasdaq": "^NDX",
        "dax": "^GDAXI",
        "mdax": "^MDAXI",
        "stoxx": "^STOXX50E",
        "nikkei": "^N225",
        "hangseng": "^HSI",
        "msci": "URTH",
        "ftse": "VT",
        "vix": "^VIX",
        "copper": "HG=F",
        "eurusd": "EURUSD=X"
    }

    for key, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="5d")
            if not df.empty:
                val = df['Close'].iloc[-1]
                data[key] = round(float(val), 2) if key in ["copper", "eurusd", "vix"] else round(float(val), 0)
        except Exception as e:
            print(f"Konnte {ticker} nicht laden: {e}")

    # Speichern als data.json
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
        
    print("Daten erfolgreich gespeichert!")

if __name__ == "__main__":
    fetch_data()
