# =============================================================================
# FASE 3 — Calcolatore RAL → Stipendio Netto Mensile
# Progetto: "Dove conviene vivere con il mio stipendio?"
# Autore: Salvatore De Rosa
# Data: 2026
# =============================================================================
# RIFERIMENTI NORMATIVI:
#   - IRPEF 2024: D.Lgs. 216/2023 (riforma fiscale)
#   - Contributi INPS: aliquota 9.19% (lavoro dipendente privato)
#   - Detrazioni lavoro dipendente: art. 13 TUIR aggiornato 2024/2025
#   - Addizionali regionali: aliquote 2023 (Ministero Economia)
#   - Bonus Irpef / trattamento integrativo: Legge 21/2020
# =============================================================================

# ── LIBRERIE ──────────────────────────────────────────────────────────────────
from dataclasses import dataclass  # per creare strutture dati ordinate (tipo "oggetti semplici")


# =============================================================================
# SEZIONE 1 — STRUTTURA DATI PER IL PROFILO UTENTE
# =============================================================================

@dataclass
class ProfiloUtente:
    """
    Contiene tutte le informazioni personali che influenzano il calcolo fiscale.
    Usiamo @dataclass per evitare di scrivere __init__ a mano.
    """
    ral: float                          # Reddito Annuo Lordo in euro (es. 35000.0)
    profilo: str = "single"             # "single" | "coppia" | "famiglia"
    figli: int = 0                      # numero di figli a carico
    coniuge_a_carico: bool = False      # True se il coniuge non ha reddito proprio
    regione: str = "Lombardia"          # regione di residenza (influenza addizionale)
    comune_aliquota: float = 0.0        # aliquota addizionale comunale (0.0 – 0.008)
    mesi_tredicesima: int = 13          # 13 = tredicesima inclusa, 14 = quattordicesima


# =============================================================================
# SEZIONE 2 — SCAGLIONI IRPEF 2024
# =============================================================================
# La riforma 2024 (D.Lgs. 216/2023), resa strutturale dal 2025,
# ha ridotto gli scaglioni da 4 a 3:
#   • 23% fino a 28.000 €
#   • 35% da 28.001 € a 50.000 €
#   • 43% oltre 50.000 €
#
# Ogni tupla è: (limite_superiore, aliquota)
# None = nessun limite superiore (scaglione infinito)

SCAGLIONI_IRPEF = [
    (28_000, 0.23),   # Primo scaglione:  0 – 28.000 €  →  23%
    (50_000, 0.35),   # Secondo scaglione: 28.001 – 50.000 €  →  35%
    (None,   0.43),   # Terzo scaglione:  oltre 50.000 €  →  43%
]


def calcola_irpef_lorda(reddito_imponibile: float) -> float:
    """
    Calcola l'IRPEF lorda applicando gli scaglioni progressivi.

    'Progressiva' significa: ogni scaglione si applica SOLO alla parte
    di reddito che cade in quello scaglione, non all'intero reddito.

    Esempio con 35.000 €:
      • 28.000 × 23%  =  6.440 €
      •  7.000 × 35%  =  2.450 €
      • TOTALE        =  8.890 €
    """
    if reddito_imponibile <= 0:
        return 0.0  # nessun reddito, nessuna imposta

    irpef = 0.0          # accumulatore: sommiamo l'imposta scaglione per scaglione
    gia_tassato = 0.0    # tiene traccia di quanti euro abbiamo già "consumato"

    for limite, aliquota in SCAGLIONI_IRPEF:
        if limite is None:
            # Ultimo scaglione: tutto il reddito rimasto viene tassato
            parte = reddito_imponibile - gia_tassato
        else:
            # Quanto cade in questo scaglione?
            parte = min(reddito_imponibile, limite) - gia_tassato

        if parte <= 0:
            break  # il reddito non arriva fino a questo scaglione, usciamo

        irpef += parte * aliquota  # imposta = base × aliquota
        gia_tassato += parte       # aggiorniamo il contatore

    return round(irpef, 2)


# =============================================================================
# SEZIONE 3 — CONTRIBUTI INPS A CARICO DEL DIPENDENTE
# =============================================================================
# Il dipendente versa il 9.19% della RAL all'INPS (pensione, malattia, ecc.).
# Nota: i contributi si calcolano sulla RAL lorda PRIMA di qualsiasi detrazione.
# Esiste un massimale annuo (2024: ~119.650 €) oltre il quale l'aliquota scende.
# Per semplicità usiamo aliquota piena fino al massimale.

ALIQUOTA_INPS_DIPENDENTE = 0.0919   # 9,19%
MASSIMALE_INPS = 119_650.0          # massimale contributivo 2024

def calcola_contributi_inps(ral: float) -> float:
    """
    Calcola i contributi INPS annui a carico del dipendente.
    Sopra il massimale l'aliquota scende: per ora usiamo aliquota piena
    sull'intera RAL (errore < 0.5% per RAL sotto 120k).
    """
    base_contributiva = min(ral, MASSIMALE_INPS)
    return round(base_contributiva * ALIQUOTA_INPS_DIPENDENTE, 2)


# =============================================================================
# SEZIONE 4 — DETRAZIONE PER LAVORO DIPENDENTE
# =============================================================================
# Lo Stato riduce l'IRPEF lorda tramite una "detrazione" (uno sconto).
# La detrazione per lavoro dipendente dipende dal reddito complessivo:
#   • RC ≤ 15.000 €  →  1.955 € (ma non meno di 690 €)
#   • 15.001 – 28.000 €  →  1.910 + 1.190 × [(28.000 - RC) / 13.000]
#   • 28.001 – 50.000 €  →  1.910 × [(50.000 - RC) / 22.000]
#   • RC > 50.000 €  →  0 €
# Inoltre, tra 25.001 € e 35.000 €, la detrazione aumenta di 65 €.

def calcola_detrazione_lavoro(reddito_complessivo: float) -> float:
    """
    Restituisce la detrazione annua per lavoro dipendente (art. 13 TUIR 2024).
    Questa somma viene sottratta all'IRPEF lorda per ottenere l'IRPEF netta.
    """
    rc = reddito_complessivo

    if rc <= 0:
        return 0.0

    if rc <= 15_000:
        # Detrazione fissa, con un minimo garantito di 690 €.
        detrazione = 1_955.0
        return round(max(detrazione, 690.0), 2)

    elif rc <= 28_000:
        # Formula ufficiale: 1.910 + 1.190 × quota residua della fascia.
        detrazione = 1_910.0 + 1_190.0 * (28_000 - rc) / 13_000

    elif rc <= 50_000:
        # Decresce linearmente da 1.910 a 0 tra 28.001 e 50.000.
        detrazione = 1_910.0 * (50_000 - rc) / 22_000

    else:
        return 0.0  # nessuna detrazione sopra 50.000 €

    if 25_000 < rc <= 35_000:
        detrazione += 65.0

    return round(max(detrazione, 0.0), 2)


# =============================================================================
# SEZIONE 5 — BONUS IRPEF (Trattamento Integrativo)
# =============================================================================
# Per i redditi fino a 15.000 €, lo Stato può aggiungere fino a 1.200 € annui
# direttamente in busta paga (Legge 21/2020 — ex "bonus Renzi").
# Tra 15.001 € e 28.000 € il trattamento integrativo dipende da altre
# detrazioni fiscali specifiche: qui non lo stimiamo per evitare falsi positivi.

def calcola_bonus_irpef(
    reddito_complessivo: float,
    irpef_lorda: float,
    detrazione_lavoro: float
) -> float:
    """
    Restituisce il trattamento integrativo (bonus IRPEF) annuo.
    Sopra 15.000 € il calcolo richiede detrazioni fiscali che non sono presenti
    nel modello, quindi restituiamo 0.0 in modo conservativo.
    """
    rc = reddito_complessivo

    if rc <= 0:
        return 0.0

    if rc <= 15_000 and irpef_lorda > max(detrazione_lavoro - 75.0, 0.0):
        return 1_200.0  # bonus pieno

    return 0.0


# =============================================================================
# SEZIONE 6 — DETRAZIONI PER FAMILIARI A CARICO
# =============================================================================
# Lo Stato riconosce detrazioni aggiuntive per coniuge e figli a carico.
# I figli under 21 ora beneficiano dell'Assegno Unico (non detrazione IRPEF):
#   per semplicità manteniamo la logica pre-2022 per i figli 21+.
# Il coniuge a carico (reddito < 2.841 €) dà diritto a ~800 € di detrazione.

def calcola_detrazioni_familiari(
    reddito_complessivo: float,
    coniuge_a_carico: bool,
    figli: int
) -> float:
    """
    Calcola le detrazioni annue per coniuge e figli a carico.
    Nota: per figli < 21 anni vale l'Assegno Unico (fuori da questa funzione).
    """
    detrazione_totale = 0.0
    rc = reddito_complessivo

    # ── Detrazione per coniuge a carico ──────────────────────────────────────
    if coniuge_a_carico and rc > 0:
        if rc <= 15_000:
            det_coniuge = 800.0
        elif rc <= 40_000:
            det_coniuge = 800.0 * (1 - (rc - 15_000) / 25_000)
        elif rc <= 80_000:
            det_coniuge = 690.0 * (1 - (rc - 40_000) / 40_000)
        else:
            det_coniuge = 0.0
        detrazione_totale += max(det_coniuge, 0.0)

    # ── Detrazione per figli a carico (21 anni e oltre) ───────────────────────
    # Per ogni figlio maggiorenne a carico: 950 € (valore semplificato)
    if figli > 0:
        detrazione_figlio = 950.0 * figli
        # La detrazione si riduce con il reddito (formula semplificata)
        if rc > 0:
            fattore = (95_000 - rc) / 95_000
            detrazione_figlio = max(detrazione_figlio * fattore, 0.0)
        detrazione_totale += round(detrazione_figlio, 2)

    return round(detrazione_totale, 2)


# =============================================================================
# SEZIONE 7 — ADDIZIONALE REGIONALE IRPEF
# =============================================================================
# Ogni regione applica una propria aliquota sull'IRPEF.
# Qui usiamo l'aliquota base (prima fascia) per semplicità.
# Fonte: Ministero dell'Economia, tabella 2023.

ADDIZIONALI_REGIONALI = {
    "Abruzzo":              0.0173,
    "Basilicata":           0.0124,
    "Calabria":             0.0230,
    "Campania":             0.0220,
    "Emilia-Romagna":       0.0133,
    "Friuli-Venezia Giulia":0.0123,
    "Lazio":                0.0173,
    "Liguria":              0.0123,
    "Lombardia":            0.0123,
    "Marche":               0.0133,
    "Molise":               0.0173,
    "Piemonte":             0.0133,
    "Puglia":               0.0080,
    "Sardegna":             0.0173,
    "Sicilia":              0.0173,
    "Toscana":              0.0123,
    "Trentino-Alto Adige":  0.0123,
    "Umbria":               0.0123,
    "Valle d'Aosta":        0.0070,
    "Veneto":               0.0123,
}

def calcola_addizionale_regionale(reddito_complessivo: float, regione: str) -> float:
    """
    Calcola l'addizionale regionale annua.
    Se la regione non è nel dizionario, usa l'aliquota nazionale minima 1.23%.
    """
    aliquota = ADDIZIONALI_REGIONALI.get(regione, 0.0123)  # default 1.23%
    return round(reddito_complessivo * aliquota, 2)


# =============================================================================
# SEZIONE 8 — FUNZIONE PRINCIPALE: calcola_netto_mensile()
# =============================================================================

def calcola_netto_mensile(profilo: ProfiloUtente) -> dict:
    """
    Funzione principale: riceve un ProfiloUtente e restituisce un dizionario
    con tutti i dettagli del calcolo (annuo e mensile).

    Flusso del calcolo:
      1. RAL lorda
      2. - Contributi INPS dipendente
      3. = Reddito imponibile IRPEF
      4. IRPEF lorda (scaglioni)
      5. - Detrazione lavoro dipendente
      6. - Detrazioni familiari
      7. = IRPEF netta
      8. + Bonus IRPEF (trattamento integrativo)
      9. - Addizionale regionale
     10. - Addizionale comunale
     11. = Imposta totale netta
     12. Netto annuo = RAL - Contributi INPS - Imposta totale
     13. Netto mensile = Netto annuo / mesi
    """
    ral = profilo.ral

    # ── STEP 1: Contributi INPS ───────────────────────────────────────────────
    contributi_inps = calcola_contributi_inps(ral)

    # ── STEP 2: Reddito imponibile ────────────────────────────────────────────
    # Il reddito su cui si calcola l'IRPEF è la RAL meno i contributi INPS
    reddito_imponibile = ral - contributi_inps

    # ── STEP 3: IRPEF lorda ───────────────────────────────────────────────────
    irpef_lorda = calcola_irpef_lorda(reddito_imponibile)

    # ── STEP 4: Detrazioni ────────────────────────────────────────────────────
    det_lavoro    = calcola_detrazione_lavoro(reddito_imponibile)
    det_familiari = calcola_detrazioni_familiari(
        reddito_imponibile, profilo.coniuge_a_carico, profilo.figli
    )

    # ── STEP 5: IRPEF netta ───────────────────────────────────────────────────
    irpef_netta = max(irpef_lorda - det_lavoro - det_familiari, 0.0)

    # ── STEP 6: Bonus IRPEF ───────────────────────────────────────────────────
    bonus_irpef = calcola_bonus_irpef(reddito_imponibile, irpef_lorda, det_lavoro)

    # ── STEP 7: Addizionali ───────────────────────────────────────────────────
    add_regionale = calcola_addizionale_regionale(reddito_imponibile, profilo.regione)
    add_comunale  = round(reddito_imponibile * profilo.comune_aliquota, 2)

    # ── STEP 8: Imposta totale netta ──────────────────────────────────────────
    imposta_totale = irpef_netta - bonus_irpef + add_regionale + add_comunale

    # ── STEP 9: Netto annuo e mensile ────────────────────────────────────────
    netto_annuo   = round(ral - contributi_inps - imposta_totale, 2)
    netto_mensile = round(netto_annuo / profilo.mesi_tredicesima, 2)

    # ── OUTPUT: dizionario con tutti i dettagli ───────────────────────────────
    return {
        # Input
        "ral":                   ral,
        "profilo":               profilo.profilo,
        "regione":               profilo.regione,
        # Contributi
        "contributi_inps":       contributi_inps,
        "reddito_imponibile":    round(reddito_imponibile, 2),
        # IRPEF
        "irpef_lorda":           irpef_lorda,
        "detrazione_lavoro":     det_lavoro,
        "detrazioni_familiari":  det_familiari,
        "irpef_netta":           round(irpef_netta, 2),
        "bonus_irpef":           bonus_irpef,
        # Addizionali
        "addizionale_regionale": add_regionale,
        "addizionale_comunale":  add_comunale,
        # Totali
        "imposta_totale":        round(imposta_totale, 2),
        "netto_annuo":           netto_annuo,
        "netto_mensile":         netto_mensile,
        "aliquota_effettiva_%":  round((imposta_totale + contributi_inps) / ral * 100, 1),
    }


# =============================================================================
# SEZIONE 9 — FUNZIONE DI STAMPA LEGGIBILE
# =============================================================================

def stampa_busta_paga(risultato: dict) -> None:
    """Stampa un riepilogo formattato tipo busta paga."""
    sep = "─" * 45
    print(f"\n{'═' * 45}")
    print(f"  BUSTA PAGA SIMULATA — RAL {risultato['ral']:,.0f} €")
    print(f"  Profilo: {risultato['profilo']} | Regione: {risultato['regione']}")
    print(f"{'═' * 45}")
    print(f"  RAL lorda                    {risultato['ral']:>10,.2f} €")
    print(sep)
    print(f"  Contributi INPS (9.19%)      {risultato['contributi_inps']:>10,.2f} €")
    print(f"  Reddito imponibile           {risultato['reddito_imponibile']:>10,.2f} €")
    print(sep)
    print(f"  IRPEF lorda                  {risultato['irpef_lorda']:>10,.2f} €")
    print(f"  - Detrazione lavoro          {risultato['detrazione_lavoro']:>10,.2f} €")
    print(f"  - Detrazioni familiari       {risultato['detrazioni_familiari']:>10,.2f} €")
    print(f"  + Bonus IRPEF                {risultato['bonus_irpef']:>10,.2f} €")
    print(f"  IRPEF netta                  {risultato['irpef_netta']:>10,.2f} €")
    print(sep)
    print(f"  Addizionale regionale        {risultato['addizionale_regionale']:>10,.2f} €")
    print(f"  Addizionale comunale         {risultato['addizionale_comunale']:>10,.2f} €")
    print(sep)
    print(f"  IMPOSTA TOTALE               {risultato['imposta_totale']:>10,.2f} €")
    print(f"{'═' * 45}")
    print(f"  NETTO ANNUO                  {risultato['netto_annuo']:>10,.2f} €")
    print(f"  NETTO MENSILE (13°)          {risultato['netto_mensile']:>10,.2f} €")
    print(f"  Aliquota effettiva           {risultato['aliquota_effettiva_%']:>9.1f} %")
    print(f"{'═' * 45}\n")


# =============================================================================
# SEZIONE 10 — TEST RAPIDO (eseguibile direttamente)
# =============================================================================

if __name__ == "__main__":
    # Questa sezione viene eseguita SOLO se lanci il file direttamente:
    #   python fase3_calcolatore_ral.py
    # Non viene eseguita se lo importi come modulo in un altro file.

    casi_test = [
        ProfiloUtente(ral=25_000, profilo="single",   regione="Lombardia"),
        ProfiloUtente(ral=35_000, profilo="single",   regione="Lombardia"),
        ProfiloUtente(ral=35_000, profilo="famiglia",  coniuge_a_carico=True, figli=2, regione="Campania"),
        ProfiloUtente(ral=50_000, profilo="coppia",   coniuge_a_carico=True, regione="Lazio"),
        ProfiloUtente(ral=70_000, profilo="single",   regione="Piemonte"),
    ]

    for caso in casi_test:
        risultato = calcola_netto_mensile(caso)
        stampa_busta_paga(risultato)
