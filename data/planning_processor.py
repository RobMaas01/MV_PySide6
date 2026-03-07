"""
Businesslogica voor de planningsmodule.
Combineert kalender- en cyclusinspecties en filtert op gebruikersinvoer.
Gebruikt de al ingeladen DataFrames van DataStore (geen directe bestandstoegang).
"""
import pandas as pd


def get_usage_items(sys_vars: dict) -> pd.DataFrame:
    """Levert de rijen voor de 'beoogd gebruik'-tabel (inSAP=True, viewID>0)."""
    items = sys_vars.get('GlimsCycles', {})
    df = pd.DataFrame.from_dict(items, orient='index')
    df = df.loc[(df['inSAP'] == True) & (df['viewID'] > 0)].sort_values('viewID')
    df = df[['kenmerk', 'relation', 'ratio']].reset_index(drop=True)
    df['gebruik'] = None
    return df


def calculate_usage(df_usage: pd.DataFrame, flight_hours, weeks_aboard) -> pd.DataFrame:
    """Berekent beoogd gebruik op basis van vluchturen en weken aan boord."""
    df = df_usage.copy()
    for i, row in df.iterrows():
        ratio = row['ratio']
        if ratio in (None, ''):
            continue
        try:
            ratio = float(ratio)
        except (ValueError, TypeError):
            continue
        if row['relation'] == 'FH' and flight_hours is not None:
            df.at[i, 'gebruik'] = round(float(flight_hours) * ratio, 2)
        elif row['relation'] == 'week a/b' and weeks_aboard is not None:
            df.at[i, 'gebruik'] = round(float(weeks_aboard) * ratio, 2)
    return df


def get_planning_inspections(
    aircraft: str,
    planning_date: str | None,
    planning_hours: float | None,
    flat_usage: dict,
    df_cal: pd.DataFrame,
    df_cyc: pd.DataFrame,
) -> pd.DataFrame:
    """
    Geeft gefilterde inspecties terug voor de Planning-tab.
    Als geen filters actief zijn, worden alle inspecties getoond.
    """
    any_filter = bool(
        planning_date or planning_hours or
        any(v is not None for v in flat_usage.values())
    )

    # --- Kalenderinspecties ---
    cal = df_cal.loc[df_cal['Aircraft'] == aircraft].copy()
    cal['Geplande datum_dt'] = pd.to_datetime(
        cal['Geplande datum'], format='%d-%m-%Y', errors='coerce'
    )
    cal['show'] = False
    if planning_date:
        cal['show'] = cal['Geplande datum_dt'] < pd.to_datetime(planning_date)

    # --- Cyclusinspecties ---
    cyc = df_cyc.loc[df_cyc['Aircraft'] == aircraft].copy()
    cyc['Geplande datum'] = ''
    cyc['show'] = False

    if planning_hours is not None:
        cyc['show'] |= (
            cyc['Kenmerknaam'] == 'FLIGHT_HOURS'
        ) & (cyc['Rest'] < planning_hours)

    for kenmerk, usage in flat_usage.items():
        if usage is not None:
            cyc['show'] |= (cyc['Kenmerknaam'] == kenmerk) & (cyc['Rest'] < usage)

    combined = pd.concat([cal, cyc], ignore_index=True)

    if any_filter:
        combined = combined.loc[combined['show']]

    combined['Type'] = combined['PoRef Omschrijving'].apply(
        lambda x: 'Insp' if isinstance(x, str) and x.startswith('I') else 'Vervang'
    )
    combined.rename(columns={'PoRef Omschrijving': 'Omschrijving'}, inplace=True)
    combined = combined.sort_values('Rest')

    columns = ['Aircraft', 'POplan', 'Type', 'PoRef', 'Omschrijving',
               'Geplande datum', 'Rest', 'Kenmerknaam']
    available = [c for c in columns if c in combined.columns]
    return combined[available].reset_index(drop=True)
