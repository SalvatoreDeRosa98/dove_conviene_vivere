# =============================================================================
# FASE 4 — Motore di Confronto e Ranking
# Progetto: "Dove conviene vivere con il mio stipendio?"
# Autore: Salvatore De Rosa
# Data: 2026
# =============================================================================
# Questo modulo è il cervello del progetto: integra le Fasi 2 e 3.
#
# Cosa fa:
#   1. Prende la RAL e la città attuale dell'utente
#   2. Calcola il netto mensile per OGNI provincia (con la sua addizionale regionale)
#   3. Sottrae il costo della vita di ogni provincia
#   4. Produce un ranking nazionale: dove il tuo stipendio vale di più?
#   5. Mostra il delta: quanti euro in più/meno rispetto alla situazione attuale
#
# Insight chiave di questo modulo:
#   Il netto NON è uguale ovunque con la stessa RAL!
#   Puglia (0.8%) vs Calabria (2.3%) = differenza significativa.
#   Questo modulo lo calcola correttamente per ogni destinazione.
# =============================================================================


# ── LIBRERIE ──────────────────────────────────────────────────────────────────
import sys                       # per stampare avvisi sullo stderr
import pandas as pd              # per costruire e ordinare il DataFrame del ranking
from dataclasses import dataclass  # per strutturare gli input in modo pulito

# ── IMPORT DAI MODULI DELLE FASI PRECEDENTI ───────────────────────────────────
# Importiamo solo le funzioni/classi che ci servono, non tutto il modulo.
# Questo rende esplicite le dipendenze e facilita la lettura del codice.
from fase3_calcolatore_ral import ProfiloUtente, calcola_netto_mensile
from fase2_dati import (
    carica_dataset,
    trova_citta,
    get_costo_vita,
    calcola_stipendio_disponibile,
)


# =============================================================================
# SEZIONE 1 — STRUTTURA DATI INPUT
# =============================================================================

@dataclass
class InputAnalisi:
    """
    Raccoglie tutti i dati necessari per l'analisi completa.

    Combina:
      - dati fiscali (RAL, profilo, figli, coniuge) → usati dalla Fase 3
      - dato geografico (città attuale) → usato dalla Fase 2

    Separare InputAnalisi da ProfiloUtente serve perché:
      ProfiloUtente ha bisogno di una 'regione' specifica (cambia per ogni destinazione).
      InputAnalisi rappresenta l'utente PRIMA di sapere dove andrà.
    """
    ral: float                       # Reddito Annuo Lordo (es. 35000.0)
    profilo: str = "single"          # "single" | "coppia" | "famiglia"
    citta_attuale: str = "Milano"    # capoluogo/sigla/provincia di partenza
    figli: int = 0                   # numero di figli a carico
    coniuge_a_carico: bool = False   # coniuge senza reddito proprio?
    comune_aliquota: float = 0.0     # addizionale comunale (0.0–0.008)
    mesi_tredicesima: int = 13       # 13 o 14 mensilità


# =============================================================================
# SEZIONE 2 — FUNZIONE DI SUPPORTO: costruisci ProfiloUtente per una regione
# =============================================================================

def _profilo_per_regione(inp: InputAnalisi, regione: str) -> ProfiloUtente:
    """
    Funzione interna (inizia con _ per convenzione) che costruisce un
    ProfiloUtente con la regione della città di destinazione.

    Viene chiamata 107 volte nel ranking: una per ogni provincia.
    Ogni volta usiamo la regione DELLA DESTINAZIONE per avere il netto corretto.
    """
    return ProfiloUtente(
        ral=inp.ral,
        profilo=inp.profilo,
        figli=inp.figli,
        coniuge_a_carico=inp.coniuge_a_carico,
        regione=regione,                  # ← questo cambia a ogni iterazione
        comune_aliquota=inp.comune_aliquota,
        mesi_tredicesima=inp.mesi_tredicesima,
    )


# =============================================================================
# SEZIONE 3 — FUNZIONE PRINCIPALE: analisi_completa()
# =============================================================================

def analisi_completa(inp: InputAnalisi) -> dict:
    """
    Funzione principale della Fase 4. Riceve un InputAnalisi e restituisce
    un dizionario con tutti i risultati: situazione attuale + ranking 107 province.

    Flusso:
      1. Carica dataset Fase 2 (107 province)
      2. Trova la riga della città attuale → regione attuale
      3. Calcola netto mensile nella città attuale (Fase 3)
      4. Calcola costo vita nella città attuale (Fase 2)
      5. Per ogni provincia nel dataset:
           a. Prende la regione della destinazione
           b. Calcola il netto mensile per quella regione (Fase 3)
           c. Calcola il costo vita per quella città (Fase 2)
           d. Calcola lo stipendio disponibile
           e. Calcola il delta rispetto alla situazione attuale
      6. Ordina per stipendio disponibile (il più alto in cima)
      7. Restituisce tutto in un dizionario strutturato
    """

    # ── STEP 1: Carica il dataset ─────────────────────────────────────────────
    df = carica_dataset()

    # ── STEP 2: Identifica la città attuale e la sua regione ─────────────────
    # trova_citta() gestisce ricerca per capoluogo, sigla e nome provincia
    riga_attuale = trova_citta(df, inp.citta_attuale)
    regione_attuale  = riga_attuale["regione"]
    capoluogo_attuale = riga_attuale["capoluogo"]

    # ── STEP 3: Calcola netto mensile nella città attuale ────────────────────
    # Usiamo la regione attuale per avere l'addizionale regionale corretta
    profilo_attuale = _profilo_per_regione(inp, regione_attuale)
    busta_attuale   = calcola_netto_mensile(profilo_attuale)
    netto_attuale   = busta_attuale["netto_mensile"]

    # ── STEP 4: Costo vita nella città attuale ───────────────────────────────
    costo_attuale       = get_costo_vita(df, capoluogo_attuale, inp.profilo)
    disponibile_attuale = calcola_stipendio_disponibile(netto_attuale, costo_attuale)

    # ── STEP 5: Ranking — itera su tutte le 107 province ────────────────────
    risultati = []

    for _, riga in df.iterrows():
        # _ è l'indice della riga (non ci serve), riga è la pd.Series
        try:
            regione_dest   = riga["regione"]
            capoluogo_dest = riga["capoluogo"]

            # 5a. Calcola il netto nella regione di destinazione
            # (l'addizionale regionale cambia: es. 0.8% Puglia, 2.3% Calabria)
            profilo_dest = _profilo_per_regione(inp, regione_dest)
            busta_dest   = calcola_netto_mensile(profilo_dest)
            netto_dest   = busta_dest["netto_mensile"]

            # 5b. Costo vita nella città di destinazione
            costo_dest       = get_costo_vita(df, capoluogo_dest, inp.profilo)
            disponibile_dest = calcola_stipendio_disponibile(netto_dest, costo_dest)

            # 5c. Delta rispetto alla situazione attuale:
            # positivo = stai meglio nella destinazione, negativo = stai peggio
            delta_mensile = round(disponibile_dest - disponibile_attuale, 2)
            delta_annuale = round(delta_mensile * 12, 0)

            risultati.append({
                "sigla":                 riga["sigla"],
                "capoluogo":             capoluogo_dest,
                "regione":               regione_dest,
                "area":                  riga["area"],
                "netto_mensile":         netto_dest,
                "affitto":               costo_dest["affitto"],
                "costo_vita_totale":     costo_dest["costo_totale_mensile"],
                "stipendio_disponibile": disponibile_dest,
                "risparmio_annuo":       round(disponibile_dest * 12, 0),
                "delta_mensile":         delta_mensile,
                "delta_annuale":         delta_annuale,
            })

        except Exception as e:
            # Se una riga ha un problema, saltiamo e avvisiamo
            print(f"⚠️  Saltata '{riga.get('capoluogo', '?')}': {e}", file=sys.stderr)
            continue

    # ── STEP 6: Costruisce DataFrame e ordina ────────────────────────────────
    df_rank = pd.DataFrame(risultati)

    # Ordina: la città con più stipendio disponibile è al primo posto
    df_rank = df_rank.sort_values("stipendio_disponibile", ascending=False)
    df_rank = df_rank.reset_index(drop=True)

    # Aggiunge la colonna rank (parte da 1)
    df_rank["rank"] = df_rank.index + 1

    # Riordina le colonne in modo logico
    df_rank = df_rank[[
        "rank", "sigla", "capoluogo", "regione", "area",
        "netto_mensile", "affitto", "costo_vita_totale",
        "stipendio_disponibile", "risparmio_annuo",
        "delta_mensile", "delta_annuale"
    ]]

    # ── STEP 7: Trova il rank della città attuale nel ranking ────────────────
    # Usiamo .str.lower() per confronto case-insensitive
    maschera_attuale = df_rank["capoluogo"].str.lower() == capoluogo_attuale.lower()
    riga_rank_attuale = df_rank[maschera_attuale]

    # Se trovata, prende il numero di rank; altrimenti None
    rank_attuale = int(riga_rank_attuale["rank"].iloc[0]) if not riga_rank_attuale.empty else None

    # ── STEP 8: Prepara l'output ─────────────────────────────────────────────
    return {
        # --- Input originale ---
        "input":                   inp,
        # --- Situazione attuale ---
        "citta_attuale":           capoluogo_attuale,
        "regione_attuale":         regione_attuale,
        "netto_mensile_attuale":   netto_attuale,
        "costo_vita_attuale":      costo_attuale["costo_totale_mensile"],
        "disponibile_attuale":     disponibile_attuale,
        "risparmio_annuo_attuale": round(disponibile_attuale * 12, 0),
        "rank_citta_attuale":      rank_attuale,
        # --- Ranking completo ---
        "ranking":                 df_rank,
        # --- Top 5 come lista di dizionari (pronti per Streamlit/JSON) ---
        "top5":                    df_rank.head(5).to_dict("records"),
        # --- Busta paga attuale (dettaglio Fase 3) ---
        "busta_paga_attuale":      busta_attuale,
    }


# =============================================================================
# SEZIONE 4 — FUNZIONE DI STAMPA DEL REPORT
# =============================================================================

def stampa_analisi(risultato: dict) -> None:
    """
    Stampa il report completo dell'analisi in forma leggibile.
    Verrà sostituito dalla UI Streamlit nella Fase 5, ma è utile per debug.
    """
    inp = risultato["input"]
    sep = "─" * 70

    print(f"\n{'═' * 70}")
    print(f"  ANALISI COMPLETA — RAL {inp.ral:,.0f} € | Profilo: {inp.profilo.upper()}")
    print(f"{'═' * 70}")

    # ── Situazione attuale ────────────────────────────────────────────────────
    print(f"\n  📍 SITUAZIONE ATTUALE: "
          f"{risultato['citta_attuale']} ({risultato['regione_attuale']})")
    print(f"  {sep[:50]}")
    print(f"  Netto mensile:           {risultato['netto_mensile_attuale']:>8,.0f} €")
    print(f"  Costo vita (fisso):     -{risultato['costo_vita_attuale']:>8,.0f} €")
    print(f"  {'─' * 40}")
    print(f"  Disponibile:             {risultato['disponibile_attuale']:>8,.0f} €/mese")
    print(f"  Risparmio potenziale:    {risultato['risparmio_annuo_attuale']:>8,.0f} €/anno")
    print(f"  Rank nazionale:          {risultato['rank_citta_attuale']:>8} / 107")

    # ── Top 5 ─────────────────────────────────────────────────────────────────
    print(f"\n  🏆 TOP 5 — DOVE IL TUO STIPENDIO VALE DI PIÙ")
    print(f"  {sep}")
    intestazione = (
        f"  {'#':>3}  {'Città':<15} {'Regione':<20} "
        f"{'Netto':>7}  {'Costo':>7}  {'Disponibile':>11}  {'Δ vs ora':>10}"
    )
    print(intestazione)
    print(f"  {sep}")

    for city in risultato["top5"]:
        # Formatta il delta con segno + o -
        delta = city["delta_mensile"]
        delta_str = f"+{delta:,.0f}€" if delta >= 0 else f"{delta:,.0f}€"

        print(
            f"  {int(city['rank']):>3}. {city['capoluogo']:<15} {city['regione']:<20} "
            f"{city['netto_mensile']:>6,.0f}€  {city['costo_vita_totale']:>6,.0f}€  "
            f"{city['stipendio_disponibile']:>10,.0f}€  {delta_str:>10}"
        )

    # ── Messaggio riassuntivo ─────────────────────────────────────────────────
    migliore = risultato["top5"][0]
    print(f"\n  {'─' * 60}")
    print(f"\n  💡 Con la stessa RAL di {inp.ral:,.0f} €, trasferendoti a")
    print(f"     {migliore['capoluogo']} ({migliore['regione']}) avresti:")
    print(f"     {migliore['delta_mensile']:+,.0f} €/mese  "
          f"({migliore['delta_annuale']:+,.0f} €/anno)")
    print(f"     rispetto a {risultato['citta_attuale']}.\n")

    # ── Bottom 3 (le peggiori) ────────────────────────────────────────────────
    df_rank = risultato["ranking"]
    peggiori = df_rank.tail(3).iloc[::-1]  # ultime 3 righe, rovesciate

    print(f"  ⚠️  LE 3 CITTÀ MENO CONVENIENTI")
    print(f"  {sep[:50]}")
    for _, row in peggiori.iterrows():
        delta = row["delta_mensile"]
        delta_str = f"{delta:+,.0f}€"
        print(
            f"  {int(row['rank']):>3}. {row['capoluogo']:<15} {row['regione']:<20} "
            f"Disponibile: {row['stipendio_disponibile']:>7,.0f}€  Δ {delta_str}"
        )

    print(f"\n{'═' * 70}\n")


# =============================================================================
# SEZIONE 5 — FUNZIONE: esporta risultati in CSV
# =============================================================================

def esporta_ranking_csv(risultato: dict, percorso: str = None) -> str:
    """
    Esporta il ranking completo in un file CSV.
    Utile per analisi in Excel o per la dashboard Streamlit.

    Se non si specifica il percorso, salva nella stessa cartella del progetto.
    Restituisce il percorso del file salvato.
    """
    from pathlib import Path

    if percorso is None:
        # Salva nella stessa cartella di questo script
        cartella = Path(__file__).parent
        nome_file = f"fase4_ranking_{risultato['citta_attuale'].lower()}_{int(risultato['input'].ral)}.csv"
        percorso = str(cartella / nome_file)

    # Seleziona le colonne più utili per l'esportazione
    df_export = risultato["ranking"][[
        "rank", "sigla", "capoluogo", "regione", "area",
        "netto_mensile", "affitto", "costo_vita_totale",
        "stipendio_disponibile", "risparmio_annuo",
        "delta_mensile", "delta_annuale"
    ]]

    df_export.to_csv(percorso, index=False, encoding="utf-8")
    print(f"✅ Ranking esportato in: {percorso}")
    return percorso


# =============================================================================
# SEZIONE 6 — TEST RAPIDO
# =============================================================================

if __name__ == "__main__":
    # ── Caso 1: Single, 35.000 € RAL, vive a Milano ───────────────────────────
    caso1 = InputAnalisi(
        ral=35_000,
        profilo="single",
        citta_attuale="Milano"
    )
    risultato1 = analisi_completa(caso1)
    stampa_analisi(risultato1)

    # ── Caso 2: Famiglia (2 figli), 45.000 € RAL, vive a Roma ─────────────────
    caso2 = InputAnalisi(
        ral=45_000,
        profilo="famiglia",
        citta_attuale="Roma",
        figli=2,
        coniuge_a_carico=True,
    )
    risultato2 = analisi_completa(caso2)
    stampa_analisi(risultato2)

    # ── Esporta il ranking del caso 1 in CSV ──────────────────────────────────
    esporta_ranking_csv(risultato1)
