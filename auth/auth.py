"""
Authenticatie voor MV3 (PySide6).
Leest wachtwoorden en gebruikers uit de gedeelde JSON-instellingen van MV2.
Geen Flask-sessies — login wordt bijgehouden als variabele in de applicatie.
"""
import sys
import json
from datetime import datetime
from pathlib import Path

# sys.frozen = True wanneer gebundeld als PyInstaller exe
if getattr(sys, 'frozen', False):
    _BASE = Path(sys._MEIPASS)          # _internal/ map naast de exe
else:
    _BASE = Path(__file__).parent.parent

_SETTINGS_DIR = _BASE / 'settings'
_SYS_FILE  = _SETTINGS_DIR / 'MV_SystemVariabelen.json'
_USER_FILE = _SETTINGS_DIR / 'MV_UserVariabelen.json'


def _load(path: Path) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _save(path: Path, data: dict) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_credentials(username: str, password: str) -> bool:
    """Valideert gebruikersnaam en wachtwoord."""
    passwords = _load(_SYS_FILE).get('Passwords', {})
    return passwords.get(username) == password


def ensure_user_exists(username: str) -> None:
    """Registreert een nieuwe gebruiker als deze nog niet bestaat."""
    data = _load(_USER_FILE)
    if username not in data['user']:
        data['user'][username] = {
            'lastLogIn':   datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'logInCounts': 1,
            'Location':    1,
            'Helikopter':  ['N088'],
        }
        _save(_USER_FILE, data)
