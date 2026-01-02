# librerie 
from bs4 import BeautifulSoup
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt

# creazione delle cartelle
cartella_script = os.path.dirname(os.path.abspath(__file__))
file_csv = os.path.join(cartella_script, "dati_azioni.csv")
cartella_immagini = os.path.join(cartella_script, "Grafici")
os.makedirs(cartella_immagini, exist_ok=True)

# URL della pagina Yahoo 
link = "https://finance.yahoo.com/markets/stocks/most-active/"

# simulazione di un browser per evitare di venire bloccati dal sito
intestazione = {"User-Agent": "Mozilla/5.0"}

# richiesta di download della pagina web
risposta = requests.get(link, headers=intestazione)

# conversione da HTML a formato leggibile 
pagina = BeautifulSoup(risposta.text, "html.parser")

# ricerca della tabella con dentro i ticker
tabella = pagina.find("table")


# Estrazione dei simboli ticker dalla tabella
tickers = []
tbody = tabella.find("tbody")
righe = tbody.find_all("tr")

for riga in righe:
    celle = riga.find_all("td")
    prima_cella = celle[0]
    testo = prima_cella.text
    ticker = testo.strip()
    tickers.append(ticker)

print("Ticker trovati:", tickers)

# intervallo dei dati di un anno
oggi = datetime.today()
annoscorso = oggi - timedelta(days=365)

lista_dati = []

colonne = ['Date', 'Open', 'High', 'Low', 'Close']

# Download dei dati per ogni ticker
for ticker in tickers:
    print(f"Download per {ticker}...")
    
    # download dati storici da Yahoo Finance
    dati = yf.download(ticker, start=annoscorso.strftime("%Y-%m-%d"), end=oggi.strftime("%Y-%m-%d"), progress=False)


    
    # Gestione delle colonne multi-livello
    if isinstance(dati.columns, pd.MultiIndex):
        dati.columns = dati.columns.get_level_values(0)
    
    # Trasformazione dell'indice in colonna
    dati = dati.reset_index()
    

    
    # conversione delle colonne in formato numerico
    for col in ['Open', 'High', 'Low', 'Close']:
        dati[col] = pd.to_numeric(dati[col], errors='coerce')
    
    # cancellazione delle righe senza valori 
    dati = dati.dropna(subset=['Open', 'High', 'Low', 'Close'])
    
    # colonna ticker
    dati["Ticker"] = ticker
    lista_dati.append(dati)

# unione di tutti i dataframe


dati_completi = pd.concat(lista_dati, ignore_index=True)
dati_completi["Date"] = pd.to_datetime(dati_completi["Date"])

# salvataggio dei dati in CSV
dati_completi.to_csv(file_csv, index=False)
print(f"File CSV salvato: {file_csv}")

# Creazione dei grafici
print(f"Generazione grafici nella cartella: {cartella_immagini}")

for ticker in dati_completi['Ticker'].unique():
    # sceglie un ticker alla volta 
    dati_ticker = dati_completi[dati_completi['Ticker'] == ticker].copy()
    dati_ticker = dati_ticker.sort_values('Date')
    
    # Creazione della figura
    grafico, asse = plt.subplots(figsize=(12, 6))
    
    # colori delle candele
    colori = []
    for chiusura, apertura in zip(dati_ticker['Close'], dati_ticker['Open']):
        if chiusura >= apertura:
            colori.append('green')
        else:
            colori.append('red')
    
    # creazione della candela 
    for indice, (data, apertura, massimo, minimo, chiusura, colore) in enumerate(
        zip(dati_ticker['Date'], dati_ticker['Open'], dati_ticker['High'], 
            dati_ticker['Low'], dati_ticker['Close'], colori)):
        
        # linea sopra 
        asse.plot([data, data], [max(apertura, chiusura), massimo], color='black', linewidth=1)

        # linea sotto 
        asse.plot([data, data], [minimo, min(apertura, chiusura)], color='black', linewidth=1)

        # corpo 
        asse.bar(data, abs(chiusura - apertura), bottom=min(apertura, chiusura), 
                 width=1.7, color=colore, alpha=0.8, align='center')
    
    # creazione dei titoli 
    asse.set_title(f"{ticker}")
    asse.set_xlabel("Data")
    asse.set_ylabel("Prezzo ($)")
    grafico.autofmt_xdate()
    plt.tight_layout()

    # salvataggio del grafico
    percorso_file = os.path.join(cartella_immagini, f"{ticker}.png")
    grafico.savefig(percorso_file, dpi=100, bbox_inches='tight')
    plt.close(grafico)
    print(f"{ticker}.png salvato")

print(f"Grafici salvati in: {cartella_immagini}")
plt.close('all')