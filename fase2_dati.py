# =============================================================================
# FASE 2 — Struttura Dati e Analisi Costo della Vita
# Progetto: "Dove conviene vivere con il mio stipendio?"
# Autore: Salvatore De Rosa
# Data: 2026
# =============================================================================
# Questo modulo:
#   1. Carica il dataset delle 107 province italiane (fase2_dataset.csv)
#   2. Pulisce e valida i dati
#   3. Calcola il costo della vita mensile per qualsiasi città e profilo
#   4. Produce il ranking: "dove il tuo stipendio vale di più?"
#
# La formula chiave del progetto è:
#   Stipendio disponibile = Netto mensile - Affitto - Spesa - Trasporti - Utenze
# =============================================================================


# ── LIBRERIE ─────────────────────────────────────────────────────────────────
import pandas as pd          # libreria per lavorare con tabelle (DataFrame)
from pathlib import Path     # gestione percorsi file in modo cross-platform
import sys                   # per accedere a informazioni sul sistema (es. errori)


# =============================================================================
# SEZIONE 1 — PERCORSO DEL DATASET
# =============================================================================
# Path(__file__) restituisce il percorso del file corrente (fase2_dati.py).
# .parent risale alla cartella che lo contiene.
# Con / "fase2_dataset.csv" costruiamo il percorso completo del CSV.
# Questo funziona indipendentemente da dove lanci lo script.

DATASET_PATH = Path(__file__).parent / "fase2_dataset.csv"


# =============================================================================
# SEZIONE 2 — CARICAMENTO E VALIDAZIONE DEL DATASET
# =============================================================================

def carica_dataset() -> pd.DataFrame:
    """
    Legge fase2_dataset.csv e restituisce un DataFrame pandas pulito.

    Un DataFrame è come un foglio Excel in memoria: righe = province,
    colonne = affitto, spesa, trasporti, ecc.

    Operazioni eseguite:
      - verifica che il file esista
      - legge il CSV con pandas
      - rimuove spazi bianchi nei nomi delle colonne
      - converte le colonne numeriche al tipo float
      - elimina righe con valori mancanti (NaN)
    """
    # Controlla che il file CSV esista prima di aprirlo
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset non trovato: {DATASET_PATH}\n"
            "Assicurati che fase2_dataset.csv sia nella stessa cartella."
        )

    # Legge il CSV. sep="," = separatore virgola, encoding="utf-8" per le lettere accentate
    df = pd.read_csv(DATASET_PATH, sep=",", encoding="utf-8")

    # Rimuove eventuali spazi prima/dopo i nomi delle colonne (es. " sigla" → "sigla")
    df.columns = df.columns.str.strip()

    # Lista delle colonne che devono essere numeri
    colonne_numeriche = [
        "affitto_monolocale",
        "affitto_bilocale",
        "spesa_mensile_single",
        "trasporti_mensile",
        "utenze_mensile",
        "ristorante_medio",
    ]

    # Converte ogni colonna numerica: pd.to_numeric gestisce valori non validi
    # con errors="coerce" → i valori non convertibili diventano NaN (valore mancante)
    for col in colonne_numeriche:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Elimina le righe che hanno almeno un NaN nelle colonne numeriche
    righe_prima = len(df)
    df = df.dropna(subset=colonne_numeriche)
    righe_dopo = len(df)

    if righe_prima != righe_dopo:
        print(
            f"⚠️  Attenzione: {righe_prima - righe_dopo} righe rimosse per dati mancanti.",
            file=sys.stderr
        )

    # Resetta l'indice (i numeri di riga) dopo aver eliminato eventuali righe
    df = df.reset_index(drop=True)

    return df


# =============================================================================
# SEZIONE 3 — RICERCA DI UNA CITTÀ
# =============================================================================

def trova_citta(df: pd.DataFrame, nome: str) -> pd.Series:
    """
    Cerca una città nel dataset per nome del capoluogo, sigla o nome provincia.
    La ricerca è case-insensitive (non distingue maiuscole/minuscole).

    Restituisce una pd.Series = una singola riga del DataFrame.
    Lancia ValueError se la città non viene trovata.

    Esempi di ricerca validi:
      trova_citta(df, "Milano")
      trova_citta(df, "mi")
      trova_citta(df, "monza e brianza")
    """
    nome_lower = nome.lower().strip()  # converte in minuscolo e rimuove spazi

    # Prima cerca per capoluogo (es. "Milano", "Roma")
    maschera = df["capoluogo"].str.lower() == nome_lower
    if maschera.any():
        return df[maschera].iloc[0]  # .iloc[0] prende la prima riga trovata

    # Se non trova, cerca per sigla provincia (es. "MI", "RM")
    maschera = df["sigla"].str.lower() == nome_lower
    if maschera.any():
        return df[maschera].iloc[0]

    # Se non trova ancora, cerca per nome provincia completo (es. "Monza e Brianza")
    maschera = df["provincia"].str.lower().str.contains(nome_lower)
    if maschera.any():
        return df[maschera].iloc[0]

    # Nessuna corrispondenza trovata → errore chiaro con suggerimento
    raise ValueError(
        f"Città '{nome}' non trovata.\n"
        f"Usa il capoluogo (es. 'Milano'), la sigla (es. 'MI') "
        f"o parte del nome provincia."
    )


# =============================================================================
# SEZIONE 4 — CALCOLO COSTO DELLA VITA
# =============================================================================

def get_costo_vita(
    df: pd.DataFrame,
    nome_citta: str,
    profilo: str = "single"
) -> dict:
    """
    Calcola il costo mensile fisso per vivere in una città con un dato profilo.

    Parametri:
      df          → il DataFrame caricato con carica_dataset()
      nome_citta  → nome del capoluogo, sigla o provincia (es. "Milano", "MI")
      profilo     → "single" | "coppia" | "famiglia"

    Il costo include:
      - Affitto (monolocale per single, bilocale per coppia/famiglia)
      - Spesa alimentare mensile
      - Abbonamento trasporti pubblici
      - Utenze (luce + gas + internet)

    Nota: NON include svago, abbigliamento, imprevisti.
    Questi vanno nella "riserva" che emergerà dallo stipendio disponibile.
    """
    # Recupera la riga della città cercata
    riga = trova_citta(df, nome_citta)

    # Scelta dell'affitto in base al profilo:
    # single  → monolocale (~40 mq)
    # coppia o famiglia → bilocale (~65 mq)
    if profilo == "single":
        affitto = float(riga["affitto_monolocale"])
        spesa   = float(riga["spesa_mensile_single"])
    else:
        affitto = float(riga["affitto_bilocale"])
        # Per coppia/famiglia la spesa alimentare scala per 1.7 (non raddoppia
        # perché i prodotti sfusi e i formati famiglia costano meno per persona)
        spesa   = round(float(riga["spesa_mensile_single"]) * 1.7, 0)

    trasporti = float(riga["trasporti_mensile"])
    utenze    = float(riga["utenze_mensile"])

    # La somma di tutte le voci fisse
    costo_totale = affitto + spesa + trasporti + utenze

    return {
        "capoluogo":            riga["capoluogo"],
        "sigla":                riga["sigla"],
        "provincia":            riga["provincia"],
        "regione":              riga["regione"],
        "area":                 riga["area"],
        "affitto":              affitto,
        "spesa":                spesa,
        "trasporti":            trasporti,
        "utenze":               utenze,
        "costo_totale_mensile": round(costo_totale, 2),
    }


# =============================================================================
# SEZIONE 5 — FORMULA CHIAVE: STIPENDIO DISPONIBILE
# =============================================================================

def calcola_stipendio_disponibile(
    netto_mensile: float,
    costo_vita: dict
) -> float:
    """
    Calcola quanto ti rimane dopo aver pagato tutte le spese fisse.

    Questa è la metrica centrale del progetto:
      Stipendio disponibile = Netto mensile − Costo vita totale

    Un valore positivo significa che hai "avanzo" per svago, risparmio, ecc.
    Un valore negativo significa che lo stipendio non copre le spese di base.

    Esempio:
      Netto mensile a Milano:  1.950 €
      Costo vita Milano:      −1.840 €
      Disponibile:               110 €   ← pochissimo!

      Netto mensile a Bari:    1.950 €
      Costo vita Bari:        −1.094 €
      Disponibile:               856 €   ← molto più confortevole
    """
    return round(netto_mensile - costo_vita["costo_totale_mensile"], 2)


# =============================================================================
# SEZIONE 6 — RANKING NAZIONALE
# =============================================================================

def ranking_province(
    df: pd.DataFrame,
    netto_mensile: float,
    profilo: str = "single",
    top_n: int = 107,
    area_filtro: str = None
) -> pd.DataFrame:
    """
    Per ogni provincia calcola lo stipendio disponibile e restituisce
    un DataFrame ordinato dal più alto al più basso.

    Parametri:
      df            → DataFrame caricato
      netto_mensile → netto mensile calcolato dalla Fase 3
      profilo       → "single" | "coppia" | "famiglia"
      top_n         → quante righe restituire (default: tutte le 107)
      area_filtro   → filtra per area geografica (es. "Nord-Est", "Sud")
                      None = nessun filtro, tutte le aree

    L'output include anche il risparmio annuo potenziale (disponibile × 12).
    """
    # Se è stato specificato un filtro geografico, lavora solo su quelle righe
    df_lavoro = df.copy()
    if area_filtro:
        df_lavoro = df_lavoro[df_lavoro["area"] == area_filtro]
        if df_lavoro.empty:
            aree_valide = df["area"].unique().tolist()
            raise ValueError(
                f"Area '{area_filtro}' non trovata.\n"
                f"Aree disponibili: {aree_valide}"
            )

    risultati = []  # lista in cui accumuliamo un dizionario per ogni provincia

    # Itera su ogni riga del DataFrame con iterrows()
    # _ = indice della riga (non ci serve), riga = la riga come pd.Series
    for _, riga in df_lavoro.iterrows():
        try:
            costo = get_costo_vita(df, riga["capoluogo"], profilo)
            disponibile = calcola_stipendio_disponibile(netto_mensile, costo)

            risultati.append({
                "rank":                  None,           # sarà assegnato dopo l'ordinamento
                "sigla":                 riga["sigla"],
                "capoluogo":             riga["capoluogo"],
                "regione":               riga["regione"],
                "area":                  riga["area"],
                "affitto":               costo["affitto"],
                "costo_vita_totale":     costo["costo_totale_mensile"],
                "stipendio_disponibile": disponibile,
                "risparmio_annuo":       round(disponibile * 12, 0),
            })
        except Exception as e:
            # Se una riga ha un problema, la saltiamo e stampiamo un avviso
            print(f"⚠️  Saltata {riga.get('capoluogo', '?')}: {e}", file=sys.stderr)
            continue

    # Costruisce il DataFrame dai risultati e ordina per stipendio disponibile
    df_rank = pd.DataFrame(risultati)
    df_rank = df_rank.sort_values("stipendio_disponibile", ascending=False)
    df_rank = df_rank.reset_index(drop=True)

    # Aggiunge la colonna "rank" che parte da 1
    df_rank["rank"] = df_rank.index + 1

    # Riordina le colonne: rank prima di tutto
    df_rank = df_rank[
        ["rank", "sigla", "capoluogo", "regione", "area",
         "affitto", "costo_vita_totale", "stipendio_disponibile", "risparmio_annuo"]
    ]

    # Limita al numero di righe richiesto
    return df_rank.head(top_n)


# =============================================================================
# SEZIONE 7 — STAMPA RISULTATI
# =============================================================================

def stampa_ranking(df_rank: pd.DataFrame, top_n: int = 20) -> None:
    """
    Stampa il ranking in forma tabellare leggibile.
    Mostra solo le prime top_n righe per non riempire lo schermo.
    """
    print(f"\n{'═' * 75}")
    print(f"  TOP {top_n} PROVINCE PER STIPENDIO DISPONIBILE")
    print(f"{'═' * 75}")
    print(f"  {'#':>3}  {'Città':<16} {'Regione':<22} {'Affitto':>8}  "
          f"{'Costo vita':>10}  {'Disponibile':>11}  {'Risparmio/anno':>14}")
    print(f"  {'-' * 71}")

    for _, row in df_rank.head(top_n).iterrows():
        print(
            f"  {int(row['rank']):>3}. {row['capoluogo']:<16} {row['regione']:<22} "
            f"{row['affitto']:>7.0f}€  {row['costo_vita_totale']:>9.0f}€  "
            f"{row['stipendio_disponibile']:>10.0f}€  {row['risparmio_annuo']:>13.0f}€"
        )

    print(f"{'═' * 75}\n")


def stampa_confronto_citta(
    df: pd.DataFrame,
    netto_mensile: float,
    citta_a: str,
    citta_b: str,
    profilo: str = "single"
) -> None:
    """
    Confronto diretto tra due città: mostra fianco a fianco tutte le voci
    e quanto si risparmia spostandosi da una città all'altra.
    """
    costo_a = get_costo_vita(df, citta_a, profilo)
    costo_b = get_costo_vita(df, citta_b, profilo)
    disp_a  = calcola_stipendio_disponibile(netto_mensile, costo_a)
    disp_b  = calcola_stipendio_disponibile(netto_mensile, costo_b)
    delta   = round(disp_b - disp_a, 2)  # quanto in più hai nella città B rispetto alla A

    print(f"\n{'═' * 60}")
    print(f"  CONFRONTO: {costo_a['capoluogo']} vs {costo_b['capoluogo']}")
    print(f"  Profilo: {profilo} | Netto mensile: {netto_mensile:,.0f} €")
    print(f"{'═' * 60}")
    print(f"  {'Voce':<22} {costo_a['capoluogo']:>14}  {costo_b['capoluogo']:>14}")
    print(f"  {'-' * 52}")

    voci = [
        ("Affitto",      "affitto"),
        ("Spesa",        "spesa"),
        ("Trasporti",    "trasporti"),
        ("Utenze",       "utenze"),
        ("── TOTALE ──", "costo_totale_mensile"),
    ]

    for etichetta, chiave in voci:
        sep = "─" * 52 if etichetta.startswith("──") else ""
        if sep:
            print(f"  {sep}")
        print(f"  {etichetta:<22} {costo_a[chiave]:>13.0f}€  {costo_b[chiave]:>13.0f}€")

    print(f"{'─' * 60}")
    print(f"  {'Disponibile':>22} {disp_a:>13.0f}€  {disp_b:>13.0f}€")
    print(f"  {'Risparmio annuo':>22} {disp_a*12:>13.0f}€  {disp_b*12:>13.0f}€")
    print(f"{'═' * 60}")

    # Messaggio riassuntivo
    if delta > 0:
        print(f"\n  ✅ Trasferendoti a {costo_b['capoluogo']} avresti")
        print(f"     +{delta:.0f} €/mese in più  (+{delta*12:.0f} €/anno)\n")
    elif delta < 0:
        print(f"\n  ⚠️  A {costo_b['capoluogo']} avresti {abs(delta):.0f} €/mese in meno")
        print(f"     rispetto a {costo_a['capoluogo']}.\n")
    else:
        print(f"\n  Le due città hanno lo stesso impatto sul tuo stipendio.\n")


# =============================================================================
# SEZIONE 8 — TEST RAPIDO
# =============================================================================

if __name__ == "__main__":
    # ── Carica dataset ────────────────────────────────────────────────────────
    print("Caricamento dataset...")
    df = carica_dataset()
    print(f"✅ {len(df)} province caricate.\n")

    # ── Esempio: netto mensile di un 35.000 € RAL a Milano (da Fase 3) ───────
    NETTO_MENSILE_ESEMPIO = 1_948.0   # valore approssimativo da Fase 3

    # ── Ranking top 20 per un single ──────────────────────────────────────────
    rank = ranking_province(df, NETTO_MENSILE_ESEMPIO, profilo="single")
    stampa_ranking(rank, top_n=20)

    # ── Confronto Milano vs Bari ──────────────────────────────────────────────
    stampa_confronto_citta(df, NETTO_MENSILE_ESEMPIO, "Milano", "Bari", profilo="single")

    # ── Costo vita per una famiglia a Roma ────────────────────────────────────
    costo_roma = get_costo_vita(df, "Roma", profilo="famiglia")
    print(f"Costo vita famiglia a Roma: {costo_roma['costo_totale_mensile']:.0f} €/mese")
    disp_roma = calcola_stipendio_disponibile(NETTO_MENSILE_ESEMPIO, costo_roma)
    print(f"Disponibile: {disp_roma:.0f} €/mese")
