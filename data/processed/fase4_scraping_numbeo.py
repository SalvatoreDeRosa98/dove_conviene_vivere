import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import re
import time
import random

print(">>> Avvio Scraping Costo della Vita (Numbeo)...")

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

def formatta_citta_numbeo(citta):
    if pd.isna(citta):
        return ""
    citta = str(citta).strip().title()
    
    eccezioni = {
        "Monza E Della Brianza": "Monza",
        "Reggio Nell'Emilia": "Reggio-Emilia",
        "Reggio Di Calabria": "Reggio-Calabria",
        "Forlì-Cesena": "Forli",
        "Pesaro E Urbino": "Pesaro",
        "Massa-Carrara": "Massa",
        "Valle D'Aosta/Vallée D'Aoste": "Aosta",
        "Bolzano/Bozen": "Bolzano",
        "L'Aquila": "L-Aquila" # Aggiunta l'Aquila
    }
    
    if citta in eccezioni:
        return eccezioni[citta]
        
    citta = citta.replace(" ", "-").replace("'", "-")
    citta = citta.replace("ì", "i").replace("ò", "o").replace("à", "a").replace("è", "e").replace("é", "e")
    return citta

def estrai_dati_numbeo(citta):
    citta_url = formatta_citta_numbeo(citta)
    if not citta_url:
        return None, None

    # TORNATI ALL'URL CORRETTO
    url = f"https://it.numbeo.com/costo-della-vita/città/{citta_url}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        r = scraper.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            testo = soup.get_text()
            
            # Regex potenziata: cerca "singola" e "famiglia" vicino a cifre e al simbolo €
            # Ignora cosa c'è scritto in mezzo
            match_single = re.search(r"singola[^\d]*?([\d\.,]+)\s*€", testo, re.IGNORECASE)
            match_famiglia = re.search(r"famiglia[^\d]*?([\d\.,]+)\s*€", testo, re.IGNORECASE)
            
            costo_single = None
            costo_famiglia = None
            
            if match_single:
                val_str = match_single.group(1).replace('.', '').replace(',', '.')
                costo_single = float(val_str)
                
            if match_famiglia:
                val_str = match_famiglia.group(1).replace('.', '').replace(',', '.')
                costo_famiglia = float(val_str)
                
            return costo_single, costo_famiglia
            
        elif r.status_code == 404:
            # Stampiamo l'URL se fallisce, così capiamo cosa cerca
            print(f"      [!] 404 - Città non presente nel database Numbeo: {citta_url}")
            return None, None
        else:
            print(f"      [!] Errore {r.status_code} dal server Numbeo")
            return None, None
            
    except Exception as e:
        print(f"      [!] Errore di connessione: {e}")
        return None, None

def main():
    try:
        df = pd.read_csv("affitti_completi.csv")
    except FileNotFoundError:
        print("ERRORE: File 'affitti_completi.csv' non trovato!")
        return

    costi_single = []
    costi_famiglia = []
    
    print(f">>> File caricato. Inizio estrazione per {len(df)} province...")

    for idx, row in df.iterrows():
        citta = row['provincia']
        print(f"[{idx+1}/{len(df)}] Analisi di {citta}...")
        
        single, famiglia = estrai_dati_numbeo(citta)
        
        if single or famiglia:
            print(f"  --> TROVATO: Single {single}€ | Famiglia {famiglia}€")
        else:
            print("  --> Dato non trovato.")
            
        costi_single.append(single)
        costi_famiglia.append(famiglia)
        
        time.sleep(random.uniform(2.5, 4.5))

    df['costo_vita_single'] = costi_single
    df['costo_vita_famiglia'] = costi_famiglia
    
    nome_file = "dataset_reale_completo.csv"
    df.to_csv(nome_file, index=False)
    print(f"\n✅ Finito! Il tuo dataset definitivo è salvato in '{nome_file}'.")

if __name__ == "__main__":
    main()