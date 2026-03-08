"""
Settings-tab voor MV3.
Toont informatie over de applicatie en de architectuur.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ui.theme import SLATE_400, SLATE_600, SLATE_700, SLATE_800, SLATE_900, WHITE


_SECTION_QSS = f"""
    QFrame#section {{
        background-color: {SLATE_800};
        border-radius: 10px;
        border: 1px solid {SLATE_700};
    }}
    QLabel  {{ background: transparent; color: {WHITE}; }}
"""

_DIVIDER_QSS = f'background: {SLATE_700}; border: none; max-height: 1px;'


class SettingsTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f'QScrollArea {{ background: {SLATE_900}; border: none; }}')
        scroll.viewport().setStyleSheet(f'background: {SLATE_900};')

        content = QWidget()
        content.setStyleSheet(f'background: {SLATE_900};')

        col = QHBoxLayout(content)
        col.setContentsMargins(24, 20, 24, 20)
        col.setSpacing(24)
        col.setAlignment(Qt.AlignmentFlag.AlignTop)

        left = QVBoxLayout()
        left.setSpacing(20)
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        right = QVBoxLayout()
        right.setSpacing(20)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        # -- Sectie: Over deze applicatie ------------------------------
        about_section = QFrame()
        about_section.setObjectName('section')
        about_section.setStyleSheet(_SECTION_QSS)
        about_section.setFixedWidth(640)

        va = QVBoxLayout(about_section)
        va.setContentsMargins(18, 14, 18, 18)
        va.setSpacing(0)

        ta = QLabel('About this application')
        ta.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;')
        va.addWidget(ta)
        va.addSpacing(10)

        diva = QFrame(); diva.setFixedHeight(1); diva.setStyleSheet(_DIVIDER_QSS)
        va.addWidget(diva)
        va.addSpacing(10)

        desc = QLabel(
            '<b>Maintenance Viewer (MV3)</b> is een desktop applicatie voor het bewaken van de '
            'onderhoudsstatus van NH90 helikopters van de Koninklijke Marine.<br><br>'
            '<b>Interne database</b><br>'
            'De app werkt met een eigen lokale database (<code>mv_data.db</code>). '
            'Alle schermen lezen uitsluitend uit deze database — er is geen directe SAP-koppeling. '
            'Dit maakt de app stabiel en volledig offline bruikbaar, ook zonder netwerkverbinding.<br><br>'
            '<b>Dagelijkse update — statusbord</b><br>'
            'Het statusbord wordt dagelijks als Excel-bestand uit SAP geëxporteerd. '
            'Via de knop op de Home-tab wordt dit bestand ingeladen en opgeslagen in de interne database. '
            'Voor een actueel beeld is een dagelijkse import gewenst.<br><br>'
            '<b>Overige tabellen — eenmalig geladen</b><br>'
            'Tabellen zoals de configuratie, MIS-data en 3MS-gegevens zijn momenteel eenmalig ingeladen. '
            'In de toekomst wordt hiervoor een automatische synchronisatie ontwikkeld via een centrale '
            'PostgreSQL-database, die enkele keren per week wordt gevoed met verse SAP-data. '
            'Naast de onderhoudsdata bevat deze database ook CAMO-gerelateerde tabellen. '
            'Een periodieke sync — streeffrequentie 2x per week — vervangt dan het handmatig laden.<br><br>'
            '<b>Tabs:</b><br>'
            '&nbsp;&nbsp;• <b>Home</b> — statistieken, helikopterselectie en statusbord importeren<br>'
            '&nbsp;&nbsp;• <b>Overview</b> — actuele onderhoudsstatus per helikopter<br>'
            '&nbsp;&nbsp;• <b>Planning</b> — komende inspecties; exporteren naar Excel<br>'
            '&nbsp;&nbsp;• <b>Configuration / Part. insp. / MIS</b> — in ontwikkeling<br>'
            '&nbsp;&nbsp;• <b>Info</b> — dit scherm'
        )
        desc.setStyleSheet(f'font-size: 12px; color: {SLATE_400}; background: transparent; line-height: 1.6;')
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.TextFormat.RichText)
        va.addWidget(desc)

        left.addWidget(about_section)

        # -- Sectie: Architectuur --------------------------------------
        arch_section = QFrame()
        arch_section.setObjectName('section')
        arch_section.setStyleSheet(_SECTION_QSS)
        arch_section.setFixedWidth(640)

        vb = QVBoxLayout(arch_section)
        vb.setContentsMargins(18, 14, 18, 18)
        vb.setSpacing(0)

        tb = QLabel('Architecture')
        tb.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;')
        vb.addWidget(tb)
        vb.addSpacing(10)

        divb = QFrame(); divb.setFixedHeight(1); divb.setStyleSheet(_DIVIDER_QSS)
        vb.addWidget(divb)
        vb.addSpacing(10)

        arch = QLabel(
            '<b>Opstarten</b><br>'
            'Bij start laadt <code>main.py</code> het hoofdvenster en haalt de data op in de achtergrond, '
            'zodat de app direct reageert.<br><br>'
            '<b>Data</b> &nbsp;<code>data/</code><br>'
            '&nbsp;&nbsp;• <code>database.py</code> — lezen en schrijven van de SQLite-database<br>'
            '&nbsp;&nbsp;• <code>loader.py</code> — haalt data op in een achtergrond-thread<br>'
            '&nbsp;&nbsp;• <code>store.py</code> — laadt alle tabellen in geheugen als DataFrames<br>'
            '&nbsp;&nbsp;• <code>processor.py</code> — berekeningen: inspecties filteren en splitsen<br><br>'
            '<b>Schermen</b> &nbsp;<code>ui/</code><br>'
            '&nbsp;&nbsp;• <code>home_tab.py</code> — statistieken, helikopterselectie, import<br>'
            '&nbsp;&nbsp;• <code>overview_tab.py</code> — onderhoudsstatus per helikopter<br>'
            '&nbsp;&nbsp;• <code>planning_tab.py</code> — planningsoverzicht, export naar Excel<br>'
            '&nbsp;&nbsp;• <code>settings_tab.py</code> — dit scherm<br><br>'
            '<b>Databron</b> &nbsp;<code>datasource/mv_data.db</code><br>'
            'Lokale SQLite-database. Excel dient alleen als importmechanisme via de Home-tab.'
        )
        arch.setStyleSheet(f'font-size: 12px; color: {SLATE_400}; background: transparent; line-height: 1.6;')
        arch.setWordWrap(True)
        arch.setTextFormat(Qt.TextFormat.RichText)
        vb.addWidget(arch)

        left.addWidget(arch_section)

        # -- Sectie: Developer notes -----------------------------------
        dev_section = QFrame()
        dev_section.setObjectName('section')
        dev_section.setStyleSheet(_SECTION_QSS)
        dev_section.setFixedWidth(820)

        vc = QVBoxLayout(dev_section)
        vc.setContentsMargins(18, 14, 18, 18)
        vc.setSpacing(0)

        tc = QLabel('Developer Notes')
        tc.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;')
        vc.addWidget(tc)
        vc.addSpacing(10)

        divc = QFrame(); divc.setFixedHeight(1); divc.setStyleSheet(_DIVIDER_QSS)
        vc.addWidget(divc)
        vc.addSpacing(10)

        dev = QLabel(
            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">STACK</span><br>'
            '<span style="color:#e2e8f0;">Python 3.12 &nbsp;·&nbsp; PySide6 (Qt6) &nbsp;·&nbsp; pandas &nbsp;·&nbsp; SQLite &nbsp;·&nbsp; openpyxl</span><br>'
            '<span style="color:#64748b; font-size:11px;">Vereist: pip install pyside6 pandas openpyxl. Geen extra Qt-installatie nodig.<br>'
            'Kan worden gebundeld als standalone executable via PyInstaller — '
            '<span style="color:#94a3b8; font-family:monospace;">_base_dir()</span> detecteert frozen-modus automatisch.</span>'
            '<br><br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">INSTELLINGEN</span>'
            '&nbsp;&nbsp;<span style="color:#64748b; font-size:10px;">settings/</span><br>'
            '<table cellspacing="0" cellpadding="0" style="margin-top:4px;">'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; vertical-align:top;">MV_UserVariabelen.json</td>'
            '<td style="color:#94a3b8; font-size:11px; vertical-align:top;">'
            'Per gebruiker (Windows USERNAME): geselecteerde helis per work_mode, bijzonderheden per heli, login-teller.<br>'
            '<span style="color:#64748b;">Wordt geschreven door de app — niet handmatig aanpassen tijdens een actieve sessie.</span>'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">MV_SystemVariabelen.json</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Vaste applicatie-constanten: Kenmerken (PoRef + eenheid per teller), GlimsCycles (inspectie-definities), '
            'Engine-groepen (motor-PoRefs), SerieNummers (Functie-IDs).<br>'
            '<span style="color:#64748b;">Aanpassen alleen bij structurele SAP-wijzigingen.</span>'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">last_change.txt</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Wijzigingsflag (mtime-check). Wordt aangeraakt na statusbord-import zodat de meta-watcher '
            'een refresh triggert. Niet aangeraakt bij filter-saves — anders zou elke helikopter-selectie '
            'een onnodige overview-refresh veroorzaken.'
            '</td></tr>'
            '</table>'
            '<br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">REFRESH-KETEN</span><br>'
            '<span style="color:#e2e8f0; font-family:monospace; font-size:11px;">DataLoader (thread) &rarr; DataStore (DataFrames) &rarr; on_data_loaded &rarr; tabs</span><br>'
            '<span style="color:#94a3b8; font-size:11px;">'
            'Bij opstarten laadt <span style="color:#7dd3fc; font-family:monospace;">DataLoader</span> alle SQLite-tabellen in een achtergrond-thread '
            'zodat de UI direct reageert. Na laden wordt <span style="color:#7dd3fc; font-family:monospace;">on_data_loaded</span> aangeroepen '
            'en worden alle tabs gevuld.<br>'
            'Filter-saves (helikopterselectie, locatie) sturen <span style="color:#7dd3fc; font-family:monospace;">settings_saved</span> '
            '→ <span style="font-family:monospace;">_refresh_overview()</span> ververst alleen de Overview-tab — geen herlaad van SQLite.<br>'
            'De Planning-tab ververst alleen bij tab-wissel (lazy load).<br>'
            'De meta-watcher (<span style="font-family:monospace;">_check_for_updates</span>) pollt elke 2 sec op '
            '<span style="color:#7dd3fc; font-family:monospace;">last_change.txt</span> — bij wijziging volgt een volledige overview-refresh '
            '(bijv. na statusbord-import door een andere gebruiker).<br>'
            'Na statusbord-import: <span style="color:#7dd3fc; font-family:monospace;">import_completed</span> '
            '→ <span style="font-family:monospace;">_reload_data()</span> → nieuwe DataLoader-thread → '
            'volledige SQLite-herlaad → <span style="font-family:monospace;">on_data_loaded</span> → alle tabs ververst. '
            '<span style="color:#64748b;">last_change.txt wordt aangeraakt zodat andere openstaande sessies de wijziging oppikken.</span>'
            '</span>'
            '<br><br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">WORK MODES</span><br>'
            '<span style="color:#94a3b8; font-size:11px;">Vijf modi bepalen welke helikopters in de Overview zichtbaar zijn.<br>'
            'De username wordt opgehaald uit de Windows-omgevingsvariabele <span style="color:#7dd3fc; font-family:monospace;">USERNAME</span>.</span><br>'
            '<table cellspacing="0" cellpadding="0" style="margin-top:4px;">'
            '<tr><td style="color:#7dd3fc; font-size:11px; white-space:nowrap; padding-right:14px; vertical-align:top;">Flight MVKK<br>Out of area 1–3</td>'
            '<td style="color:#94a3b8; font-size:11px; vertical-align:top;">'
            'Gedeeld per groep — alle gebruikers zien dezelfde selectie.<br>'
            'Opgeslagen: <span style="font-family:monospace;">overview_filters.groups[mode]</span>'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">BVP</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Persoonlijk — elke gebruiker heeft een eigen selectie.<br>'
            'Opgeslagen: <span style="font-family:monospace;">overview_filters.bvp_by_user[username]</span>'
            '</td></tr>'
            '</table>'
            '<br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">BEREKENINGEN</span>'
            '&nbsp;&nbsp;<span style="color:#64748b; font-size:10px;">data/processor.py</span><br>'
            '<span style="color:#94a3b8; font-size:11px;">Het ruwe SAP-export DataFrame doorloopt een vaste verwerkingsketen vóór weergave.</span><br>'
            '<table cellspacing="0" cellpadding="0" style="margin-top:4px;">'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; vertical-align:top;">prepare_statusbord</td>'
            '<td style="color:#94a3b8; font-size:11px; vertical-align:top;">'
            'Normaliseert kolomnamen, splitst <span style="font-family:monospace;">Tekst PO-plan</span> → '
            '<span style="font-family:monospace;">PoRef</span> + omschrijving, verwijdert rijen zonder Aircraft.'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">get_calendar_inspections</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Kalender-inspecties: rijen zonder Kenmerknaam. '
            '<span style="font-family:monospace;">Rest</span> = (Geplande datum − vandaag) in dagen. '
            'Per PO-plan wordt de vroegste datum gekozen.'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">get_cycle_inspections</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Cyclus-inspecties: rijen mét Kenmerknaam (uren, cycles, meters). '
            '<span style="font-family:monospace;">Rest</span> = resterende eenheden tot ingreep. '
            'Per PO-plan + Kenmerknaam wordt het minimum gekozen.'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">get_bijzonderheden</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Combineert handmatige invoer (user_vars) met live tellerstanden. '
            'Rest via datum → dagen; rest via <span style="font-family:monospace;">UitvoerenBij</span> → '
            'doelwaarde − huidige tellerstand (eenheid uit Kenmerken).'
            '</td></tr>'
            '</table>'
        )
        dev.setStyleSheet(f'font-size: 12px; color: {SLATE_400}; background: transparent; line-height: 1.5;')
        dev.setWordWrap(True)
        dev.setTextFormat(Qt.TextFormat.RichText)
        vc.addWidget(dev)

        right.addWidget(dev_section)
        right.addStretch()

        disclaimer = QLabel('This Info screen was AI-generated and may contain errors.')
        disclaimer.setStyleSheet(
            f'font-size: 11px; color: {SLATE_600}; background: transparent;'
        )
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left.addStretch()
        left.addWidget(disclaimer)

        col.addLayout(left)
        col.addLayout(right)

        scroll.setWidget(content)
        outer.addWidget(scroll)
