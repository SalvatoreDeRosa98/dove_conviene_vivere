"""
Fase 2 - Struttura dati per il progetto:
"Dove conviene vivere con il mio stipendio?"

Questo script crea la base dati territoriale ufficiale partendo dal file ISTAT
dei comuni italiani. L'obiettivo non e' ancora stimare affitti e costo vita, ma
preparare una tabella province pulita e pronta per essere arricchita.
"""

from pathlib import Path

import pandas as pd


SOURCE_URL = "https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.xlsx"
PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
RAW_FILE = RAW_DIR / "istat_elenco_comuni_italiani.xlsx"
OUTPUT_FILE = PROCESSED_DIR / "province_base.csv"


COLUMNS = {
    "codice_uts": "Codice dell'Unità territoriale sovracomunale \n(valida a fini statistici)",
    "provincia": "Denominazione dell'Unità territoriale sovracomunale \n(valida a fini statistici)",
    "regione": "Denominazione Regione",
    "sigla": "Sigla automobilistica",
    "tipologia_uts": "Tipologia di Unità territoriale sovracomunale ",
    "ripartizione": "Ripartizione geografica",
}

TIPOLOGIA_UTS = {
    1: "Provincia",
    2: "Provincia autonoma",
    3: "Citta metropolitana",
    4: "Libero consorzio comunale",
    5: "Ente di decentramento regionale",
}

SIGLE_MANUALI = {
    "Napoli": "NA",
}


def prepara_cartelle() -> None:
    """Crea le cartelle data/raw e data/processed se non esistono."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def scarica_file_istat() -> None:
    """Scarica il file ISTAT solo se non e' gia' presente in data/raw."""
    if RAW_FILE.exists():
        print(f"File ISTAT gia' presente: {RAW_FILE}")
        return

    print("Scarico il file ISTAT ufficiale...")
    df = pd.read_excel(SOURCE_URL)
    df.to_excel(RAW_FILE, index=False)
    print(f"File salvato in: {RAW_FILE}")


def carica_comuni() -> pd.DataFrame:
    """Legge il file ISTAT dei comuni italiani."""
    return pd.read_excel(RAW_FILE)


def costruisci_tabella_province(comuni: pd.DataFrame) -> pd.DataFrame:
    """Estrae una riga per ogni provincia o unita' territoriale sovracomunale."""
    province = comuni[list(COLUMNS.values())].drop_duplicates().copy()
    province = province.rename(columns={v: k for k, v in COLUMNS.items()})
    province["sigla"] = province["sigla"].fillna(province["provincia"].map(SIGLE_MANUALI))
    province["tipologia_uts_nome"] = province["tipologia_uts"].map(TIPOLOGIA_UTS)

    province = province.sort_values(["regione", "provincia"]).reset_index(drop=True)

    province["affitto_mensile_monolocale"] = pd.NA
    province["affitto_mensile_bilocale"] = pd.NA
    province["costo_vita_single"] = pd.NA
    province["costo_vita_coppia"] = pd.NA
    province["costo_vita_famiglia"] = pd.NA
    province["stipendio_medio_lordo"] = pd.NA
    province["fonte_affitto"] = pd.NA
    province["fonte_costo_vita"] = pd.NA
    province["fonte_stipendio"] = pd.NA

    ordine_colonne = [
        "codice_uts",
        "provincia",
        "sigla",
        "regione",
        "ripartizione",
        "tipologia_uts",
        "tipologia_uts_nome",
        "affitto_mensile_monolocale",
        "affitto_mensile_bilocale",
        "costo_vita_single",
        "costo_vita_coppia",
        "costo_vita_famiglia",
        "stipendio_medio_lordo",
        "fonte_affitto",
        "fonte_costo_vita",
        "fonte_stipendio",
    ]
    return province[ordine_colonne]


def salva_tabella(province: pd.DataFrame) -> None:
    """Salva la tabella province in formato CSV."""
    province.to_csv(OUTPUT_FILE, index=False)


def stampa_riepilogo(province: pd.DataFrame) -> None:
    """Stampa un riepilogo veloce per controllare che la pipeline funzioni."""
    print("\nFase 2 completata.")
    print(f"Province/unita' territoriali trovate: {len(province)}")
    print(f"Regioni coperte: {province['regione'].nunique()}")
    print(f"Output CSV: {OUTPUT_FILE}")
    print("\nPrime 5 righe:")
    print(province.head().to_string(index=False))


def main() -> None:
    """Esegue tutta la pipeline della Fase 2."""
    prepara_cartelle()
    scarica_file_istat()
    comuni = carica_comuni()
    province = costruisci_tabella_province(comuni)
    salva_tabella(province)
    stampa_riepilogo(province)


if __name__ == "__main__":
    main()
