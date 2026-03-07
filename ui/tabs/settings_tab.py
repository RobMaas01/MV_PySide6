"""
Settings-tab voor MV3.
Toont informatie over de applicatie en de architectuur.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget,
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

        col = QVBoxLayout(content)
        col.setContentsMargins(24, 20, 24, 20)
        col.setSpacing(20)
        col.setAlignment(Qt.AlignmentFlag.AlignTop)

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

        col.addWidget(about_section)

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

        col.addWidget(arch_section)

        col.addStretch()

        disclaimer = QLabel('This Info screen was AI-generated and may contain errors.')
        disclaimer.setStyleSheet(
            f'font-size: 11px; color: {SLATE_600}; background: transparent;'
        )
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignLeft)
        col.addWidget(disclaimer)

        scroll.setWidget(content)
        outer.addWidget(scroll)
