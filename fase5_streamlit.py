# =============================================================================
# FASE 5 — Web App Streamlit
# Progetto: "Dove conviene vivere con il mio stipendio?"
# Autore: Salvatore De Rosa
# =============================================================================
# Lancia con:
#   streamlit run fase5_streamlit.py
# =============================================================================

import sys
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# Aggiunge la cartella del progetto al path Python così i moduli sono trovati
sys.path.insert(0, str(Path(__file__).parent))

from fase3_calcolatore_ral import ProfiloUtente, calcola_netto_mensile
from fase2_dati import carica_dataset, trova_citta, get_costo_vita, calcola_stipendio_disponibile
from fase4_motore import InputAnalisi, analisi_completa


# =============================================================================
# SEZIONE 1 — CONFIGURAZIONE PAGINA
# =============================================================================
# set_page_config DEVE essere la prima chiamata Streamlit del file.
# layout="wide" usa tutta la larghezza dello schermo.
# initial_sidebar_state="expanded" apre la sidebar di default.

st.set_page_config(
    page_title="città. — dove conviene vivere?",
    page_icon="🏙",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# SEZIONE 2 — PALETTE COLORI (dal design system del carosello)
# =============================================================================
# Estratti dagli screenshot forniti dal cliente:
#   Slide 1 (hook)        → sfondo giallo
#   Slide 2 (classifica) → sfondo crema
#   Slide 3 (care)        → sfondo rosso
#   Slide 4 (convenienti) → sfondo verde
#   Slide 5 (CTA)         → sfondo nero con testo giallo

C_YELLOW = "#F2C14E"   # giallo hero / accento brand
C_DARK   = "#0F0C08"   # nero profondo (quasi nero)
C_RED    = "#CC4433"   # rosso "più care" (indice > 110)
C_GREEN  = "#3A8C52"   # verde "più convenienti" (indice < 90)
C_AMBER  = "#E89E2A"   # arancio medio (indice 90-110)
C_CREAM  = "#EDE8DC"   # crema / beige di sfondo
C_WHITE  = "#F5F2EA"   # bianco caldo

# =============================================================================
# SEZIONE 2b — COORDINATE GEOGRAFICHE DEI 107 CAPOLUOGHI
# =============================================================================
# Dizionario {capoluogo: (lat, lon)} usato dalla mappa interattiva.
# I nomi corrispondono esattamente al campo "capoluogo" del dataset CSV.

LAT_LON = {
    # Lombardia
    "Milano":           (45.4654,  9.1866),
    "Monza":            (45.5845,  9.2744),
    "Como":             (45.8081,  9.0852),
    "Varese":           (45.8207,  8.8257),
    "Bergamo":          (45.6983,  9.6773),
    "Brescia":          (45.5416, 10.2118),
    "Lecco":            (45.8566,  9.3970),
    "Lodi":             (45.3143,  9.5034),
    "Pavia":            (45.1847,  9.1582),
    "Cremona":          (45.1327, 10.0227),
    "Mantova":          (45.1564, 10.7914),
    "Sondrio":          (46.1698,  9.8727),
    # Piemonte
    "Torino":           (45.0703,  7.6869),
    "Cuneo":            (44.3908,  7.5488),
    "Novara":           (45.4455,  8.6203),
    "Asti":             (44.9003,  8.2064),
    "Alessandria":      (44.9124,  8.6151),
    "Biella":           (45.5659,  8.0537),
    "Vercelli":         (45.3204,  8.4232),
    "Verbania":         (45.9235,  8.5519),
    # Liguria
    "Genova":           (44.4056,  8.9463),
    "La Spezia":        (44.1024,  9.8240),
    "Imperia":          (43.8886,  8.0306),
    "Savona":           (44.3074,  8.4823),
    # Valle d'Aosta
    "Aosta":            (45.7370,  7.3150),
    # Trentino-Alto Adige
    "Bolzano":          (46.4982, 11.3548),
    "Trento":           (46.0664, 11.1257),
    # Veneto
    "Venezia":          (45.4408, 12.3155),
    "Padova":           (45.4064, 11.8768),
    "Verona":           (45.4384, 10.9916),
    "Treviso":          (45.6669, 12.2420),
    "Vicenza":          (45.5455, 11.5353),
    "Belluno":          (46.1444, 12.2189),
    "Rovigo":           (45.0707, 11.7891),
    # Friuli-Venezia Giulia
    "Trieste":          (45.6495, 13.7768),
    "Udine":            (46.0643, 13.2350),
    "Gorizia":          (45.9419, 13.6207),
    "Pordenone":        (45.9639, 12.6616),
    # Emilia-Romagna
    "Bologna":          (44.4949, 11.3426),
    "Parma":            (44.8015, 10.3279),
    "Modena":           (44.6471, 10.9252),
    "Reggio Emilia":    (44.6989, 10.6312),
    "Rimini":           (44.0594, 12.5683),
    "Ferrara":          (44.8381, 11.6197),
    "Forlì":            (44.2227, 12.0407),
    "Piacenza":         (45.0526,  9.6932),
    "Ravenna":          (44.4184, 12.2035),
    # Toscana
    "Firenze":          (43.7696, 11.2558),
    "Prato":            (43.8777, 11.1023),
    "Pisa":             (43.7228, 10.4017),
    "Siena":            (43.3188, 11.3307),
    "Livorno":          (43.5480, 10.3106),
    "Lucca":            (43.8430, 10.5077),
    "Arezzo":           (43.4633, 11.8800),
    "Pistoia":          (43.9300, 10.9175),
    "Grosseto":         (42.7636, 11.1130),
    "Massa":            (44.0355, 10.1401),
    # Lazio
    "Roma":             (41.9028, 12.4964),
    "Latina":           (41.4677, 12.9038),
    "Frosinone":        (41.6399, 13.3436),
    "Viterbo":          (42.4175, 12.1063),
    "Rieti":            (42.4034, 12.8628),
    # Marche
    "Ancona":           (43.6158, 13.5189),
    "Pesaro":           (43.9100, 12.9130),
    "Macerata":         (43.2988, 13.4535),
    "Fermo":            (43.1602, 13.7189),
    "Ascoli Piceno":    (42.8536, 13.5749),
    # Umbria
    "Perugia":          (43.1122, 12.3888),
    "Terni":            (42.5636, 12.6408),
    # Abruzzo
    "L'Aquila":         (42.3476, 13.3995),
    "Pescara":          (42.4584, 14.2159),
    "Chieti":           (42.3539, 14.1662),
    "Teramo":           (42.6589, 13.7043),
    # Molise
    "Campobasso":       (41.5602, 14.6699),
    "Isernia":          (41.5954, 14.2330),
    # Campania
    "Napoli":           (40.8518, 14.2681),
    "Salerno":          (40.6824, 14.7681),
    "Caserta":          (41.0699, 14.3328),
    "Avellino":         (40.9146, 14.7903),
    "Benevento":        (41.1297, 14.7808),
    # Puglia
    "Bari":             (41.1171, 16.8719),
    "Lecce":            (40.3516, 18.1750),
    "Taranto":          (40.4645, 17.2470),
    "Foggia":           (41.4621, 15.5445),
    "Brindisi":         (40.6328, 17.9418),
    "Barletta":         (41.3178, 16.2844),
    # Basilicata
    "Potenza":          (40.6404, 15.8056),
    "Matera":           (40.6665, 16.6044),
    # Calabria
    "Catanzaro":        (38.8960, 16.5877),
    "Cosenza":          (39.3039, 16.2536),
    "Reggio Calabria":  (38.1113, 15.6474),
    "Crotone":          (39.0808, 17.1270),
    "Vibo Valentia":    (38.6722, 16.0989),
    # Sicilia
    "Palermo":          (38.1157, 13.3615),
    "Catania":          (37.5079, 15.0830),
    "Messina":          (38.1938, 15.5542),
    "Siracusa":         (37.0755, 15.2866),
    "Agrigento":        (37.3108, 13.5765),
    "Ragusa":           (36.9249, 14.7254),
    "Trapani":          (38.0174, 12.5113),
    "Enna":             (37.5659, 14.2767),
    "Caltanissetta":    (37.4919, 14.0615),
    # Sardegna
    "Cagliari":         (39.2238,  9.1217),
    "Sassari":          (40.7259,  8.5556),
    "Nuoro":            (40.3210,  9.3268),
    "Oristano":         (39.9062,  8.5913),
    "Carbonia":         (39.1662,  8.5236),
}


# =============================================================================
# SEZIONE 3 — CSS PERSONALIZZATO
# =============================================================================
# Usiamo st.markdown con unsafe_allow_html=True per iniettare CSS globale.
# Le triple-virgolette e le f-string permettono di usare le variabili di colore.
# NOTA: le doppie graffe {{ }} in una f-string producono una singola graffa { }.

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=Crimson+Pro:ital,wght@0,700;1,400;1,700&display=swap');

/* Nasconde elementi default di Streamlit */
#MainMenu {{ visibility: hidden; }}
footer    {{ visibility: hidden; }}
header    {{ visibility: hidden; }}

/* Sfondo generale */
.stApp {{ background-color: {C_CREAM}; font-family: 'Inter', sans-serif; }}

/* ── Hero (dark banner in cima) ─────────────────────────────────────── */
.hero {{
    background: {C_DARK};
    color: {C_WHITE};
    padding: 2.5rem 2rem 1.8rem;
    margin: -1rem -1rem 1.5rem;
    border-radius: 0 0 16px 16px;
}}
.hero-tag {{
    font-family: 'Courier New', monospace;
    font-size: 10px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(245, 242, 234, 0.4);
    margin-bottom: 0.9rem;
}}
.hero-h1 {{
    font-size: clamp(1.7rem, 3.5vw, 2.8rem);
    font-weight: 900;
    line-height: 1.05;
    margin: 0 0 0.7rem;
    color: {C_WHITE};
}}
.hero-h1 em {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-style: italic;
    font-weight: 400;
    color: {C_YELLOW};
}}
.hero-sub {{
    font-size: 0.88rem;
    color: rgba(245, 242, 234, 0.6);
    margin: 0 0 1.2rem;
    line-height: 1.6;
}}
.hero-brand {{
    font-size: 0.85rem;
    font-weight: 900;
    color: {C_YELLOW};
    font-family: 'Crimson Pro', Georgia, serif;
    font-style: italic;
    display: block;
}}

/* ── Metric card ────────────────────────────────────────────────────── */
.mc {{
    background: white;
    border-radius: 10px;
    padding: 1rem 1.2rem 0.9rem;
    border: 0.5px solid rgba(0,0,0,0.1);
    height: 100%;
}}
.mc-lbl {{
    font-size: 9.5px;
    font-family: 'Courier New', monospace;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #999;
    margin-bottom: 4px;
}}
.mc-val {{
    font-size: 1.9rem;
    font-weight: 900;
    color: {C_DARK};
    line-height: 1;
}}
.mc-sub {{
    font-size: 10px;
    color: #aaa;
    margin-top: 5px;
    font-family: 'Courier New', monospace;
}}
.mc-green  .mc-val {{ color: {C_GREEN}; }}
.mc-red    .mc-val {{ color: {C_RED};   }}
.mc-yellow .mc-val {{ color: {C_AMBER}; }}

/* ── Section header ─────────────────────────────────────────────────── */
.sec-h {{
    font-size: 1.55rem;
    font-weight: 900;
    color: {C_DARK};
    margin-bottom: 0.2rem;
    line-height: 1.1;
}}
.sec-h em {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-style: italic;
    font-weight: 400;
}}
.sec-sub {{
    font-size: 10.5px;
    font-family: 'Courier New', monospace;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 1.4rem;
    display: block;
}}

/* ── Rank row (top 5) ───────────────────────────────────────────────── */
.rk {{
    background: white;
    border-radius: 10px;
    padding: 13px 16px;
    margin-bottom: 9px;
    border: 0.5px solid rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
    gap: 13px;
}}
.rk-n {{
    font-size: 1.35rem;
    font-weight: 900;
    font-family: 'Crimson Pro', Georgia, serif;
    font-style: italic;
    color: rgba(0,0,0,0.2);
    min-width: 26px;
}}
.rk-city {{
    font-size: 0.95rem;
    font-weight: 700;
    color: {C_DARK};
}}
.rk-sub {{
    font-size: 9px;
    font-family: 'Courier New', monospace;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #aaa;
    margin-top: 2px;
}}
.rk-disp {{ font-size: 0.95rem; font-weight: 900; color: {C_DARK}; text-align: right; }}
.rk-delta {{ font-size: 10px; font-weight: 700; text-align: right; }}

/* ── Sidebar brand ──────────────────────────────────────────────────── */
.sb-logo {{
    font-size: 1.4rem;
    font-weight: 900;
    font-family: 'Crimson Pro', Georgia, serif;
    font-style: italic;
    color: {C_DARK};
    margin-bottom: 0.2rem;
}}
.sb-logo span {{ color: {C_YELLOW}; }}

/* ── Tab strip ──────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab"] {{
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SEZIONE 4 — CARICAMENTO DATI CON CACHE
# =============================================================================
# @st.cache_data dice a Streamlit:
#   "esegui questa funzione SOLO la prima volta, poi usa il risultato in cache".
# Questo evita di ricaricare il CSV a ogni interazione dell'utente.

@st.cache_data
def carica_dati_app():
    """
    Carica il dataset e aggiunge l'indice costo vita (media Italia = 100).
    Cached per evitare I/O ripetuti.
    """
    df = carica_dataset()
    # Costo vita totale mensile per un single
    df["costo_totale"] = (
        df["affitto_monolocale"]
        + df["spesa_mensile_single"]
        + df["trasporti_mensile"]
        + df["utenze_mensile"]
    )
    media_it = df["costo_totale"].mean()
    df["indice_costo"] = (df["costo_totale"] / media_it * 100).round(0).astype(int)
    return df


df_dati = carica_dati_app()


# =============================================================================
# SEZIONE 5 — FUNZIONE COLORE BARRE (classifica)
# =============================================================================

def colore_indice(idx: int) -> str:
    """
    Restituisce il colore della barra in base all'indice costo vita.
    > 110  → rosso   (città cara)
    90–110 → arancio (nella media)
    < 90   → verde   (città conveniente)
    """
    if idx > 110:
        return C_RED
    if idx > 90:
        return C_AMBER
    return C_GREEN


# =============================================================================
# SEZIONE 6 — SIDEBAR (input utente)
# =============================================================================

with st.sidebar:
    st.markdown('<div class="sb-logo">città<span>.</span></div>', unsafe_allow_html=True)
    st.caption("Calcola il tuo stipendio reale in ogni città d'Italia.")
    st.divider()

    # Slider RAL: il valore aggiorna tutta la dashboard in tempo reale
    ral = st.slider(
        "💼 RAL annua",
        min_value=15_000,
        max_value=150_000,
        value=35_000,
        step=1_000,
        format="%d €",
        help="Reddito Annuo Lordo — il lordo che trovi sul contratto di lavoro",
    )

    profilo = st.selectbox(
        "👤 Profilo familiare",
        options=["single", "coppia", "famiglia"],
        format_func=lambda x: {
            "single":   "Single",
            "coppia":   "Coppia",
            "famiglia": "Famiglia con figli",
        }[x],
    )

    # Lista città ordinata alfabeticamente
    citta_list = sorted(df_dati["capoluogo"].tolist())
    default_idx = citta_list.index("Milano") if "Milano" in citta_list else 0
    citta_attuale = st.selectbox("📍 Città attuale", options=citta_list, index=default_idx)

    with st.expander("⚙️ Dettagli avanzati"):
        figli = st.number_input("Figli a carico", min_value=0, max_value=5, value=0, step=1)
        coniuge = st.checkbox("Coniuge a carico (senza reddito)", value=False)
        tredicesima = st.radio("Mensilità", options=[13, 14], horizontal=True)

    st.divider()

    # ── Città di confronto (condivisa tra mappa e biglietto) ─────────────────
    # Usa df_dati (già in cache) — df_rank non è ancora disponibile qui
    citta_list_cfr = sorted(df_dati["capoluogo"].tolist())
    # Default: prima città alfabetica che non sia quella attuale
    def_cfr = next((c for c in citta_list_cfr if c != citta_attuale), citta_list_cfr[0])
    citta_cfr = st.selectbox(
        "🔀 Confronta con",
        options=citta_list_cfr,
        index=citta_list_cfr.index(def_cfr),
        key="confronto_citta",
        help="Città con cui vuoi confrontare il tuo stipendio disponibile. Usata nella mappa e nel biglietto.",
    )

    st.write("")
    if st.button("🎫  Crea il tuo biglietto", use_container_width=True, type="primary"):
        st.session_state["vai_biglietto"] = True

    st.divider()
    st.caption("Fonti: ISTAT · Numbeo · Immobiliare.it\nAliquote IRPEF 2024")


# =============================================================================
# SEZIONE 7 — CALCOLO PRINCIPALE
# =============================================================================
# InputAnalisi combina tutti i dati utente in un'unica struttura.
# analisi_completa() fa girare Fase 3 × 107 province + Fase 2 per ogni città.
# st.spinner mostra un messaggio mentre il calcolo è in corso.

inp = InputAnalisi(
    ral=ral,
    profilo=profilo,
    citta_attuale=citta_attuale,
    figli=figli,
    coniuge_a_carico=coniuge,
    mesi_tredicesima=tredicesima,
)

with st.spinner("Calcolo in corso..."):
    risultato = analisi_completa(inp)

# Estrae i risultati dal dizionario per usarli più facilmente
netto_att = risultato["netto_mensile_attuale"]
costo_att = risultato["costo_vita_attuale"]
disp_att  = risultato["disponibile_attuale"]
rank_att  = risultato["rank_citta_attuale"]
df_rank   = risultato["ranking"]
top5      = risultato["top5"]

# ── Variabili confronto diretto (calcolate dopo l'analisi, usate in tab3 e tab4) ──
row_cfr       = df_rank[df_rank["capoluogo"] == citta_cfr].iloc[0]
delta_cfr     = float(row_cfr["delta_mensile"])
disp_cfr      = float(row_cfr["stipendio_disponibile"])
netto_cfr     = float(row_cfr["netto_mensile"])
costo_cfr     = float(row_cfr["costo_vita_totale"])
rank_cfr      = int(row_cfr["rank"])
reg_cfr       = row_cfr["regione"]
delta_ann_cfr = float(row_cfr["delta_annuale"])
col_delta_cfr = C_GREEN if delta_cfr >= 0 else C_RED
sign_cfr      = "+" if delta_cfr >= 0 else "-"
arrow_cfr     = "↗" if delta_cfr >= 0 else "↘"


# =============================================================================
# SEZIONE 8 — HERO SECTION
# =============================================================================

st.markdown(f"""
<div class="hero">
    <p class="hero-tag">città. · maggio 2026</p>
    <h1 class="hero-h1">{citta_attuale}<br><em>ti sta rubando lo stipendio.</em></h1>
    <p class="hero-sub">
        Con una RAL di <strong>{ral:,.0f} €</strong> ti restano solo <strong>{disp_att:,.0f} €/mese</strong>
        dopo affitto, spesa, trasporti e utenze — sei al <strong>posto {rank_att}/107</strong>.
        Scopri dove puoi fare di meglio.
    </p>
    <em class="hero-brand">città.</em>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# SEZIONE 9 — METRIC CARDS (situazione attuale)
# =============================================================================
# st.columns(4) divide la riga in 4 colonne uguali.

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="mc">
        <p class="mc-lbl">Netto mensile</p>
        <p class="mc-val">€ {netto_att:,.0f}</p>
        <p class="mc-sub">su {tredicesima} mensilità</p>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="mc mc-red">
        <p class="mc-lbl">Costo vita fisso</p>
        <p class="mc-val">€ {costo_att:,.0f}</p>
        <p class="mc-sub">affitto + spesa + trasporti + utenze</p>
    </div>""", unsafe_allow_html=True)

with c3:
    # Il colore del disponibile cambia in base al valore
    cls = "mc-green" if disp_att > 600 else ("mc-yellow" if disp_att > 200 else "mc-red")
    st.markdown(f"""
    <div class="mc {cls}">
        <p class="mc-lbl">Disponibile</p>
        <p class="mc-val">€ {disp_att:,.0f}</p>
        <p class="mc-sub">€ {disp_att * 12:,.0f} l'anno</p>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="mc">
        <p class="mc-lbl">Rank nazionale</p>
        <p class="mc-val">{rank_att}<span style="font-size:.95rem;font-weight:400;color:#bbb;">/107</span></p>
        <p class="mc-sub">posizione classifica stipendio disponibile</p>
    </div>""", unsafe_allow_html=True)

st.write("")


# =============================================================================
# SEZIONE 10 — CONFRONTO DIRETTO (sempre visibile, primo contenuto della pagina)
# =============================================================================
# Questo è il cuore del progetto: mostra immediatamente cosa cambia
# nel tuo portafoglio se ti sposti in un'altra città.
# La città di confronto si sceglie dalla sidebar ("Confronta con").

st.markdown(f"""
<p class="sec-h">Il confronto <em>che conta.</em></p>
<span class="sec-sub">{citta_attuale} vs {citta_cfr} · modifica la destinazione nella sidebar</span>
""", unsafe_allow_html=True)

_ca, _cm, _cb = st.columns([5, 1, 5])

with _ca:
    st.markdown(f"""
    <div style="background:{C_DARK};border-radius:14px;padding:1.6rem 1.8rem;">
        <p style="font-size:8px;font-family:Courier New;letter-spacing:.2em;text-transform:uppercase;
                  color:rgba(255,255,255,.35);margin-bottom:6px;">SITUAZIONE ATTUALE</p>
        <p style="font-size:1.7rem;font-weight:900;color:{C_YELLOW};margin-bottom:2px;
                  font-family:'Crimson Pro',Georgia,serif;font-style:italic;">{citta_attuale}</p>
        <p style="font-size:8px;font-family:Courier New;letter-spacing:.13em;text-transform:uppercase;
                  color:rgba(255,255,255,.28);margin-bottom:20px;">{risultato["regione_attuale"]} · RANK {rank_att}/107</p>
        <div style="display:flex;gap:10px;margin-bottom:10px;">
            <div style="flex:1;background:rgba(255,255,255,.07);border-radius:9px;padding:12px 14px;">
                <p style="font-size:7.5px;font-family:Courier New;letter-spacing:.13em;
                          color:rgba(255,255,255,.35);text-transform:uppercase;margin-bottom:4px;">Netto</p>
                <p style="font-size:1.5rem;font-weight:900;color:white;margin:0;">€ {netto_att:,.0f}</p>
            </div>
            <div style="flex:1;background:rgba(255,255,255,.07);border-radius:9px;padding:12px 14px;">
                <p style="font-size:7.5px;font-family:Courier New;letter-spacing:.13em;
                          color:rgba(255,255,255,.35);text-transform:uppercase;margin-bottom:4px;">Costo vita</p>
                <p style="font-size:1.5rem;font-weight:900;color:{C_RED};margin:0;">€ {costo_att:,.0f}</p>
            </div>
        </div>
        <div style="background:rgba(255,255,255,.07);border-radius:9px;padding:14px;">
            <p style="font-size:7.5px;font-family:Courier New;letter-spacing:.13em;
                      color:rgba(255,255,255,.35);text-transform:uppercase;margin-bottom:4px;">Disponibile</p>
            <p style="font-size:2.2rem;font-weight:900;color:{C_YELLOW};margin:0;">€ {disp_att:,.0f}
                <span style="font-size:.85rem;font-weight:400;color:rgba(255,255,255,.28);">/mese</span></p>
            <p style="font-size:8px;font-family:Courier New;color:rgba(255,255,255,.28);margin-top:4px;">
                € {disp_att * 12:,.0f} l'anno</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with _cm:
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                height:100%;padding-top:95px;gap:8px;">
        <div style="font-size:2.4rem;color:{col_delta_cfr};line-height:1;">{arrow_cfr}</div>
        <div style="font-size:11px;font-weight:900;font-family:'Courier New',monospace;
                    color:{col_delta_cfr};text-align:center;line-height:1.5;">
            {sign_cfr}€&nbsp;{abs(int(delta_cfr)):,}<br>/mese
        </div>
    </div>
    """, unsafe_allow_html=True)

with _cb:
    st.markdown(f"""
    <div style="background:{C_CREAM};border:2px solid {col_delta_cfr};border-radius:14px;
                padding:1.6rem 1.8rem;">
        <p style="font-size:8px;font-family:Courier New;letter-spacing:.2em;text-transform:uppercase;
                  color:#aaa;margin-bottom:6px;">DESTINAZIONE</p>
        <p style="font-size:1.7rem;font-weight:900;color:{C_DARK};margin-bottom:2px;
                  font-family:'Crimson Pro',Georgia,serif;font-style:italic;">{citta_cfr}</p>
        <p style="font-size:8px;font-family:Courier New;letter-spacing:.13em;text-transform:uppercase;
                  color:#bbb;margin-bottom:20px;">{reg_cfr} · RANK {rank_cfr}/107</p>
        <div style="display:flex;gap:10px;margin-bottom:10px;">
            <div style="flex:1;background:rgba(0,0,0,.04);border-radius:9px;padding:12px 14px;">
                <p style="font-size:7.5px;font-family:Courier New;letter-spacing:.13em;
                          color:#aaa;text-transform:uppercase;margin-bottom:4px;">Netto</p>
                <p style="font-size:1.5rem;font-weight:900;color:{C_DARK};margin:0;">€ {netto_cfr:,.0f}</p>
            </div>
            <div style="flex:1;background:rgba(0,0,0,.04);border-radius:9px;padding:12px 14px;">
                <p style="font-size:7.5px;font-family:Courier New;letter-spacing:.13em;
                          color:#aaa;text-transform:uppercase;margin-bottom:4px;">Costo vita</p>
                <p style="font-size:1.5rem;font-weight:900;color:{C_RED};margin:0;">€ {costo_cfr:,.0f}</p>
            </div>
        </div>
        <div style="background:rgba(0,0,0,.04);border-radius:9px;padding:14px;
                    border:1px solid {col_delta_cfr}44;">
            <p style="font-size:7.5px;font-family:Courier New;letter-spacing:.13em;
                      color:#aaa;text-transform:uppercase;margin-bottom:4px;">Disponibile</p>
            <p style="font-size:2.2rem;font-weight:900;color:{col_delta_cfr};margin:0;">€ {disp_cfr:,.0f}
                <span style="font-size:.85rem;font-weight:400;color:#aaa;">/mese</span></p>
            <p style="font-size:8px;font-family:Courier New;color:#aaa;margin-top:4px;">
                {sign_cfr}€ {abs(int(delta_ann_cfr)):,} l'anno rispetto a {citta_attuale}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ── Top 5 inline (veloci da leggere) ────────────────────────────────────────
st.markdown(f'<p style="font-size:9px;font-family:Courier New;letter-spacing:.16em;text-transform:uppercase;color:#aaa;margin-bottom:8px;">Le 5 città dove il tuo stipendio vale di più</p>', unsafe_allow_html=True)
_cols = st.columns(5)
for i, city in enumerate(top5):
    _d = city["delta_mensile"]
    _s = "+" if _d >= 0 else "-"
    _c = C_GREEN if _d >= 0 else C_RED
    with _cols[i]:
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:12px 14px;border:0.5px solid rgba(0,0,0,.08);">
            <p style="font-size:8px;font-family:Courier New;letter-spacing:.1em;text-transform:uppercase;
                      color:#bbb;margin-bottom:4px;">#{int(city['rank'])}</p>
            <p style="font-size:1rem;font-weight:900;color:{C_DARK};margin-bottom:2px;
                      line-height:1.1;">{city['capoluogo']}</p>
            <p style="font-size:8px;font-family:Courier New;color:#bbb;
                      text-transform:uppercase;margin-bottom:8px;">{city['regione']}</p>
            <p style="font-size:1rem;font-weight:900;color:{_c};margin:0;">
                {_s}€ {abs(int(_d)):,}</p>
            <p style="font-size:7.5px;font-family:Courier New;color:#ccc;">/mese</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()


# =============================================================================
# SEZIONE 11 — AUTO-TRIGGER BIGLIETTO
# =============================================================================
# Se il bottone "Crea il tuo biglietto" è stato premuto:
#   1. Inietta JS che clicca il tab corretto (DOM traversal)
#   2. Dopo 600ms manda postMessage all'iframe del ticket che chiama scarica()
# st.session_state.pop() legge e cancella il flag in un colpo solo (esegue 1 volta).

if st.session_state.pop("vai_biglietto", False):
    components.html("""
    <script>
    setTimeout(function() {
        // 1. Trova e clicca il tab "Il biglietto"
        var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].textContent.toLowerCase().includes('biglietto')) {
                tabs[i].click();
                break;
            }
        }
        // 2. Dopo che il tab è visibile, manda il segnale di download a tutti gli iframe
        setTimeout(function() {
            var frames = window.parent.document.querySelectorAll('iframe');
            for (var j = 0; j < frames.length; j++) {
                try { frames[j].contentWindow.postMessage('auto_download', '*'); }
                catch(e) {}
            }
        }, 700);
    }, 150);
    </script>
    """, height=0)


# =============================================================================
# SEZIONE 12 — TAB NAVIGATION (approfondimenti)
# =============================================================================

tab1, tab2, tab3 = st.tabs(["📊  La classifica", "🗺️  La mappa", "🎫  Il biglietto"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — LA CLASSIFICA
# ─────────────────────────────────────────────────────────────────────────────

with tab1:
    st.write("")
    st.markdown("""
    <p class="sec-h">La classifica <em>completa.</em></p>
    <span class="sec-sub">indice del costo della vita · media Italia = 100</span>
    """, unsafe_allow_html=True)

    # Unisce il ranking con l'indice costo vita
    df_cls = df_rank.merge(
        df_dati[["capoluogo", "indice_costo"]],
        on="capoluogo",
        how="left",
    ).sort_values("indice_costo", ascending=False)

    df_cls["colore"] = df_cls["indice_costo"].apply(colore_indice)

    col_g, col_t = st.columns([3, 2])

    with col_g:
        # Mostra le top 20 per non affollare il grafico
        df20 = df_cls.head(20)

        fig = go.Figure()

        # Barre orizzontali colorate
        fig.add_trace(go.Bar(
            y=df20["capoluogo"],
            x=df20["indice_costo"],
            orientation="h",
            marker_color=df20["colore"].tolist(),
            text=df20["indice_costo"].astype(str),
            textposition="outside",
            textfont=dict(family="Courier New", size=11, color=C_DARK),
            hovertemplate="<b>%{y}</b><br>Indice: %{x}<extra></extra>",
        ))

        # Linea tratteggiata a 100 = media italiana
        fig.add_vline(
            x=100,
            line_dash="dash",
            line_color="rgba(0,0,0,0.2)",
            annotation_text="Media Italia",
            annotation_font=dict(family="Courier New", size=9, color="#999"),
            annotation_position="top",
        )

        # Evidenzia la città attuale se è nelle top 20
        if citta_attuale in df20["capoluogo"].values:
            fig.add_annotation(
                y=citta_attuale, x=df20[df20["capoluogo"] == citta_attuale]["indice_costo"].values[0],
                text=f" ← sei qui",
                font=dict(family="Courier New", size=10, color=C_YELLOW),
                showarrow=False,
                xanchor="left",
            )

        fig.update_layout(
            height=520,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=C_CREAM,
            margin=dict(l=0, r=70, t=10, b=20),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,0.06)",
                range=[0, df20["indice_costo"].max() * 1.18],
                tickfont=dict(family="Courier New", size=10, color="#888"),
            ),
            yaxis=dict(
                tickfont=dict(family="Inter", size=12, color=C_DARK),
                autorange="reversed",
            ),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_t:
        st.write("")

        # Sezione: le 5 più care
        st.markdown(f'<p style="font-size:10px;font-family:Courier New;letter-spacing:.14em;text-transform:uppercase;color:#aaa;margin-bottom:6px;">Le 5 più care</p>', unsafe_allow_html=True)
        for _, row in df_cls.head(5).iterrows():
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:0.5px solid rgba(0,0,0,0.07);">
                <span style="font-size:1.2rem;font-weight:900;font-family:Georgia,serif;font-style:italic;color:rgba(0,0,0,0.2);min-width:24px;">{int(row.get('rank', 1))}</span>
                <div style="flex:1;">
                    <div style="font-size:.9rem;font-weight:700;color:{C_DARK};">{row['capoluogo']}</div>
                    <div style="font-size:8.5px;font-family:Courier New;letter-spacing:.1em;text-transform:uppercase;color:#bbb;">{row['regione']} · € {row['affitto']:,.0f}/mese</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:.95rem;font-weight:900;color:{C_RED};">{row['indice_costo']}</div>
                    <div style="font-size:8px;font-family:Courier New;letter-spacing:.1em;text-transform:uppercase;color:#bbb;">INDICE</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.write("")

        # Sezione: le 5 più convenienti
        st.markdown(f'<p style="font-size:10px;font-family:Courier New;letter-spacing:.14em;text-transform:uppercase;color:#aaa;margin-bottom:6px;">Le 5 più convenienti</p>', unsafe_allow_html=True)
        for _, row in df_cls.tail(5).iloc[::-1].iterrows():
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:0.5px solid rgba(0,0,0,0.07);">
                <span style="font-size:1.2rem;font-weight:900;font-family:Georgia,serif;font-style:italic;color:rgba(0,0,0,0.2);min-width:24px;">{int(row.get('rank', 107))}</span>
                <div style="flex:1;">
                    <div style="font-size:.9rem;font-weight:700;color:{C_DARK};">{row['capoluogo']}</div>
                    <div style="font-size:8.5px;font-family:Courier New;letter-spacing:.1em;text-transform:uppercase;color:#bbb;">{row['regione']} · € {row['affitto']:,.0f}/mese</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:.95rem;font-weight:900;color:{C_GREEN};">{row['indice_costo']}</div>
                    <div style="font-size:8px;font-family:Courier New;letter-spacing:.1em;text-transform:uppercase;color:#bbb;">INDICE</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # Tabella completa scaricabile
    st.write("")
    with st.expander("📋 Mostra classifica completa (107 province)"):
        df_exp = df_cls[[
            "rank", "sigla", "capoluogo", "regione", "area",
            "indice_costo", "affitto", "costo_vita_totale",
            "stipendio_disponibile", "risparmio_annuo",
        ]].copy()
        df_exp.columns = [
            "Rank", "Sigla", "Città", "Regione", "Area",
            "Indice costo", "Affitto €", "Costo vita €",
            "Disponibile €/mese", "Risparmio €/anno",
        ]
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
        csv_bytes = df_exp.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Scarica CSV", csv_bytes, "classifica_citta.csv", "text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 (ex-tab3) — LA MAPPA INTERATTIVA
# ─────────────────────────────────────────────────────────────────────────────

with tab2:
    st.write("")
    st.markdown("""
    <p class="sec-h">La mappa <em>del tuo stipendio.</em></p>
    <span class="sec-sub">verde = guadagni di più · rosso = perdi potere d'acquisto · giallo = sei qui</span>
    """, unsafe_allow_html=True)

    # ── Prepara i dati per la mappa ──────────────────────────────────────────
    df_map = df_rank.copy()
    # Aggiunge lat/lon da dizionario; None se città non trovata
    df_map["lat"] = df_map["capoluogo"].map(lambda c: LAT_LON.get(c, (None, None))[0])
    df_map["lon"] = df_map["capoluogo"].map(lambda c: LAT_LON.get(c, (None, None))[1])
    df_map = df_map.dropna(subset=["lat", "lon"])

    # Normalizza dimensione bolla tra 10 e 28 px in base allo stipendio disponibile
    d_min = df_map["stipendio_disponibile"].min()
    d_max = df_map["stipendio_disponibile"].max()
    df_map["bsize"] = 10 + 18 * (df_map["stipendio_disponibile"] - d_min) / (d_max - d_min + 1)

    mask_att = df_map["capoluogo"] == citta_attuale
    df_alt   = df_map[~mask_att]
    df_sel   = df_map[mask_att]

    # Colorscale divergente centrata sullo zero: rosso < 0 < verde
    d_abs = max(df_alt["delta_mensile"].abs().max(), 1)

    fig_map = go.Figure()

    # ── Layer 1: tutte le province (tranne quella attuale) ───────────────────
    fig_map.add_trace(go.Scattermapbox(
        name="Province",
        lat=df_alt["lat"].tolist(),
        lon=df_alt["lon"].tolist(),
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=df_alt["bsize"].tolist(),
            color=df_alt["delta_mensile"].tolist(),
            colorscale=[
                [0.0,  C_RED],
                [0.44, "#E89E2A"],
                [0.5,  "#F2C14E"],
                [0.56, "#a8c97b"],
                [1.0,  C_GREEN],
            ],
            cmin=-d_abs,
            cmax= d_abs,
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Δ €/mese",
                    font=dict(family="Courier New", size=10, color="#888"),
                ),
                thickness=12,
                len=0.55,
                tickfont=dict(family="Courier New", size=9, color="#888"),
                x=1.01,
            ),
        ),
        customdata=df_alt[[
            "regione", "stipendio_disponibile",
            "delta_mensile", "netto_mensile",
            "costo_vita_totale", "rank",
        ]].values,
        text=df_alt["capoluogo"].tolist(),
        hovertemplate=(
            "<b>%{text}</b> · %{customdata[0]}<br>"
            "──────────────────────<br>"
            "Disponibile: <b>€ %{customdata[1]:,.0f}/mese</b><br>"
            "Netto: € %{customdata[3]:,.0f} · Costo vita: € %{customdata[4]:,.0f}<br>"
            "Rank: %{customdata[5]}/107 · "
            "Δ vs " + citta_attuale + ": <b>%{customdata[2]:+,.0f} €/mese</b>"
            "<extra></extra>"
        ),
    ))

    # ── Layer 2: città attuale (cerchio giallo grande) ───────────────────────
    if not df_sel.empty:
        r_sel = df_sel.iloc[0]
        fig_map.add_trace(go.Scattermapbox(
            name=citta_attuale,
            lat=df_sel["lat"].tolist(),
            lon=df_sel["lon"].tolist(),
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=26,
                color=C_YELLOW,
            ),
            text=[citta_attuale],
            hovertemplate=(
                f"<b>{citta_attuale}</b> · 📍 Sei qui<br>"
                f"Disponibile: <b>€ {disp_att:,.0f}/mese</b><br>"
                f"Netto: € {netto_att:,.0f} · Costo vita: € {costo_att:,.0f}<br>"
                f"Rank: {rank_att}/107"
                "<extra></extra>"
            ),
        ))

    # Centra la mappa sull'Italia con stile OpenStreetMap (nessun token richiesto)
    fig_map.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=42.0, lon=12.5),
            zoom=4.5,
        ),
        height=540,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    st.plotly_chart(fig_map, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — IL BIGLIETTO
# ─────────────────────────────────────────────────────────────────────────────

with tab3:
    st.write("")

    # ── Toggle confronto / migliore ──────────────────────────────────────────
    modo = st.radio(
        "",
        options=["confronto", "migliore"],
        format_func=lambda x: (
            f"🔀  {citta_attuale} → {citta_cfr}  (il tuo confronto)"
            if x == "confronto"
            else "🏆  Dove il tuo stipendio vale di più"
        ),
        horizontal=True,
        label_visibility="collapsed",
    )

    # ── Scegli la destinazione ───────────────────────────────────────────────
    if modo == "confronto":
        dest_cap     = citta_cfr
        dest_delta   = delta_cfr
        dest_delta_a = delta_ann_cfr
        dest_sign    = sign_cfr
        riga_dest    = trova_citta(df_dati, citta_cfr)
    else:
        if top5:
            _m           = top5[0]
            dest_cap     = _m["capoluogo"]
            dest_delta   = _m["delta_mensile"]
            dest_delta_a = _m["delta_annuale"]
            dest_sign    = "+" if dest_delta >= 0 else "-"
            riga_dest    = trova_citta(df_dati, dest_cap)
        else:
            dest_cap     = citta_cfr
            dest_delta   = delta_cfr
            dest_delta_a = delta_ann_cfr
            dest_sign    = sign_cfr
            riga_dest    = trova_citta(df_dati, citta_cfr)

    # ── Frase catchy dinamica ────────────────────────────────────────────────
    _d  = int(dest_delta)
    _mo = abs(_d)
    _yr = abs(int(dest_delta_a))

    if _d > 0:
        if _mo >= 700:
            frase = f"{citta_attuale} ti sta rubando €{_mo:,} al mese di stipendio."
        elif _mo >= 350:
            frase = f"{citta_attuale} ti sta rubando lo stipendio: €{_yr:,} l'anno in fumo."
        elif _mo >= 100:
            frase = f"{citta_attuale} ti costa cara — a {dest_cap} avresti €{_mo:,} in più al mese."
        else:
            frase = f"A {dest_cap} vivresti un po' meglio. +€{_mo:,}/mese."
    elif _d < 0:
        if _mo >= 400:
            frase = f"Attenzione: {dest_cap} ti ruberebbe €{_mo:,} in più al mese."
        elif _mo >= 150:
            frase = f"{dest_cap} è più cara di {citta_attuale}: -{_mo:,}€/mese."
        else:
            frase = f"Quasi pari. {dest_cap} ti costerebbe €{_mo:,} in più al mese."
    else:
        frase = f"{citta_attuale} e {dest_cap}: stesso potere d'acquisto."

    # ── Indici e dati per il biglietto ───────────────────────────────────────
    idx_from  = int(df_dati.loc[df_dati["capoluogo"] == citta_attuale, "indice_costo"].values[0])
    idx_to    = int(df_dati.loc[df_dati["capoluogo"] == dest_cap, "indice_costo"].values[0])
    riga_from = trova_citta(df_dati, citta_attuale)

    oggi     = datetime.now().strftime("%d.%m.%y")
    ora_     = datetime.now().strftime("%H:%M")
    seed     = int(hashlib.md5(f"{citta_attuale}{dest_cap}".encode()).hexdigest()[:4], 16)
    carrozza = str((seed % 12) + 1).zfill(2)
    posto    = str((seed % 99) + 1) + ["A", "B", "C", "D"][seed % 4]
    sf       = citta_attuale[:3].upper()
    st_code  = dest_cap[:3].upper()

    delta_color_ticket = "#3A8C52" if dest_delta >= 0 else "#CC4433"
    dest_sign_abs      = abs(int(dest_delta))
    dest_ann_abs       = abs(int(dest_delta_a))

    # ── HTML del biglietto ───────────────────────────────────────────────────
    ticket_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Courier New',Courier,monospace;}}
body{{background:#EDE8DC;padding:12px 0 0;}}
.wrap{{max-width:700px;}}

/* ── Headline frase ── */
.hl{{
  background:#0F0C08;
  color:#F2C14E;
  padding:14px 22px;
  font-family:Georgia,'Times New Roman',serif;
  font-style:italic;
  font-size:17px;
  font-weight:700;
  line-height:1.35;
  border-radius:4px 4px 0 0;
  border:1.5px solid #0F0C08;
  border-bottom:none;
}}

/* ── Biglietto ── */
.t{{display:flex;border-radius:0 0 4px 4px;overflow:hidden;border:1.5px solid #aaa;}}
.sn{{font-family:Georgia,'Times New Roman',serif!important;}}
.l{{flex:1;background:#EDE8DC;color:#1A1A1A;min-width:0;display:flex;flex-direction:column;}}
.h{{display:flex;align-items:center;gap:10px;padding:8px 18px;border-bottom:1.5px solid #1A1A1A;}}
.b{{background:#CC1414;color:#fff;font-size:9px;font-weight:bold;letter-spacing:.14em;padding:2px 7px;}}
.ht{{font-size:10px;letter-spacing:.18em;text-transform:uppercase;}}
.ro{{display:flex;align-items:flex-start;padding:14px 18px 8px;gap:8px;}}
.cb{{flex:1;min-width:0;}}
.cl{{font-size:8.5px;letter-spacing:.18em;text-transform:uppercase;color:#777;margin-bottom:3px;}}
.cn{{font-size:36px;font-weight:900;letter-spacing:-.02em;line-height:1;color:#1A1A1A;margin-bottom:4px;
     overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.cs{{font-size:8.5px;letter-spacing:.13em;text-transform:uppercase;color:#777;}}
.ar{{padding-top:20px;flex-shrink:0;font-size:18px;color:#CC1414;}}
.da{{border:none;border-top:1px dashed #999;margin:0 18px;}}
.de{{display:flex;padding:9px 18px;gap:0;border-bottom:1px dashed #aaa;}}
.di{{flex:1;border-right:1px solid #ccc;margin-right:11px;}}
.di:last-child{{border-right:none;margin-right:0;}}
.dl{{font-size:7.5px;letter-spacing:.12em;color:#888;text-transform:uppercase;margin-bottom:2px;}}
.dv{{font-size:13px;font-weight:bold;color:#1A1A1A;}}
.cp{{background:#1A1A1A;padding:12px 18px;display:flex;align-items:center;
     justify-content:space-between;gap:10px;}}
.cl2{{color:#777;font-size:8px;letter-spacing:.18em;text-transform:uppercase;margin-bottom:4px;}}
.cd{{color:#bbb;font-size:10px;}}
.ca{{text-align:right;flex-shrink:0;}}
.cm{{line-height:1;white-space:nowrap;}}
.cpfx{{font-size:20px;font-weight:bold;color:{delta_color_ticket};}}
.cnum{{font-size:42px;font-weight:900;color:{delta_color_ticket};letter-spacing:-.02em;}}
.csb{{font-size:9px;color:#777;letter-spacing:.1em;text-transform:uppercase;margin-top:3px;}}
.fi{{padding:8px 18px;font-size:7.5px;letter-spacing:.05em;text-transform:uppercase;
     color:#999;line-height:1.7;}}
.r{{width:108px;background:#CC1414;display:flex;flex-direction:column;
    align-items:center;padding:12px 9px;flex-shrink:0;}}
.co{{font-size:15px;font-weight:900;letter-spacing:.04em;color:#fff;margin-bottom:12px;text-align:center;}}
.vt{{writing-mode:vertical-rl;transform:rotate(180deg);font-size:7px;letter-spacing:.2em;
     text-transform:uppercase;color:rgba(255,255,255,.45);flex:1;text-align:center;
     line-height:1.5;overflow:hidden;}}

/* ── Download button ── */
.dl-btn{{
  display:block;width:100%;margin-top:10px;padding:11px 0;
  background:#0F0C08;color:#F2C14E;
  border:none;font-family:'Courier New',monospace;
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  cursor:pointer;border-radius:4px;
  transition:opacity .15s;
}}
.dl-btn:hover{{opacity:.8;}}
.dl-btn:disabled{{opacity:.5;cursor:default;}}
</style></head><body>
<div class="wrap">

  <!-- Frase catchy headline -->
  <div class="hl">{frase}</div>

  <!-- Biglietto -->
  <div class="t" id="ticket">
    <div class="l">
      <div class="h">
        <span class="b">CITTÀ</span>
        <span class="ht">BIGLIETTO CONFRONTO · {profilo.upper()}</span>
      </div>
      <div class="ro">
        <div class="cb">
          <div class="cl">PARTENZA</div>
          <div class="cn sn">{citta_attuale}</div>
          <div class="cs">{riga_from['regione']} · INDICE {idx_from}</div>
        </div>
        <div class="ar">→</div>
        <div class="cb" style="text-align:right">
          <div class="cl">DESTINAZIONE</div>
          <div class="cn sn">{dest_cap}</div>
          <div class="cs">{riga_dest['regione']} · INDICE {idx_to}</div>
        </div>
      </div>
      <div class="da"></div>
      <div class="de">
        <div class="di" style="flex:1.4"><div class="dl">DATA</div><div class="dv">{oggi}</div></div>
        <div class="di"><div class="dl">ORA</div><div class="dv">{ora_}</div></div>
        <div class="di" style="flex:1.2"><div class="dl">CARROZZA</div><div class="dv">{carrozza}</div></div>
        <div class="di"><div class="dl">POSTO</div><div class="dv">{posto}</div></div>
        <div class="di"><div class="dl">CLASSE</div><div class="dv">VITA</div></div>
        <div class="di"><div class="dl">RAL</div><div class="dv">€{int(ral):,}</div></div>
      </div>
      <div class="cp">
        <div>
          <div class="cl2">DIFFERENZA MENSILE</div>
          <div class="cd">netto disponibile · {citta_attuale} vs {dest_cap}</div>
        </div>
        <div class="ca">
          <div class="cm">
            <span class="cpfx">{dest_sign}€ </span><span class="cnum sn">{dest_sign_abs:,}</span>
          </div>
          <div class="csb">AL MESE · {dest_sign}€ {dest_ann_abs:,} L'ANNO</div>
        </div>
      </div>
      <div class="fi">CONDIZIONI: BAGAGLI ILLIMITATI · ANIMALI AMMESSI · NESSUN RIMBORSO IN CASO DI NOSTALGIA · ALIQUOTE IRPEF 2024 · DATI ISTAT/NUMBEO</div>
    </div>
    <div class="r">
      <div class="co sn">{sf}—{st_code}</div>
      <div class="vt">QUANTO COSTA DAVVERO VIVERE IN ITALIA · CITTÀ · QUANTO COSTA DAVVERO VIVERE IN ITALIA · CITTÀ</div>
      <svg width="88" height="40" viewBox="0 0 88 40" style="margin-top:10px;display:block;">
        <rect x="0"  y="0" width="3" height="40" fill="white"/>
        <rect x="5"  y="0" width="1" height="40" fill="white"/>
        <rect x="8"  y="0" width="2" height="40" fill="white"/>
        <rect x="12" y="0" width="1" height="40" fill="white"/>
        <rect x="15" y="0" width="3" height="40" fill="white"/>
        <rect x="20" y="0" width="1" height="40" fill="white"/>
        <rect x="23" y="0" width="2" height="40" fill="white"/>
        <rect x="28" y="0" width="1" height="40" fill="white"/>
        <rect x="31" y="0" width="3" height="40" fill="white"/>
        <rect x="36" y="0" width="1" height="40" fill="white"/>
        <rect x="39" y="0" width="2" height="40" fill="white"/>
        <rect x="43" y="0" width="1" height="40" fill="white"/>
        <rect x="47" y="0" width="3" height="40" fill="white"/>
        <rect x="52" y="0" width="2" height="40" fill="white"/>
        <rect x="56" y="0" width="1" height="40" fill="white"/>
        <rect x="59" y="0" width="3" height="40" fill="white"/>
        <rect x="64" y="0" width="1" height="40" fill="white"/>
        <rect x="67" y="0" width="2" height="40" fill="white"/>
        <rect x="71" y="0" width="1" height="40" fill="white"/>
        <rect x="74" y="0" width="3" height="40" fill="white"/>
        <rect x="79" y="0" width="2" height="40" fill="white"/>
        <rect x="83" y="0" width="1" height="40" fill="white"/>
        <rect x="86" y="0" width="2" height="40" fill="white"/>
      </svg>
    </div>
  </div>

  <!-- Download button -->
  <button class="dl-btn" id="dl-btn" onclick="scarica()">⬇ &nbsp;Scarica PNG</button>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script>
// Ascolta il segnale dal bottone sidebar
window.addEventListener('message', function(e) {{
  if (e.data === 'auto_download') scarica();
}});

function scarica() {{
  var btn = document.getElementById('dl-btn');
  btn.disabled = true;
  btn.textContent = 'Generando...';
  // Cattura headline + biglietto insieme (.wrap)
  html2canvas(document.querySelector('.wrap'), {{
    scale: 2,
    backgroundColor: '#EDE8DC',
    useCORS: true,
    ignoreElements: function(el) {{ return el.id === 'dl-btn'; }}
  }}).then(function(canvas) {{
    var link = document.createElement('a');
    link.download = 'biglietto-{sf}-{st_code}.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
    btn.disabled = false;
    btn.textContent = '⬇  Scarica PNG';
  }}).catch(function() {{
    btn.disabled = false;
    btn.textContent = '⬇  Scarica PNG';
  }});
}}
</script>
</body></html>"""

    components.html(ticket_html, height=440, scrolling=False)

    st.caption(
        f"Biglietto generato per {citta_attuale} → {dest_cap} · "
        f"RAL {int(ral):,} € · profilo {profilo}. "
        f"Clicca ⬇ Scarica PNG per salvarlo."
    )


# =============================================================================
# SEZIONE 11 — FOOTER
# =============================================================================

st.divider()
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:.3rem 0;">
    <em style="font-family:'Crimson Pro',Georgia,serif;font-size:1.1rem;font-weight:900;color:{C_DARK};">città.</em>
    <span style="font-size:9px;font-family:'Courier New',monospace;letter-spacing:.14em;text-transform:uppercase;color:#bbb;">
        FONTI: ISTAT · NUMBEO · IMMOBILIARE.IT · TARIFFA IRPEF 2024
    </span>
</div>
""", unsafe_allow_html=True)
