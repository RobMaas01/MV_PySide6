"""
Pad-configuratie voor MV3.

Leest mv_config.ini naast de exe (frozen) of projectroot (dev).
Als het bestand niet bestaat, wordt het aangemaakt met standaardwaarden.

Voorbeeld mv_config.ini:
    [paths]
    internal   = _internal
    datasource = datasource
    settings   = settings

Waarden mogen absoluut zijn of relatief (relatief = ten opzichte van de exe-map).
"""
import configparser
import os
import sys
from pathlib import Path


def _exe_dir() -> Path:
    """Map waar de exe (of main.py in dev) staat."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent  # MV_PySide6/


_CONFIG_FILE = 'mv_config.ini'
_DEFAULTS = {
    'internal':   '_internal',
    'datasource': 'datasource',
    'settings':   'settings',
}

_COMMENT = (
    '# MV3 pad-configuratie\n'
    '# Paden mogen absoluut zijn of relatief t.o.v. de exe-map.\n'
    '# Voorbeeld absoluut: datasource = C:\\Gedeeld\\MV_data\\datasource\n\n'
)


def _config_path() -> Path:
    return _exe_dir() / _CONFIG_FILE


def _load_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    p = _config_path()
    if not p.exists():
        cfg['paths'] = _DEFAULTS
        with open(p, 'w', encoding='utf-8') as f:
            f.write(_COMMENT)
            cfg.write(f)
    else:
        cfg.read(p, encoding='utf-8')
        if 'paths' not in cfg:
            cfg['paths'] = {}
        for key, default in _DEFAULTS.items():
            if key not in cfg['paths']:
                cfg['paths'][key] = default
    return cfg


def _resolve(raw: str) -> Path:
    """Absoluut pad direct teruggeven; relatief pad koppelen aan exe-map."""
    p = Path(raw)
    if p.is_absolute():
        return p
    return _exe_dir() / p


# ---------------------------------------------------------------------------
# Lazy-loaded singleton
# ---------------------------------------------------------------------------

_cfg: configparser.ConfigParser | None = None


def _get_cfg() -> configparser.ConfigParser:
    global _cfg
    if _cfg is None:
        _cfg = _load_config()
    return _cfg


# ---------------------------------------------------------------------------
# Publieke API
# ---------------------------------------------------------------------------

def get_internal_dir() -> Path:
    """_internal map — PyInstaller bundled bestanden (DLLs, modules)."""
    if getattr(sys, 'frozen', False):
        raw = _get_cfg()['paths'].get('internal', _DEFAULTS['internal'])
        return _resolve(raw)
    return Path(getattr(sys, '_MEIPASS', str(_exe_dir() / '_internal')))


def get_datasource_dir() -> Path:
    """Datasource map — xlsx-bestanden en mv_data.db."""
    env = os.environ.get('MV3_DATASOURCE', '').strip()
    if env:
        p = Path(env)
    else:
        raw = _get_cfg()['paths'].get('datasource', _DEFAULTS['datasource'])
        p = _resolve(raw)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_settings_dir() -> Path:
    """Settings map — JSON gebruikers- en systeemvariabelen."""
    env = os.environ.get('MV3_SETTINGS', '').strip()
    if env:
        p = Path(env)
    else:
        raw = _get_cfg()['paths'].get('settings', _DEFAULTS['settings'])
        p = _resolve(raw)
    p.mkdir(parents=True, exist_ok=True)
    return p
