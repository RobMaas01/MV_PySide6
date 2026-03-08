"""
Dataverwerking voor MV3 overzichtscherm.
Zet ruwe DataStore-DataFrames om naar kant-en-klare weergave-DataFrames.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd

N_ROWS = 7
WORK_MODES = ('Flight MVKK', 'Out of area 1', 'Out of area 2', 'Out of area 3', 'BVP')
_DEFAULT_WORK_MODE = 'Flight MVKK'
_WORK_MODE_ALIASES = {
    'B1': 'Flight MVKK',
    'B2': 'Out of area 1',
    'B3': 'Out of area 2',
    'FLIGHT MVKK': 'Flight MVKK',
    'OUT OF AREA 1': 'Out of area 1',
    'OUT OF AREA 2': 'Out of area 2',
    'OUT OF AREA 3': 'Out of area 3',
    'BVP': 'BVP',
}


# ---------------------------------------------------------------------------
# Paden
# ---------------------------------------------------------------------------

def _base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


def _settings_dir() -> Path:
    return _base_dir() / 'settings'


def load_user_variables() -> dict:
    with open(_settings_dir() / 'MV_UserVariabelen.json', encoding='utf-8') as f:
        return json.load(f)


def load_system_variables() -> dict:
    with open(_settings_dir() / 'MV_SystemVariabelen.json', encoding='utf-8') as f:
        return json.load(f)


def _normalize_user(username: str | None) -> str:
    u = (username or '').strip()
    return u.lower()


def get_current_username() -> str:
    return _normalize_user(os.environ.get('USERNAME') or os.environ.get('USER') or '')


def _legacy_selected_aircraft(user_vars: dict) -> list[str]:
    heli = user_vars.get('helikopter', {})
    return sorted([k for k, v in heli.items() if v.get('Location_1', False)])


def get_work_mode(user_vars: dict, username: str | None = None) -> str:
    user_key = _normalize_user(username) or get_current_username()
    by_user = user_vars.get('work_mode_by_user', {})
    raw = str(by_user.get(user_key, _DEFAULT_WORK_MODE))
    mode = _WORK_MODE_ALIASES.get(raw.upper(), raw)
    return mode if mode in WORK_MODES else _DEFAULT_WORK_MODE


def set_work_mode(user_vars: dict, mode: str, username: str | None = None) -> str:
    user_key = _normalize_user(username) or get_current_username()
    raw = str(mode)
    mode_norm = _WORK_MODE_ALIASES.get(raw.upper(), raw)
    if mode_norm not in WORK_MODES:
        mode_norm = _DEFAULT_WORK_MODE
    by_user = user_vars.setdefault('work_mode_by_user', {})
    by_user[user_key] = mode_norm
    return mode_norm


def get_selected_aircraft(user_vars: dict,
                          username: str | None = None,
                          work_mode: str | None = None) -> list[str]:
    user_key = _normalize_user(username) or get_current_username()
    mode = set_work_mode(user_vars, work_mode or get_work_mode(user_vars, user_key), user_key)
    legacy = _legacy_selected_aircraft(user_vars)

    scope = user_vars.setdefault('overview_filters', {})
    groups = scope.setdefault('groups', {})
    bvp_by_user = scope.setdefault('bvp_by_user', {})

    if mode == 'BVP':
        selected = bvp_by_user.get(user_key)
        if not isinstance(selected, list):
            selected = list(legacy)
            bvp_by_user[user_key] = selected
        return sorted(dict.fromkeys(str(a) for a in selected))

    selected = groups.get(mode)
    # Migratiepad voor oude sleutel-namen
    if not isinstance(selected, list):
        legacy_key = {'Flight MVKK': 'B1', 'Out of area 1': 'B2', 'Out of area 2': 'B3'}.get(mode)
        if legacy_key and isinstance(groups.get(legacy_key), list):
            selected = list(groups.get(legacy_key))
            groups[mode] = selected
            del groups[legacy_key]
    if not isinstance(selected, list):
        selected = list(legacy)
        groups[mode] = selected
    return sorted(dict.fromkeys(str(a) for a in selected))


def set_selected_aircraft(user_vars: dict, selected: list[str],
                          username: str | None = None,
                          work_mode: str | None = None) -> None:
    user_key = _normalize_user(username) or get_current_username()
    mode = set_work_mode(user_vars, work_mode or get_work_mode(user_vars, user_key), user_key)
    sel = sorted(dict.fromkeys(str(a) for a in selected))

    scope = user_vars.setdefault('overview_filters', {})
    groups = scope.setdefault('groups', {})
    bvp_by_user = scope.setdefault('bvp_by_user', {})
    if mode == 'BVP':
        bvp_by_user[user_key] = sel
    else:
        groups[mode] = sel

    # legacy mirror voor backward compat / debug readability
    heli = user_vars.get('helikopter', {})
    sel_set = set(sel)
    for ac, data in heli.items():
        if isinstance(data, dict):
            data['Location_1'] = ac in sel_set


def get_hide_completed(user_vars: dict, username: str | None = None) -> bool:
    user_key = _normalize_user(username) or get_current_username()
    return bool(user_vars.get('hide_completed_by_user', {}).get(user_key, False))


def set_hide_completed(user_vars: dict, hide: bool, username: str | None = None) -> None:
    user_key = _normalize_user(username) or get_current_username()
    user_vars.setdefault('hide_completed_by_user', {})[user_key] = bool(hide)


# ---------------------------------------------------------------------------
# Statusbord
# ---------------------------------------------------------------------------

def prepare_statusbord(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df.rename(columns={
        'ID/tactisch teken': 'Aircraft',
        'PO-plan':           'POplan',
        'Ref.equipment':     'Equipment',
        'Ref.func.plaats':   'Functieplaats',
        'Restwaarde teller': 'Rest',
    }, inplace=True)
    df[['PoRef', 'PoRef Omschrijving']] = df['Tekst PO-plan'].str.split(' ', n=1, expand=True)
    df['Equipment'] = df['Equipment'].astype(str).str.strip('.0')
    df['POplan']    = df['POplan'].astype(str).str.strip('.0')
    df.dropna(subset=['Aircraft'], inplace=True)
    return df


def get_calendar_inspections(df_sb: pd.DataFrame) -> pd.DataFrame:
    df = df_sb.loc[
        df_sb['Kenmerknaam'].isnull(),
        ['Aircraft', 'Equipment', 'Functieplaats', 'POplan', 'PoRef', 'PoRef Omschrijving', 'Geplande datum']
    ].copy()
    df['Rest'] = (pd.to_datetime(df['Geplande datum']) - pd.Timestamp(date.today())).dt.days
    df['Geplande datum'] = pd.to_datetime(df['Geplande datum']).dt.strftime('%d-%m-%Y')
    df['Kenmerknaam'] = 'DAYS'
    df = (df
          .groupby(['Aircraft', 'Equipment', 'Functieplaats', 'POplan',
                    'PoRef', 'PoRef Omschrijving', 'Kenmerknaam'])[['Geplande datum', 'Rest']]
          .min()
          .reset_index()
          .sort_values('Rest'))
    return df


def get_cycle_inspections(df_sb: pd.DataFrame) -> pd.DataFrame:
    df = df_sb.dropna(subset=['Kenmerknaam']).copy()
    df = (df
          .groupby(['Aircraft', 'Equipment', 'Functieplaats', 'POplan',
                    'PoRef', 'PoRef Omschrijving', 'Kenmerknaam', 'Eenheid cyclus'])[['Rest', 'Waarde teller']]
          .min()
          .reset_index()
          .sort_values('Rest'))
    return df


def get_aircraft_list(df_sb: pd.DataFrame, user_vars: dict | None = None,
                      username: str | None = None,
                      work_mode: str | None = None) -> list:
    """Geeft gesorteerde lijst van vliegtuigen. Filtert op Location_1 als user_vars beschikbaar."""
    if user_vars:
        loc1 = get_selected_aircraft(user_vars, username=username, work_mode=work_mode)
        in_data = set(df_sb['Aircraft'].dropna().unique())
        return sorted(a for a in loc1 if a in in_data)
    return sorted(df_sb['Aircraft'].dropna().unique().tolist())


def get_ac_hrs(df_cycle: pd.DataFrame, aircraft: str, fh_poref: str) -> float:
    mask = (df_cycle['Aircraft'] == aircraft) & (df_cycle['PoRef'] == fh_poref)
    vals = df_cycle.loc[mask, 'Waarde teller']
    return float(vals.values[0]) if len(vals) > 0 else 0.0


# ---------------------------------------------------------------------------
# Configuratie
# ---------------------------------------------------------------------------

def prepare_configuratie(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    rename = {}
    for c in df.columns:
        if 'Hoogste Functieplaats' in c:
            rename[c] = 'Hoogste Functieplaats'
        elif 'Omschrijving' in c and c.startswith('Functieplaats'):
            rename[c] = 'Functieplaats_Omschrijving'
        elif c.startswith('Functieplaats') and 'Hoogste' not in c:
            rename[c] = 'Functieplaats'
        elif 'Producentcomp' in c:
            rename[c] = 'PartNumber'
    df.rename(columns=rename, inplace=True)
    if 'Hoogste Functieplaats' in df.columns:
        df['Aircraft'] = df['Hoogste Functieplaats'].apply(
            lambda x: str(x)[-4:] if pd.notna(x) else '')
    return df


def get_serienummers(aircraft: str, df_cfg: pd.DataFrame, sys_vars: dict) -> pd.DataFrame:
    components = sys_vars.get('SerieNummers', {})
    cfg = df_cfg.loc[df_cfg['Aircraft'] == aircraft, ['Functie-ID', 'Serienummer']]
    rows = []
    for component, functie_id in components.items():
        match = cfg.loc[cfg['Functie-ID'] == functie_id, 'Serienummer']
        rows.append({'Component': component, 'Serienummer': match.values[0] if len(match) else ''})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tellerstanden
# ---------------------------------------------------------------------------

_UNIT_MAP = {'Hours': 'UUR', 'Meter': 'M', 'Cycle': 'ST'}


def get_tellerstanden(aircraft: str, df_cycle: pd.DataFrame, sys_vars: dict) -> pd.DataFrame:
    kenmerken = sys_vars.get('Kenmerken', {})
    kenmerken = dict(list(kenmerken.items())[:7])   # eerste 7 (niet motorspecifiek)
    usage = df_cycle.loc[df_cycle['Aircraft'] == aircraft,
                         ['PoRef', 'Waarde teller', 'Eenheid cyclus']]
    rows = []
    for name, (poref, unit_type) in kenmerken.items():
        cycle_unit = _UNIT_MAP.get(unit_type, '')
        mask = (usage['PoRef'] == poref) & (usage['Eenheid cyclus'] == cycle_unit)
        vals = usage.loc[mask, 'Waarde teller']
        rows.append({'Type': name, 'Waarde': str(vals.values[0]) if len(vals) else '', 'Eenheid': unit_type})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ECU
# ---------------------------------------------------------------------------

def get_ecu_status(aircraft: str, ecu_nr: str, df_cycle: pd.DataFrame, sys_vars: dict) -> pd.DataFrame:
    """ECU inspections gefilterd op Functieplaats (N721 = ECU 1, N722 = ECU 2)."""
    fp_filter = f'N72{ecu_nr}'
    engine_groups = sys_vars.get('Engine', {})

    ecu_df = df_cycle[
        (df_cycle['Aircraft'] == aircraft) &
        df_cycle['Functieplaats'].str.contains(fp_filter, na=False)
    ][['PoRef', 'PoRef Omschrijving', 'Waarde teller', 'Rest']].copy()

    poref_to_group: dict = {}
    for group, porefs in engine_groups.items():
        for poref in porefs:
            poref_to_group[poref] = group

    ecu_df['Groep'] = ecu_df['PoRef'].map(poref_to_group).fillna('')
    ecu_df['Omschrijving'] = ecu_df['PoRef Omschrijving'].str.split('/').str[-1].str.strip()
    return ecu_df[['Groep', 'PoRef', 'Omschrijving', 'Waarde teller', 'Rest']].reset_index(drop=True)


def get_ecu_serienumber(aircraft: str, ecu_nr: str, df_cfg: pd.DataFrame) -> str:
    """Geeft het serienummer van ECU 1 (N721) of ECU 2 (N722)."""
    fp = f'NH90_{aircraft}_N72{ecu_nr}'
    match = df_cfg.loc[df_cfg['Functieplaats'] == fp, 'Serienummer']
    return str(match.values[0]) if len(match) else 'niet gevonden'


def save_user_variables(user_vars: dict) -> None:
    """Slaat user variabelen op naar MV_UserVariabelen.json.

    Raakt last_change.txt NIET aan — gebruikersinstellingen (heli-selectie,
    bijzonderheden, completed-inspections) zijn lokaal en triggeren geen
    overview-refresh bij andere gebruikers.
    """
    path = _settings_dir() / 'MV_UserVariabelen.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(user_vars, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Bijzonderheden
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# wijzigingsflag (last_change.txt)
# ---------------------------------------------------------------------------

_meta_path: Path | None = None


def _get_meta_path() -> Path:
    global _meta_path
    if _meta_path is None:
        _meta_path = _settings_dir() / 'last_change.txt'
    return _meta_path


def touch_meta() -> None:
    """Maak (of update) het "last_change" bestand.

    Het bestand bevat geen inhoud; we updaten alleen de modificatietijd.
    """
    p = _get_meta_path()
    p.parent.mkdir(exist_ok=True)
    # schrijf lege inhoud en zet mtime op nu
    p.write_text('')


def last_meta() -> float:
    """Retourneer de modificatietijd van de flag, of 0 als niet aanwezig."""
    try:
        return _get_meta_path().stat().st_mtime
    except FileNotFoundError:
        return 0.0


def get_bijzonderheden(aircraft: str, user_vars: dict, sys_vars: dict,
                       df_cycle: pd.DataFrame) -> pd.DataFrame:
    heli      = user_vars.get('helikopter', {}).get(aircraft, {})
    bijz      = heli.get('InspBijzonderheden', {})
    kenmerken = sys_vars.get('Kenmerken', {})
    usage     = df_cycle.loc[df_cycle['Aircraft'] == aircraft,
                              ['PoRef', 'Waarde teller', 'Eenheid cyclus']]
    rows = []
    for _, item in bijz.items():
        beschr       = item.get('Bijzonderheid', '')
        due_date     = item.get('DueDate', '')
        eenheid      = item.get('Eenheid', '')
        po_plan      = item.get('PoPlan', '')
        uitvoeren_bij = item.get('UitvoerenBij', '')

        rest = ''
        eenheid_display = eenheid

        if due_date:
            try:
                d = pd.to_datetime(due_date, dayfirst=True)
                rest = (d - pd.Timestamp(date.today())).days
                eenheid_display = 'Dagen'
            except Exception:
                pass
        elif uitvoeren_bij and eenheid and eenheid in kenmerken:
            try:
                poref, unit_type = kenmerken[eenheid]
                cycle_unit = _UNIT_MAP.get(unit_type, '')
                mask = (usage['PoRef'] == poref) & (usage['Eenheid cyclus'] == cycle_unit)
                vals = usage.loc[mask, 'Waarde teller']
                if len(vals):
                    current = float(str(vals.values[0]).replace(',', '.'))
                    target  = float(uitvoeren_bij.replace(',', '.'))
                    rest = round(target - current, 1)
            except Exception:
                pass

        rows.append({'Bijzonderheid': beschr, 'PoPlan': po_plan,
                     'Rest': rest, 'Eenheid': eenheid_display})
    return pd.DataFrame(rows)
