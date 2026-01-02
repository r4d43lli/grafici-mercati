from bs4 import BeautifulSoup
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
os.environ['MPLBACKEND'] = 'Agg'
import matplotlibt
print(f"Backend in uso: {matplotlib.get_backend()}") 
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
plt.ioff()


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

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table")
if table is None:
    raise Exception("Tabella non trovata su Yahoo Finance")

tickers = [row.find_all("td")[0].text.strip() for row in table.find("tbody").find_all("tr")]
print("Ticker trovati:", tickers)

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
    df = yf.download(
        ticker,
        start=un_anno_fa.strftime("%Y-%m-%d"),
        end=oggi.strftime("%Y-%m-%d"),
        progress=False
    )
    
    # Scarta ticker senza dati
    if df.empty:
        print(f"{ticker} senza dati, salto")
        continue

# Aggiungi questa riga:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)


    df = df.reset_index()

    # Controlla colonne
    required_cols = ['Date','Open','High','Low','Close']
    if not all(col in df.columns for col in required_cols):
        print(f"{ticker} mancano colonne necessarie, salto")
        continue

    # Converti colonne OHLC in numerico, eventuali valori non numerici diventano NaN
    for col in ['Open','High','Low','Close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Mantieni solo righe completamente valide
    df_valid = df.dropna(subset=['Open','High','Low','Close'])

    if df_valid.empty:
        print(f"{ticker} senza dati validi, salto")
        continue

    df_valid["Ticker"] = ticker
    all_rows.append(df_valid)

# -------------------------------
# Creare CSV
# -------------------------------
if not all_rows:
    raise Exception("Nessun dato valido scaricato")

final_df = pd.concat(all_rows, ignore_index=True)
final_df["Date"] = pd.to_datetime(final_df["Date"])
final_df.to_csv(csv_path, index=False)
print(f"CSV creato correttamente in:\n{csv_path}")

# -------------------------------
# Creare grafici a candele
# -------------------------------
cartella_grafici = os.path.join(base_dir, "Grafici")
os.makedirs(cartella_grafici, exist_ok=True)

for ticker in final_df['Ticker'].unique():
    df_ticker = final_df[final_df['Ticker'] == ticker].copy()
    df_ticker = df_ticker.sort_values('Date')
    
    fig, ax = plt.subplots(figsize=(12,6))
    
    # Determina colore (verde se chiusura > apertura, rosso altrimenti)
    colors = ['green' if close >= open_ else 'red' 
              for close, open_ in zip(df_ticker['Close'], df_ticker['Open'])]
    
    # Corpo della candela (rettangolo tra Open e Close)
    for i, (date, open_, high, low, close, color) in enumerate(
        zip(df_ticker['Date'], df_ticker['Open'], df_ticker['High'], 
            df_ticker['Low'], df_ticker['Close'], colors)):
        
        # Linea verticale (High-Low)
        ax.plot([date, date], [low, high], color='black', linewidth=1)
        
        # Rettangolo corpo candela
        height = abs(close - open_)
        bottom = min(open_, close)
        ax.bar(date, height, bottom=bottom, width=0.6, color=color, alpha=0.8)
    
    ax.set_title(f"{ticker} - Grafico a candele 1 anno")
    ax.set_xlabel("Data")
    ax.set_ylabel("Prezzo ($)")
    fig.autofmt_xdate()
    plt.tight_layout()
    output_path = os.path.join(cartella_grafici, f"{ticker}.png")
    fig.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
print(f"grafici salvati in: {cartella_grafici}")
plt.close('all')