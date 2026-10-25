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
    
    # 1. Shiller-KGV (Aktueller Wert + Echte Historie)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = requests.get('https://www.multpl.com/shiller-pe/table/by-month', headers=headers, timeout=10)
        df = pd.read_html(req.text)[0]
        
        current_val = float(str(df.iloc[0, 1]).replace('estimate', '').strip())
        data['shiller_kgv'] = round(current_val, 1)

        history = []
        for index, row in df.iterrows():
            try:
                date_str = str(row[0])
                val_str = str(row[1]).replace('estimate', '').strip()
                val = float(val_str)
                
                cleaned_date = date_str.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                dt = datetime.strptime(cleaned_date, '%b %d, %Y')
                
                if dt.month in [5, 12] and dt.year >= 2011:
                    history.append({
                        "date": dt.strftime("%m.%Y"),
                        "value": val
                    })
            except Exception:
                continue
        
        history = sorted(history, key=lambda x: datetime.strptime(x["date"], "%m.%Y"))
        data['shiller_kgv_history'] = history

    except Exception as e:
        print(f"Fehler beim Laden des Shiller-KGV: {e}")
        data['shiller_kgv'] = 40.4
        data['shiller_kgv_history'] = []

    # 2. Yahoo Finance Daten + echte 1-Jahres-Historie für die Detailansicht
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
            # 1 Jahr Historie für den Detail-Chart holen
            df_yf = t.history(period="1y")
            if not df_yf.empty:
                val = df_yf['Close'].iloc[-1]
                is_decimal = key in ["copper", "eurusd", "vix"]
                data[key] = round(float(val), 2) if is_decimal else round(float(val), 0)
                
                # Historie aufbereiten
                hist_list = []
                for date_idx, row in df_yf.iterrows():
                    hist_list.append({
                        "date": date_idx.strftime("%d.%m.%Y"),
                        "value": round(float(row['Close']), 2) if is_decimal else round(float(row['Close']), 0)
                    })
                data[f"{key}_history"] = hist_list
        except Exception as e:
            print(f"Konnte {ticker} nicht laden: {e}")

    # Speichern als data.json
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
        
    print("Daten und Historien erfolgreich gespeichert!")

if __name__ == "__main__":
    fetch_data()
