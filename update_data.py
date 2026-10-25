import json
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# Hilfsfunktion: Berechnet die Risikofarbe (0=Dunkelgrün, 1=Grün, 2=Blau, 3=Orange, 4=Rot)
def calculate_risk_category(current_val, avg_val, ideal='higher', is_index=False):
    if pd.isna(current_val) or pd.isna(avg_val) or avg_val == 0:
        return 2 # Neutral (Blau) als Fallback

    if is_index:
        excess = (current_val - avg_val) / avg_val
        if excess > 0.20:
            return 3 # Orange (Überhitzt)
            
    diff = ((current_val - avg_val) / abs(avg_val)) * 100
    if abs(diff) <= 0.5:
        return 2 # Blau
        
    if ideal == 'higher':
        if diff > 5: return 0
        elif diff > 0: return 1
        else: return 4
    elif ideal == 'lower':
        if diff < -5: return 0
        elif diff < 0: return 1
        else: return 4
    return 3

def fetch_data():
    data = {
        "last_update": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "live"
    }
    
    # 1. Shiller-KGV
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = requests.get('https://www.multpl.com/shiller-pe/table/by-month', headers=headers, timeout=10)
        df = pd.read_html(req.text)[0]
        data['shiller_kgv'] = round(float(str(df.iloc[0, 1]).replace('estimate', '').strip()), 1)
    except Exception as e:
        print(f"Fehler beim Shiller-KGV: {e}")
        data['shiller_kgv'] = 40.4

    # 2. Yahoo Finance Daten für 10 Jahre laden
    tickers = {
        "sp500": "^GSPC", "nasdaq": "^NDX", "dax": "^GDAXI", "mdax": "^MDAXI", 
        "stoxx": "^STOXX50E", "nikkei": "^N225", "hangseng": "^HSI", "msci": "URTH", 
        "ftse": "VT", "vix": "^VIX", "copper": "HG=F", "eurusd": "EURUSD=X"
    }

    current_year = datetime.now().year
    years_to_track = list(range(current_year - 10, current_year))
    
    # Zähler-Matrix: 5 Arrays (Dunkelgrün, Grün, Blau, Orange, Rot) für 10 Jahre
    risk_matrix = {0: [0]*10, 1: [0]*10, 2: [0]*10, 3: [0]*10, 4: [0]*10}

    for key, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            df_yf = t.history(period="10y")
            if not df_yf.empty:
                val = df_yf['Close'].iloc[-1]
                is_decimal = key in ["copper", "eurusd", "vix"]
                data[key] = round(float(val), 2) if is_decimal else round(float(val), 0)
                
                # 1-Jahres Historie für Detailcharts sichern
                df_1y = df_yf.tail(252) # ca. 252 Handelstage pro Jahr
                data[f"{key}_history"] = [{"date": idx.strftime("%d.%m.%Y"), "value": round(float(row['Close']), 2)} for idx, row in df_1y.iterrows()]

                # --- Historische Risiko-Berechnung (Oktober-Schnappschuss) ---
                df_yf['1Y_SMA'] = df_yf['Close'].rolling(window=252).mean()
                
                is_index = key not in ["vix", "copper", "eurusd"]
                ideal_dir = "lower" if key in ["vix", "eurusd"] else "higher"

                for i, target_year in enumerate(years_to_track):
                    # Finde den letzten Handelstag im Oktober (Monat 10) des jeweiligen Jahres
                    oct_data = df_yf[(df_yf.index.year == target_year) & (df_yf.index.month == 10)]
                    if not oct_data.empty:
                        last_oct_day = oct_data.iloc[-1]
                        cat = calculate_risk_category(last_oct_day['Close'], last_oct_day['1Y_SMA'], ideal_dir, is_index)
                        risk_matrix[cat][i] += 1
                        
        except Exception as e:
            print(f"Konnte {ticker} nicht laden: {e}")

    # Matrix ins JSON-Format übertragen
    data["risk_years_history"] = {
        "years": years_to_track,
        "dark_green": risk_matrix[0],
        "green": risk_matrix[1],
        "blue": risk_matrix[2],
        "orange": risk_matrix[3],
        "red": risk_matrix[4]
    }

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
        
    print("Daten inkl. echter historischer Oktober-Auswertung erfolgreich gespeichert!")

if __name__ == "__main__":
    fetch_data()
