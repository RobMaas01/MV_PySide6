"""
DataStore voor MV3.
Laadt alle Excel-data eenmalig in RAM na het inloggen.
Tabs lezen uit store.data.<naam> — geen directe bestandstoegang vanuit de UI.
"""
import json
import logging
import sys
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


def _base_dir() -> Path:
    """Projectroot in dev-modus; _internal/ map in frozen exe."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent   # MV_PySide6/


def _settings_file() -> Path:
    """app_settings.json in settings/ naast de EXE (frozen) of in settings/ (dev)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'settings' / 'app_settings.json'
    return _base_dir() / 'settings' / 'app_settings.json'


def _data_folder() -> Path:
    """
    Map met xlsx-bestanden.
    Leest 'data_folder' uit app_settings.json; valt terug op data/ in projectroot.
    """
    sf = _settings_file()
    if sf.exists():
        with open(sf, encoding='utf-8') as f:
            folder = json.load(f).get('data_folder', '')
        if folder:
            return Path(folder)
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'data'
    return _base_dir() / 'data'


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
        """Laad alle bronnen en retourneer een gevulde DataStore."""
        store  = cls()
        folder = _data_folder()

        store.statusbord   = store._load_excel(folder / 'statusbord.xlsx',   'statusbord',
                                               converters={'CyclusPOpakk': str})
        store.configuratie = store._load_excel(folder / 'configuratie.xlsx', 'configuratie',
                                               sheet_name='Basislijst',
                                               converters={'Equipment': str, 'Bovenligg.equipment': str})
        store.mis          = store._load_excel(folder / 'mis.xlsx',          'mis',
                                               sheet_name='ZZ_MIS')
        store.three_ms     = store._load_excel(folder / '3ms.xlsx',          '3ms')

        ok  = [k for k in ('statusbord', 'configuratie', 'mis', '3ms') if k not in store.load_errors]
        err = list(store.load_errors.keys())
        log.info('DataStore geladen — OK: %s  Fouten: %s', ok, err)
        return store

    def _load_excel(self, path: Path, key: str, **kwargs) -> pd.DataFrame | None:
        try:
            df = pd.read_excel(path, **kwargs)
            log.info('  v %s  (%d rijen)', key, len(df))
            return df
        except Exception as exc:
            self.load_errors[key] = str(exc)
            log.warning('  x %s: %s', key, exc)
            return None


# Module-niveau singleton — wordt gezet vanuit main.py na login
data: DataStore | None = None
