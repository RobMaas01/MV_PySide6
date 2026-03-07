"""
DataStore voor MV3.
Laadt alle data eenmalig in RAM na het inloggen.

Data-bron: lokale SQLite-database (mv_data.db).
Bij eerste start worden de Excel-bestanden automatisch geïmporteerd
in SQLite (eenmalige migratie). Daarna leest de app uitsluitend uit SQLite.

Tabs lezen uit store.data.<naam> — geen directe bestandstoegang vanuit de UI.
"""
import logging
import sys
from pathlib import Path

import json
import pandas as pd

log = logging.getLogger(__name__)


def _base_dir() -> Path:
    """Projectroot in dev-modus; _internal/ map in frozen exe."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent   # MV_PySide6/


def _settings_file() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'settings' / 'app_settings.json'
    return _base_dir() / 'settings' / 'app_settings.json'


def _data_folder() -> Path:
    """
    Map met xlsx-bestanden (gebruikt voor eenmalige auto-migratie naar SQLite).
    Leest 'data_folder' uit app_settings.json; valt terug op data/ in projectroot.
    """
    sf = _settings_file()
    if sf.exists():
        with open(sf, encoding='utf-8') as f:
            folder = json.load(f).get('data_folder', '')
        if folder:
            return Path(folder)
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'datasource'
    return _base_dir() / 'data'


# ---------------------------------------------------------------------------
# Bronnen: (attr, tabel, excel-pad, excel-kwargs)
# ---------------------------------------------------------------------------

def _sources(folder: Path) -> list[tuple]:
    return [
        ('statusbord',   'statusbord',   folder / 'statusbord.xlsx',
         {'converters': {'CyclusPOpakk': str}}),
        ('configuratie', 'configuratie', folder / 'configuratie.xlsx',
         {'sheet_name': 'Basislijst',
          'converters': {'Equipment': str, 'Bovenligg.equipment': str}}),
        ('mis',          'mis',          folder / 'mis.xlsx',
         {'sheet_name': 'ZZ_MIS'}),
        ('three_ms',     '3ms',          folder / '3ms.xlsx',
         {}),
    ]


class DataStore:
    """
    Centrale data-container. Aanmaken via DataStore.load().
    Attributen zijn pandas DataFrames (of None bij laadfouten).
    """

    def __init__(self):
        self.statusbord:    pd.DataFrame | None = None
        self.configuratie:  pd.DataFrame | None = None
        self.mis:           pd.DataFrame | None = None
        self.three_ms:      pd.DataFrame | None = None

        self.load_errors: dict[str, str] = {}

    @classmethod
    def load(cls) -> 'DataStore':
        """
        Laad alle databronnen vanuit SQLite.
        Als een tabel nog niet in SQLite staat, wordt het bijbehorende
        Excel-bestand automatisch geïmporteerd (eenmalige migratie).
        """
        from data.database import table_exists, load_table, import_excel_to_table

        store  = cls()
        folder = _data_folder()

        for attr, table, excel_path, excel_kwargs in _sources(folder):
            if not table_exists(table):
                # Tabel bestaat nog niet → probeer auto-import vanuit Excel
                if excel_path.exists():
                    n, err = import_excel_to_table(excel_path, table, **excel_kwargs)
                    if err:
                        store.load_errors[table] = f'Auto-import mislukt: {err}'
                        log.warning('  x %s: %s', table, err)
                        continue
                    log.info('  ↑ Auto-migratie: %s → SQLite (%d rijen)', table, n)
                else:
                    store.load_errors[table] = (
                        'Niet in SQLite en Excel niet gevonden: '
                        + str(excel_path)
                    )
                    log.warning('  x %s: geen SQLite-data en Excel niet gevonden', table)
                    continue

            df = load_table(table)
            if df is not None:
                setattr(store, attr, df)
                log.info('  v %s  (%d rijen)', table, len(df))
            else:
                store.load_errors[table] = 'Laden uit SQLite mislukt'
                log.warning('  x %s: SQLite-laden mislukt', table)

        ok  = [k for k in ('statusbord', 'configuratie', 'mis', '3ms')
               if k not in store.load_errors]
        err = list(store.load_errors.keys())
        log.info('DataStore geladen — OK: %s  Fouten: %s', ok, err)
        return store


# Module-niveau singleton — wordt gezet vanuit main.py na login
data: DataStore | None = None
