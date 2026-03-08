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

        ta = QLabel('Over deze applicatie')
        ta.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;')
        va.addWidget(ta)
        va.addSpacing(10)

        diva = QFrame()
        diva.setFixedHeight(1)
        diva.setStyleSheet(_DIVIDER_QSS)
        va.addWidget(diva)
        va.addSpacing(10)

        desc = QLabel(
            '<b>Maintenance Viewer (MV3)</b> is een desktop-app voor het monitoren van de '
            'onderhoudsstatus van NH90-helikopters van de Koninklijke Marine.<br><br>'
            '<b>Lokale database</b><br>'
            'De applicatie werkt met een lokale SQLite-database: <code>datasource/mv_data.db</code>. '
            'Alle schermen lezen uit deze database. Daardoor blijft de app snel, stabiel en bruikbaar zonder netwerk.<br><br>'
            '<b>Dagelijkse werkwijze</b><br>'
            'Het statusbord wordt als Excel-bestand uit SAP aangeleverd en via de Home-tab geimporteerd. '
            'Na een succesvolle import worden relevante tabellen opnieuw geladen zodat Overview en Planning direct met actuele data werken.<br><br>'
            '<b>Databronnen</b><br>'
            'Statusbord-data verandert doorgaans dagelijks. Overige bronnen (zoals configuratie, MIS en 3MS) '
            'wijzigen minder vaak en worden periodiek ververst.<br><br>'
            '<b>Tab-overzicht</b><br>'
            '&nbsp;&nbsp;&bull; <b>Home</b> - statistieken, locatie, helikopterselectie en import<br>'
            '&nbsp;&nbsp;&bull; <b>Overview</b> - actuele onderhoudsstatus per helikopter<br>'
            '&nbsp;&nbsp;&bull; <b>Planning</b> - komende inspecties en export naar Excel<br>'
            '&nbsp;&nbsp;&bull; <b>Configuration / Part. insp. / MIS</b> - in ontwikkeling<br>'
            '&nbsp;&nbsp;&bull; <b>Info</b> - technische en functionele toelichting'
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

        tb = QLabel('Architectuur')
        tb.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;')
        vb.addWidget(tb)
        vb.addSpacing(10)

        divb = QFrame()
        divb.setFixedHeight(1)
        divb.setStyleSheet(_DIVIDER_QSS)
        vb.addWidget(divb)
        vb.addSpacing(10)

        arch = QLabel(
            '<b>Opstartpad</b><br>'
            '<code>main.py</code> start de Qt-app, toont het hoofdvenster en start een laadthread. '
            'Daarmee blijft de UI responsief tijdens het inlezen van data.<br><br>'
            '<b>Data-laag</b> &nbsp;<code>data/</code><br>'
            '&nbsp;&nbsp;&bull; <code>database.py</code> - SQLite I/O en Excel-import<br>'
            '&nbsp;&nbsp;&bull; <code>loader.py</code> - achtergrondladen van DataStore<br>'
            '&nbsp;&nbsp;&bull; <code>store.py</code> - centrale in-memory DataFrames<br>'
            '&nbsp;&nbsp;&bull; <code>processor.py</code> - transformaties, domeinlogica en JSON-state beheer<br>'
            '&nbsp;&nbsp;&bull; <code>planning_processor.py</code> - berekeningslogica voor de Planning-tab<br><br>'
            '<b>Service-laag</b> &nbsp;<code>data/</code><br>'
            '&nbsp;&nbsp;&bull; <code>app_state_service.py</code> - ontkoppelt UI van directe processor-aanroepen; '
            'centraliseert lezen en schrijven van user/system state<br><br>'
            '<b>UI-laag</b> &nbsp;<code>ui/</code><br>'
            '&nbsp;&nbsp;&bull; <code>main_window.py</code> - orchestratie van tabs, caching en refresh<br>'
            '&nbsp;&nbsp;&bull; <code>home_tab.py</code> - import en gebruikersfilters<br>'
            '&nbsp;&nbsp;&bull; <code>overview_tab.py</code> - onderhoudsoverzicht per helikopter<br>'
            '&nbsp;&nbsp;&bull; <code>planning_tab.py</code> - vooruitblik en export<br>'
            '&nbsp;&nbsp;&bull; <code>settings_tab.py</code> - dit documentatiescherm<br><br>'
            '<b>Databron</b><br>'
            'Primaire runtime-bron: <code>datasource/mv_data.db</code> (SQLite). Excel is alleen importinput.'
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

        divc = QFrame()
        divc.setFixedHeight(1)
        divc.setStyleSheet(_DIVIDER_QSS)
        vc.addWidget(divc)
        vc.addSpacing(10)

        dev = QLabel(
            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">STACK</span><br>'
            '<span style="color:#e2e8f0;">Python 3.12 &nbsp;&middot;&nbsp; PySide6 (Qt6) &nbsp;&middot;&nbsp; pandas &nbsp;&middot;&nbsp; SQLite &nbsp;&middot;&nbsp; openpyxl</span><br>'
            '<span style="color:#64748b; font-size:11px;">Installatie: <code>pip install pyside6 pandas openpyxl</code>. '
            'Deploy mogelijk via PyInstaller.</span>'
            '<br><br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">INSTELLINGEN</span>'
            '&nbsp;&nbsp;<span style="color:#64748b; font-size:10px;">settings/</span><br>'
            '<table cellspacing="0" cellpadding="0" style="margin-top:4px;">'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; vertical-align:top;">MV_UserVariabelen.json</td>'
            '<td style="color:#94a3b8; font-size:11px; vertical-align:top;">'
            'Gebruikersinstellingen: work mode, helikopterselectie, bijzonderheden en user-specifieke flags.<br>'
            '<span style="color:#64748b;">Schrijfoperaties verlopen atomisch via een tijdelijk .tmp-bestand en worden gesynchroniseerd '
            'via een .lock-bestand. Handmatig aanpassen tijdens runtime wordt afgeraden.</span>'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">MV_UserVariabelen.lock</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Tijdelijk vergrendelingsbestand. Aangemaakt tijdens een schrijfoperatie, direct daarna verwijderd. '
            '<span style="color:#64748b;">Staat het bestand er na een crash nog? Dan verwijdert de app het na 5 seconden automatisch.</span>'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">MV_SystemVariabelen.json</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Systeemconfiguratie: kenmerken, cycles, engine-groepen en serievelden.'
            '</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">last_change.txt</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">'
            'Wijzigingsvlag op basis van mtime. Na import wordt deze aangeraakt zodat open sessies herladen.'
            '</td></tr>'
            '</table>'
            '<br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">REFRESH-KETEN</span><br>'
            '<span style="color:#e2e8f0; font-family:monospace; font-size:11px;">DataLoader &rarr; DataStore &rarr; on_data_loaded &rarr; tabs</span><br>'
            '<span style="color:#94a3b8; font-size:11px;">'
            'Bij opstart laadt DataLoader de tabellen in een thread, waarna caches in MainWindow worden opgebouwd.<br>'
            'Filterwijzigingen verversen alleen benodigde UI-delen. Volledige herlaad gebeurt alleen na import of meta-change.'
            '</span>'
            '<br><br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">WORK MODES</span><br>'
            '<span style="color:#94a3b8; font-size:11px;">'
            'Flight MVKK en Out of area 1-3 zijn gedeelde selecties. '
            'BVP is user-specifiek (per Windows-gebruiker).'
            '</span>'
            '<br><br>'

            '<span style="color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:1px;">BELANGRIJKE BEREKENINGEN</span>'
            '&nbsp;&nbsp;<span style="color:#64748b; font-size:10px;">data/processor.py</span><br>'
            '<table cellspacing="0" cellpadding="0" style="margin-top:4px;">'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; vertical-align:top;">prepare_statusbord</td>'
            '<td style="color:#94a3b8; font-size:11px; vertical-align:top;">Normaliseert kolommen en splitst PO-teksten naar referentie plus omschrijving.</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">get_calendar_inspections</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">Berekent kalender-inspecties en restdagen op basis van geplande datum.</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">get_cycle_inspections</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">Berekent cycle-inspecties en minimale restwaarden per kenmerk.</td></tr>'
            '<tr><td style="color:#7dd3fc; font-family:monospace; font-size:11px; white-space:nowrap; padding-right:14px; padding-top:6px; vertical-align:top;">get_bijzonderheden</td>'
            '<td style="color:#94a3b8; font-size:11px; padding-top:6px; vertical-align:top;">Combineert handmatige invoer met actuele tellerstanden voor operationele restwaarden.</td></tr>'
            '</table>'
        )
        dev.setStyleSheet(f'font-size: 12px; color: {SLATE_400}; background: transparent; line-height: 1.5;')
        dev.setWordWrap(True)
        dev.setTextFormat(Qt.TextFormat.RichText)
        vc.addWidget(dev)

        right.addWidget(dev_section)
        right.addStretch()

        disclaimer = QLabel('Deze Info-tab is technisch documentatief en kan na codewijzigingen verouderde details bevatten.')
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
