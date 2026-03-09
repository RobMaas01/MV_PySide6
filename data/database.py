"""
SQLite database-laag voor MV3.

Alle data die voorheen direct uit Excel werd gelezen,
wordt nu via SQLite opgehaald. Excel dient alleen nog
als importmechanisme.

Tabel-namen komen overeen met de oorspronkelijke Excel-bestandsnamen:
  statusbord, configuratie, mis, 3ms
"""
import logging
import sqlite3
import sys
from pathlib import Path

import pandas as pd
# used to mark data changes so other instances can reload
def _flag_touch():
    try:
        from data.processor import touch_meta
        touch_meta()
    except Exception:
        pass


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database-pad
# ---------------------------------------------------------------------------

def db_path() -> Path:
    """
    Dev:    <projectroot>/datasource/mv_data.db
    Frozen: <exe_dir>/datasource/mv_data.db  (gedeelde map, zelfde voor alle gebruikers)
    """
    if getattr(sys, 'frozen', False):
        root = Path(sys.executable).parent
    else:
        root = Path(__file__).parent.parent
    p = root / 'datasource'
    p.mkdir(parents=True, exist_ok=True)
    return p / 'mv_data.db'


# ---------------------------------------------------------------------------
# Connectie
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(str(db_path()))


def table_exists(table_name: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Generieke import: Excel → SQLite
# ---------------------------------------------------------------------------

def import_excel_to_table(path: Path, table_name: str, **read_kwargs) -> tuple[int, str | None]:
    """
    Leest een Excel-bestand en schrijft alle rijen naar een SQLite-tabel.
    Datum-kolommen worden omgezet naar ISO-string (YYYY-MM-DD).

    Geeft (aantal_rijen, None) bij succes, of (0, foutmelding) bij mislukking.
    """
    try:
        df = pd.read_excel(path, **read_kwargs)
    except Exception as exc:
        return 0, f'Could not read file: {exc}'

    _normalize_dates(df)

    conn = get_connection()
    try:
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        log.info('Geïmporteerd: %s → %s (%d rijen)', path.name, table_name, len(df))
        return len(df), None
    except Exception as exc:
        return 0, str(exc)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Laden: SQLite → DataFrame
# ---------------------------------------------------------------------------

def load_table(table_name: str) -> pd.DataFrame | None:
    """Laad een volledige SQLite-tabel als DataFrame. Geeft None bij fout."""
    if not table_exists(table_name):
        return None
    conn = get_connection()
    try:
        df = pd.read_sql(f'SELECT * FROM "{table_name}"', conn)
        log.info('Geladen uit SQLite: %s (%d rijen)', table_name, len(df))
        return df
    except Exception as exc:
        log.warning('Laden mislukt voor %s: %s', table_name, exc)
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Statusbord: validatie + specifieke import
# ---------------------------------------------------------------------------

_REQUIRED_STATUSBORD_COLS = {
    'ID/tactisch teken',
    'PO-plan',
    'Tekst PO-plan',
    'Ref.equipment',
    'Ref.func.plaats',
    'Restwaarde teller',
}


def import_statusbord(path: Path) -> dict:
    """
    Importeer statusbord.xlsx naar SQLite na kolomvalidatie.
    Stappen: lees + valideer → kopieer naar datasource/ → schrijf naar SQLite.

    Geeft een dict terug:
      {'rows': int, 'previous': int, 'error': str | None, 'copied_to': str}
    """
    try:
        df = pd.read_excel(path, converters={'CyclusPOpakk': str})
    except Exception as exc:
        return {'rows': 0, 'previous': 0, 'error': f'Could not read file: {exc}', 'copied_to': ''}

    missing = _REQUIRED_STATUSBORD_COLS - set(df.columns)
    if missing:
        return {
            'rows': 0,
            'previous': 0,
            'error': f'Required columns are missing: {", ".join(sorted(missing))}',
            'copied_to': '',
        }

    # Kopieer het bronbestand naar de datasource-map
    dest_dir = db_path().parent
    dest_file = dest_dir / 'statusbord.xlsx'
    try:
        shutil.copy2(path, dest_file)
        log.info('Statusbord gekopieerd naar %s', dest_file)
    except Exception as exc:
        return {'rows': 0, 'previous': 0, 'error': f'Copy failed: {exc}', 'copied_to': ''}

    _normalize_dates(df)

    conn = get_connection()
    try:
        previous = 0
        if table_exists('statusbord'):
            previous = conn.execute('SELECT COUNT(*) FROM statusbord').fetchone()[0]

        df.to_sql('statusbord', conn, if_exists='replace', index=False)
        log.info('Statusbord geïmporteerd: %d rijen (was %d)', len(df), previous)
        # update flag after successful import
        _flag_touch()
        return {'rows': len(df), 'previous': previous, 'error': None, 'copied_to': str(dest_file)}
    except Exception as exc:
        return {'rows': 0, 'previous': 0, 'error': str(exc), 'copied_to': ''}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------

def _normalize_dates(df: pd.DataFrame) -> None:
    """Zet datetime-kolommen om naar ISO-string zodat SQLite ze correct opslaat."""
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
