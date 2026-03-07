"""
Settings-tab voor MV3.
Beheert app-instellingen zoals automatisch inloggen en de data-map.
app_settings.json staat naast de EXE (of in settings/ tijdens development).
"""
import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from ui.theme import (
    BTN_PRIMARY_QSS, INPUT_QSS,
    SLATE_400, SLATE_600, SLATE_700, SLATE_800, SLATE_900, WHITE,
)


def _settings_file() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'settings' / 'app_settings.json'
    return Path(__file__).parent.parent.parent / 'settings' / 'app_settings.json'


_SETTINGS_FILE = _settings_file()

_GREEN = '#4ade80'

_SECTION_QSS = f"""
    QFrame#section {{
        background-color: {SLATE_800};
        border-radius: 10px;
        border: 1px solid {SLATE_700};
    }}
    QLabel  {{ background: transparent; color: {WHITE}; }}
    QCheckBox {{
        background: transparent;
        color: {WHITE};
        font-size: 13px;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {SLATE_600};
        background: {SLATE_900};
    }}
    QCheckBox::indicator:checked {{
        background: #1d4ed8;
        border: 1px solid #3b82f6;
        image: none;
    }}
"""

_DIVIDER_QSS = f'background: {SLATE_700}; border: none; max-height: 1px;'


def load_app_settings() -> dict:
    if _SETTINGS_FILE.exists():
        with open(_SETTINGS_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {'skip_login': False, 'auto_username': '', 'data_folder': ''}


def save_app_settings(settings: dict) -> None:
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f'font-size: 12px; color: {SLATE_400}; background: transparent;')
    return lbl


class SettingsTab(QWidget):
    settings_saved   = Signal()
    import_completed = Signal()   # emitted na succesvolle data-import

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f'QScrollArea {{ background: {SLATE_900}; border: none; }}')
        scroll.viewport().setStyleSheet(f'background: {SLATE_900};')

        content = QWidget()
        content.setStyleSheet(f'background: {SLATE_900};')

        # Twee kolommen: links instellingen, rechts beschrijving
        root = QHBoxLayout(content)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        right_col = QVBoxLayout()
        right_col.setSpacing(20)
        right_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        root.addLayout(left_col)
        root.addLayout(right_col)

        # -- Sectie: Inloggen ------------------------------------------
        login_section = QFrame()
        login_section.setObjectName('section')
        login_section.setStyleSheet(_SECTION_QSS)
        login_section.setFixedWidth(380)

        v = QVBoxLayout(login_section)
        v.setContentsMargins(18, 14, 18, 18)
        v.setSpacing(0)

        title = QLabel('Login')
        title.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;')
        v.addWidget(title)
        v.addSpacing(10)

        div = QFrame(); div.setFixedHeight(1); div.setStyleSheet(_DIVIDER_QSS)
        v.addWidget(div)
        v.addSpacing(12)

        self._skip_cb = QCheckBox('Skip login screen')
        self._skip_cb.stateChanged.connect(self._on_change)
        v.addWidget(self._skip_cb)
        v.addSpacing(12)

        v.addWidget(_lbl('Automatic user'))
        v.addSpacing(4)
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText('username')
        self._user_edit.setStyleSheet(INPUT_QSS)
        self._user_edit.setFixedHeight(32)
        self._user_edit.textChanged.connect(self._on_change)
        v.addWidget(self._user_edit)

        left_col.addWidget(login_section)

        # -- Sectie: Data map ------------------------------------------
        data_section = QFrame()
        data_section.setObjectName('section')
        data_section.setStyleSheet(_SECTION_QSS)
        data_section.setFixedWidth(380)

        v2 = QVBoxLayout(data_section)
        v2.setContentsMargins(18, 14, 18, 18)
        v2.setSpacing(0)

        title2 = QLabel('Data files')
        title2.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;')
        v2.addWidget(title2)
        v2.addSpacing(10)

        div2 = QFrame(); div2.setFixedHeight(1); div2.setStyleSheet(_DIVIDER_QSS)
        v2.addWidget(div2)
        v2.addSpacing(12)

        v2.addWidget(_lbl('Folder with xlsx files'))
        v2.addSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(6)
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText('path to folder...')
        self._folder_edit.setStyleSheet(INPUT_QSS)
        self._folder_edit.setFixedHeight(32)
        self._folder_edit.textChanged.connect(self._on_change)
        row.addWidget(self._folder_edit)

        browse_btn = QPushButton('...')
        browse_btn.setFixedSize(32, 32)
        browse_btn.setStyleSheet(BTN_PRIMARY_QSS)
        browse_btn.clicked.connect(self._browse_folder)
        row.addWidget(browse_btn)
        v2.addLayout(row)

        left_col.addWidget(data_section)

        # -- Sectie: Data importeren -----------------------------------
        import_section = QFrame()
        import_section.setObjectName('section')
        import_section.setStyleSheet(_SECTION_QSS)
        import_section.setFixedWidth(380)

        vi = QVBoxLayout(import_section)
        vi.setContentsMargins(18, 14, 18, 18)
        vi.setSpacing(0)

        title_i = QLabel('Data importeren')
        title_i.setStyleSheet(
            f'font-size: 13px; font-weight: bold; color: {WHITE}; background: transparent;'
        )
        vi.addWidget(title_i)
        vi.addSpacing(10)

        div_i = QFrame()
        div_i.setFixedHeight(1)
        div_i.setStyleSheet(_DIVIDER_QSS)
        vi.addWidget(div_i)
        vi.addSpacing(12)

        vi.addWidget(_lbl('Importeer statusbord.xlsx naar de lokale database'))
        vi.addSpacing(8)

        self._import_btn = QPushButton('Statusbord importeren')
        self._import_btn.setStyleSheet(BTN_PRIMARY_QSS)
        self._import_btn.setFixedHeight(32)
        self._import_btn.clicked.connect(self._import_statusbord)
        vi.addWidget(self._import_btn)
        vi.addSpacing(8)

        self._import_status = QLabel('')
        self._import_status.setStyleSheet(
            f'font-size: 11px; color: {_GREEN}; background: transparent;'
        )
        self._import_status.setWordWrap(True)
        vi.addWidget(self._import_status)

        left_col.addWidget(import_section)

        # -- Opslaan ---------------------------------------------------
        btn = QPushButton('Opslaan')
        btn.setStyleSheet(BTN_PRIMARY_QSS)
        btn.setFixedWidth(100)
        btn.setFixedHeight(32)
        btn.clicked.connect(self._save)

        self._status_lbl = QLabel('')
        self._status_lbl.setStyleSheet(f'font-size: 11px; color: {_GREEN}; background: transparent;')

        left_col.addWidget(btn)
        left_col.addWidget(self._status_lbl)

        # -- Sectie: Over deze applicatie ------------------------------
        about_section = QFrame()
        about_section.setObjectName('section')
        about_section.setStyleSheet(_SECTION_QSS)
        about_section.setFixedWidth(600)

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
            '<b>Maintenance Viewer (MV)</b> is een desktopapplicatie voor het inzichtelijk '
            'maken van onderhoudsdata van de NH90-helikopter. De app leest Excel-bestanden '
            'in (statusbord, configuratie, MIS, 3MS) en toont deze gestructureerd in '
            'meerdere tabbladen.<br><br>'
            'Tabs:<br>'
            '&nbsp;&nbsp;• <b>Overzicht</b> — actuele status per toestel en inspectie<br>'
            '&nbsp;&nbsp;• <b>Planning</b> — kalender- en cyclusgerelateerde inspecties; exporteer naar Excel<br>'
            '&nbsp;&nbsp;• <b>Configuratie</b> — basislijst van equipment<br>'
            '&nbsp;&nbsp;• <b>Part. insp.</b> — partnummer-gebaseerde inspecties<br>'
            '&nbsp;&nbsp;• <b>MIS</b> — MIS-rapportage<br>'
            '&nbsp;&nbsp;• <b>Settings</b> — app-instellingen (beveiligd met wachtwoord)'
        )
        desc.setStyleSheet(f'font-size: 12px; color: {SLATE_400}; background: transparent; line-height: 1.6;')
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.TextFormat.RichText)
        va.addWidget(desc)

        right_col.addWidget(about_section)

        # -- Sectie: Architectuur --------------------------------------
        arch_section = QFrame()
        arch_section.setObjectName('section')
        arch_section.setStyleSheet(_SECTION_QSS)
        arch_section.setFixedWidth(600)

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
            '<b>Gelaagde opbouw (3 lagen):</b><br><br>'
            '<b>1. Entry point</b> &nbsp;<code>main.py</code><br>'
            '&nbsp;&nbsp;&nbsp;Start de Qt-applicatie, beheert de login-loop en '
            'lanceert de DataLoader in een achtergrond-thread.<br><br>'
            '<b>2. Data-laag</b> &nbsp;<code>data/</code><br>'
            '&nbsp;&nbsp;&nbsp;• <code>loader.py</code> — QThread die DataStore.load() aanroept zonder de UI te blokkeren<br>'
            '&nbsp;&nbsp;&nbsp;• <code>store.py</code> — DataStore laadt alle xlsx-bestanden eenmalig in RAM (pandas DataFrames)<br>'
            '&nbsp;&nbsp;&nbsp;• <code>processor.py</code> — berekeningen op de DataFrames (statusbord, kalender, cycli, vliegtuiglijst)<br>'
            '&nbsp;&nbsp;&nbsp;• <code>variables.py</code> — systeem- en gebruikersvariabelen<br><br>'
            '<b>3. UI-laag</b> &nbsp;<code>ui/</code><br>'
            '&nbsp;&nbsp;&nbsp;• <code>main_window.py</code> — QMainWindow met QTabWidget, corner-widget en statusbalk<br>'
            '&nbsp;&nbsp;&nbsp;• <code>login_dialog.py</code> — inlogvenster met wachtwoordcontrole<br>'
            '&nbsp;&nbsp;&nbsp;• <code>tabs/overview_tab.py</code> — overzichtstabel per toestel<br>'
            '&nbsp;&nbsp;&nbsp;• <code>tabs/planning_tab.py</code> — planningsoverzicht + Excel-export<br>'
            '&nbsp;&nbsp;&nbsp;• <code>tabs/settings_tab.py</code> — dit scherm<br>'
            '&nbsp;&nbsp;&nbsp;• <code>theme.py</code> — centrale kleur- en stijldefinities (Slate-palette)<br><br>'
            '<b>Instellingen</b> &nbsp;<code>settings/app_settings.json</code><br>'
            '&nbsp;&nbsp;&nbsp;Sla inlogscherm over, automatische gebruiker en data-map. '
            'Staat naast de EXE (productie) of in <code>settings/</code> (ontwikkeling).<br><br>'
            '<b>Data-bronnen</b> (xlsx-bestanden in geconfigureerde map):<br>'
            '&nbsp;&nbsp;&nbsp;<code>statusbord.xlsx</code> &nbsp;·&nbsp; '
            '<code>configuratie.xlsx</code> &nbsp;·&nbsp; '
            '<code>mis.xlsx</code> &nbsp;·&nbsp; '
            '<code>3ms.xlsx</code>'
        )
        arch.setStyleSheet(f'font-size: 12px; color: {SLATE_400}; background: transparent; line-height: 1.6;')
        arch.setWordWrap(True)
        arch.setTextFormat(Qt.TextFormat.RichText)
        vb.addWidget(arch)

        right_col.addWidget(arch_section)
        right_col.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _import_statusbord(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, 'Selecteer statusbord.xlsx', '', 'Excel bestanden (*.xlsx *.xls)'
        )
        if not path:
            return

        from pathlib import Path
        from data.database import import_statusbord

        self._import_btn.setEnabled(False)
        self._import_status.setStyleSheet(
            f'font-size: 11px; color: #94a3b8; background: transparent;'
        )
        self._import_status.setText('Bezig met importeren...')

        result = import_statusbord(Path(path))

        self._import_btn.setEnabled(True)

        if result['error']:
            self._import_status.setStyleSheet(
                'font-size: 11px; color: #f87171; background: transparent;'
            )
            self._import_status.setText(f'Fout: {result["error"]}')
            QMessageBox.warning(
                self, 'Import mislukt',
                f'Statusbord kon niet worden geïmporteerd:\n\n{result["error"]}'
            )
            return

        rows     = result['rows']
        previous = result.get('previous', 0)
        self._import_status.setStyleSheet(
            f'font-size: 11px; color: {_GREEN}; background: transparent;'
        )
        if previous == 0:
            self._import_status.setText(
                f'v  {rows:,} regels geïmporteerd'
            )
        else:
            self._import_status.setText(
                f'v  {rows:,} regels geïmporteerd  (was {previous:,})'
            )

        QMessageBox.information(
            self, 'Import geslaagd',
            f'Statusbord succesvol geïmporteerd.\n\n'
            f'Geïmporteerd: {rows:,} regels\n'
            f'Vorige stand: {previous:,} regels\n\n'
            f'De schermen worden nu bijgewerkt.'
        )
        self.import_completed.emit()

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, 'Select folder with xlsx files')
        if folder:
            self._folder_edit.setText(folder)

    def _load(self) -> None:
        s = load_app_settings()
        self._skip_cb.setChecked(s.get('skip_login', False))
        self._user_edit.setText(s.get('auto_username', ''))
        self._folder_edit.setText(s.get('data_folder', ''))

    def _on_change(self) -> None:
        self._status_lbl.setText('')

    def _save(self) -> None:
        save_app_settings({
            'skip_login':    self._skip_cb.isChecked(),
            'auto_username': self._user_edit.text().strip(),
            'data_folder':   self._folder_edit.text().strip(),
        })

        self._status_lbl.setText('v  Settings saved')
        self.settings_saved.emit()
