import json
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

def fetch_data():
    data = {
        "last_update": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "live"
    }
    
    # 1. Shiller-KGV (Live-Abruf über multpl.com)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = requests.get('https://www.multpl.com/shiller-pe/table/by-month', headers=headers, timeout=10)
        # Liest alle HTML-Tabellen der Seite ein
        df = pd.read_html(req.text)[0]
        # Greift auf die erste Zeile (aktuellster Monat) und zweite Spalte (Wert) zu
        cape_str = str(df.iloc[0, 1]) 
        # Entfernt Text wie "estimate" und wandelt in eine Zahl um
        val = float(cape_str.replace('estimate', '').strip())
        data['shiller_kgv'] = round(val, 1)
    except Exception as e:
        print(f"Fehler beim Laden des Shiller-KGV: {e}")
        data['shiller_kgv'] = 37.5 # Realistischerer Fallback

    # 2. Yahoo Finance Daten einzeln abfragen (mit Fehlerbehandlung)
    tickers = {
        "sp500": "^GSPC",
        "nasdaq": "^NDX",
        "dax": "^GDAXI",
        "mdax": "^MDAXI",
        "stoxx": "^STOXX50E",
        "nikkei": "^N225",
        "hangseng": "^HSI",
        "msci": "URTH",  # iShares MSCI World ETF
        "ftse": "VT",    # Vanguard Total World Stock ETF
        "vix": "^VIX",
        "copper": "HG=F",
        "eurusd": "EURUSD=X"
    }

    for key, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            df_yf = t.history(period="5d")
            if not df_yf.empty:
                val = df_yf['Close'].iloc[-1]
                data[key] = round(float(val), 2) if key in ["copper", "eurusd", "vix"] else round(float(val), 0)
        except Exception as e:
            print(f"Konnte {ticker} nicht laden: {e}")

    # Speichern als data.json
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
        
    print("Daten erfolgreich gespeichert!")

if __name__ == "__main__":
    fetch_data()
