import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import re
import time
import random

print(">>> Avvio Recupero Affitti da IDEALISTA.IT...")

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

def formatta_slug(testo):
    """Formatta il nome per l'URL di Idealista (es. 'Trentino-Alto Adige' -> 'trentino-alto-adige')"""
    if pd.isna(testo):
        return ""
    
    testo = str(testo).lower().strip()
    
    # Eccezioni specifiche
    eccezioni = {
        "valle d'aosta/vallée d'aoste": "valle-d-aosta",
        "trentino-alto adige/südtirol": "trentino-alto-adige",
        "bolzano/bozen": "bolzano",
        "l'aquila": "l-aquila",
        "forlì-cesena": "forli-cesena",
        "reggio nell'emilia": "reggio-emilia",
        "reggio di calabria": "reggio-calabria",
        "monza e della brianza": "monza-brianza"
    }
    
    if testo in eccezioni:
        return eccezioni[testo]
        
    testo = testo.replace("'", "-").replace(" ", "-")
    testo = testo.replace("ì", "i").replace("ò", "o").replace("à", "a").replace("è", "e").replace("é", "e")
    return testo

def scarica_pagina(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.it/"
    }
    try:
        r = scraper.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            return r.text
        elif r.status_code == 404:
            return "404"
        else:
            print(f"      [!] Errore {r.status_code} dal server")
            return None
    except Exception as e:
        print(f"      [!] Errore connessione: {e}")
        return None

def cerca_su_idealista(regione, citta):
    reg = formatta_slug(regione)
    cit = formatta_slug(citta)
    
    if not reg or not cit:
        return None

    # URL Standard Idealista: /andamento-prezzi/affitto/regione/provincia-provincia/
    url1 = f"https://www.idealista.it/andamento-prezzi/affitto/{reg}/{cit}-provincia/"
    html = scarica_pagina(url1)
    
    if html == "404" or html is None:
        time.sleep(2)
        # Se fallisce, proviamo l'URL senza "-provincia"
        url2 = f"https://www.idealista.it/andamento-prezzi/affitto/{reg}/{cit}/"
        html = scarica_pagina(url2)
        
    if html and html != "404":
        # Cerchiamo il prezzo. Idealista usa "10,5 €/m2" o "10,5 euro/m2"
        match = re.search(r"([\d,]+)\s*(?:€|euro)/m[q2²]", html, re.IGNORECASE)
        if match:
            valore_str = match.group(1).replace(',', '.')
            return float(valore_str)
            
    return None

def main():
    try:
        df = pd.read_csv("affitti_completi.csv")
    except FileNotFoundError:
        print(">>> ERRORE: File 'affitti_completi.csv' non trovato!")
        return

    # Troviamo solo le province dove il prezzo è mancante
    indici_mancanti = df[df['prezzo_affitto_mq'].isna()].index.tolist()
    
    if not indici_mancanti:
        print(">>> Il dataset è già completo! Non c'è nulla da recuperare.")
        return
        
    print(f">>> Trovate {len(indici_mancanti)} province senza dati. Attacco Idealista.it...\n")
    
    recuperati = 0
    for idx in indici_mancanti:
        r = df.loc[idx, 'regione']
        c = df.loc[idx, 'provincia']
        
        print(f"[*] Tento il recupero per: {c} ({r}) su Idealista...")
        
        prezzo = cerca_su_idealista(r, c)
        
        if prezzo:
            print(f"  --> SUCCESSO: {prezzo} €/m2")
            df.loc[idx, 'prezzo_affitto_mq'] = prezzo
            df.loc[idx, 'affitto_stimato_55mq'] = prezzo * 55
            recuperati += 1
        else:
            print("  --> FALLITO: URL non trovato o blocco server.")
            
        # Pausa per simulare lettura umana
        time.sleep(random.uniform(3.5, 6.0))

    # Salviamo il file aggiornato
    df.to_csv("affitti_completi.csv", index=False)
    print(f"\n>>> Operazione conclusa. Recuperati {recuperati} su {len(indici_mancanti)} da Idealista.")

if __name__ == "__main__":
    main()