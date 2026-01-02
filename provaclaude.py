from bs4 import BeautifulSoup
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import time

# Forza backend non-interattivo PRIMA di tutto
import matplotlib
matplotlib.use('Agg', force=True)
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates

# Disabilita modalità interattiva
plt.ioff()

print(f"Backend matplotlib: {matplotlib.get_backend()}")

# -------------------------------
# Cartella e CSV
# -------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "most_active_last_year.csv")

# -------------------------------
# Prendere ticker più attivi
# -------------------------------
url = "https://finance.yahoo.com/markets/stocks/most-active/"
headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table is None:
        raise Exception("Tabella non trovata su Yahoo Finance")
    
    tickers = [row.find_all("td")[0].text.strip() for row in table.find("tbody").find_all("tr")]
    print(f"Ticker trovati: {tickers}")
except Exception as e:
    print(f"Errore nello scraping: {e}")
    exit(1)

# -------------------------------
# Intervallo 1 anno
# -------------------------------
oggi = datetime.today()
un_anno_fa = oggi - timedelta(days=365)

# -------------------------------
# Scaricare dati e filtrare ticker validi
# -------------------------------
all_rows = []

for ticker in tickers:
    print(f"Scarico dati per {ticker}...")
    
    try:
        df = yf.download(
            ticker,
            start=un_anno_fa.strftime("%Y-%m-%d"),
            end=oggi.strftime("%Y-%m-%d"),
            progress=False
        )
        
        # Pausa per evitare rate limiting
        time.sleep(0.5)
        
        if df.empty:
            print(f"  {ticker} - nessun dato disponibile")
            continue
        
        # Gestisci colonne multi-livello
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.reset_index()
        
        # Controlla colonne necessarie
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            print(f"  {ticker} - colonne mancanti")
            continue
        
        # Converti a numerico
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Rimuovi righe non valide
        df_valid = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        if df_valid.empty:
            print(f"  {ticker} - dati non validi")
            continue
        
        df_valid["Ticker"] = ticker
        all_rows.append(df_valid)
        print(f"  {ticker} - ✓ {len(df_valid)} righe valide")
        
    except Exception as e:
        print(f"  {ticker} - errore: {e}")
        continue

# -------------------------------
# Creare CSV
# -------------------------------
if not all_rows:
    print("ERRORE: Nessun dato valido scaricato!")
    exit(1)

final_df = pd.concat(all_rows, ignore_index=True)
final_df["Date"] = pd.to_datetime(final_df["Date"])
final_df.to_csv(csv_path, index=False)
print(f"\n✓ CSV creato: {csv_path}")

# -------------------------------
# Creare grafici a candele
# -------------------------------
cartella_grafici = os.path.join(base_dir, "Grafici")
os.makedirs(cartella_grafici, exist_ok=True)

print(f"\nCreazione grafici in: {cartella_grafici}")

for ticker in final_df['Ticker'].unique():
    try:
        df_ticker = final_df[final_df['Ticker'] == ticker].copy()
        df_ticker = df_ticker.sort_values('Date')
        
        # Crea figura
        fig = plt.figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        # Determina colori
        colors = ['green' if close >= open_ else 'red' 
                  for close, open_ in zip(df_ticker['Close'], df_ticker['Open'])]
        
        # Disegna candele
        for date, open_, high, low, close, color in zip(
            df_ticker['Date'], df_ticker['Open'], df_ticker['High'], 
            df_ticker['Low'], df_ticker['Close'], colors):
            
            # Linea verticale (High-Low)
            ax.plot([date, date], [low, high], color='black', linewidth=1)
            
            # Corpo candela
            height = abs(close - open_)
            bottom = min(open_, close)
            ax.bar(date, height, bottom=bottom, width=0.6, color=color, alpha=0.8)
        
        ax.set_title(f"{ticker} - Grafico a candele (1 anno)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Prezzo ($)")
        fig.autofmt_xdate()
        fig.tight_layout()
        
        # Salva e chiudi
        output_path = os.path.join(cartella_grafici, f"{ticker}.png")
        fig.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        print(f"  ✓ {ticker}.png salvato")
        
    except Exception as e:
        print(f"  ✗ Errore con {ticker}: {e}")
        continue

print(f"\n✓ Completato! Grafici salvati in: {cartella_grafici}")