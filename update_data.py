import json
import requests
import yfinance as yf
from datetime import datetime

def fetch_data():
    data = {
        "last_update": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "live"
    }
    
    try:
        # 1. Shiller-KGV
        req = requests.get('https://www.econdb.com/api/series/SHILLER_CAPE/?format=json', timeout=10)
        data['shiller_kgv'] = round(req.json()['data']['values'][-1], 1)
    except:
        data['shiller_kgv'] = 40.5 # Fallback

    # 2. Yahoo Finance Live-Kurse & Indizes
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
            hist = yf.Ticker(ticker).history(period="1d")
            if not hist.empty:
                val = hist['Close'].iloc[-1]
                data[key] = round(val, 2) if key in ["copper", "eurusd", "vix"] else round(val, 0)
        except Exception as e:
            print(f"Fehler bei {ticker}: {e}")

    # Speichern als data.json
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
        
    print("Daten erfolgreich in data.json geschrieben!")

if __name__ == "__main__":
    fetch_data()
Klicke unten auf "Commit changes..." (Speichern).

Schritt 3: Den Automatisierungs-Knopf anlegen (.github/workflows/update.yml)
Das sagt GitHub, dass es das Python-Skript auf Knopfdruck ausführen soll.

Klicke auf "Add file" -> "Create new file".

Als Dateinamen tippst du exakt ein: .github/workflows/update.yml (Die Ordner .github/workflows/ werden automatisch erstellt, wenn du sie eintippst).

Kopiere diesen Code hinein:

YAML
name: Live-Daten aktualisieren

on:
  workflow_dispatch: # Erzeugt den manuellen Start-Button auf GitHub

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Code auschecken
        uses: actions/checkout@v3
        
      - name: Python einrichten
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Pakete installieren
        run: pip install yfinance requests
          
      - name: Skript ausführen
        run: python update_data.py
          
      - name: Änderungen speichern & pushen
        run: |
          git config --global user.name "Makro-Bot"
          git config --global user.email "bot@dashboard.local"
          git add data.json
          git commit -m "Automatisches Live-Daten Update" || echo "Keine Änderungen"
          git push
