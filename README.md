# città. — Dove conviene vivere con il mio stipendio?

> **"Milano ti sta rubando lo stipendio."**  
> Scopri quanto vale davvero il tuo RAL in ogni provincia italiana — tasse e costo della vita inclusi.

## Demo live

🔗 [apri su Streamlit Cloud](#) *(sostituisci con il link dopo il deploy)*

---

## Il progetto

Inserisci il tuo RAL, il profilo familiare e la città in cui vivi: l'app calcola il netto mensile reale (IRPEF 2024 + detrazioni), sottrae il costo della vita locale (affitto, spesa, trasporti, utenze) e ti mostra quant'è il tuo **stipendio disponibile** rispetto alle altre 107 province italiane.

**Funzionalità principali**

- Calcolo IRPEF 2024 con detrazioni per tipo di reddito, coniuge e figli a carico
- Ranking interattivo di tutti i 107 capoluoghi italiani
- Mappa a bolle (Plotly + OpenStreetMap, senza token)
- Confronto diretto tra due città con delta mensile e annuale
- **Biglietto condivisibile**: genera un PNG scaricabile con la tua situazione personalizzata

---

## Stack tecnico

| Layer | Tecnologia |
|---|---|
| Frontend / UI | Streamlit ≥ 1.32 |
| Grafici | Plotly ≥ 5.18 |
| Dati | Pandas ≥ 2.0 |
| Screenshot | html2canvas (CDN) |
| Dati fiscali | IRPEF 2024 (ISTAT / MEF) |
| Dati costo vita | Numbeo · Immobiliare.it |

---

## Struttura file

```
calcolatore/
├── fase5_streamlit.py        # App principale
├── fase4_motore.py           # Logica di analisi e ranking
├── fase3_calcolatore_ral.py  # Calcolo IRPEF e netto
├── fase2_dati.py             # Caricamento dataset e costo vita
├── dataset_province.csv      # Dati delle 107 province
├── requirements.txt
└── .gitignore
```

---

## Avvio locale

```bash
# 1. Clona il repo
git clone https://github.com/TUO_USERNAME/dove-conviene-vivere.git
cd dove-conviene-vivere

# 2. Crea ambiente virtuale (opzionale ma consigliato)
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Avvia l'app
streamlit run fase5_streamlit.py
```

L'app si apre su `http://localhost:8501`.

---

## Deploy su Streamlit Community Cloud

Vedi le istruzioni passo-passo in [DEPLOY.md](DEPLOY.md).

---

## Autore

**Salvatore De Rosa**  
[LinkedIn](https://www.linkedin.com/in/TUO_PROFILO) · [GitHub](https://github.com/TUO_USERNAME)

---

## Licenza

MIT — libero per uso personale e portfolio.
