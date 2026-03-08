"""
Hoofdvenster voor MV3 (PySide6).
Navigatie als tabbalk bovenaan â€” geen zijbalk.
Content neemt de volledige breedte in.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout,
    QLabel,
    QMainWindow, QStatusBar, QTabWidget,
    QWidget,
)

from ui.tabs.home_tab import HomeTab
from ui.tabs.overview_tab import OverviewTab
from ui.tabs.planning_tab import PlanningTab
from ui.tabs.settings_tab import SettingsTab
from ui.theme import (
    APP_QSS, BLUE_700,
    SLATE_400, SLATE_600, SLATE_700, SLATE_800, SLATE_900, WHITE,
)

_NAV_ITEMS = [
    ('Home',          'home'),
    ('Overview',      'overview'),
    ('Planning',      'planning'),
    ('Configuration', 'configuration'),
    ('Part. insp.',   'partnumber'),
    ('MIS',           'mis'),
    ('Info',          'info'),
]

_TAB_QSS = f"""
    QTabWidget::pane {{
        border: none;
        background: {SLATE_900};
        padding-top: 12px;
    }}
    QTabBar {{
        background: {SLATE_900};
    }}
    QTabBar::tab {{
        background: {SLATE_700};
        color: {WHITE};
        padding: 5px 22px;
        font-size: 12px;
        border: none;
        border-right: 1px solid {SLATE_900};
    }}
    QTabBar::tab:selected {{
        background: {BLUE_700};
        color: {WHITE};
        font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{
        background: {SLATE_600};
        color: {WHITE};
    }}
    QTabBar::scroller {{
        width: 0px;
    }}
"""


def _track_login() -> tuple[str, int]:
    """
    Lees Windows-gebruikersnaam, verhoog de login-teller in MV_UserVariabelen.json
    en geef (username, count) terug.
    """
    username = os.environ.get('USERNAME') or os.environ.get('USER') or ''

    if getattr(sys, 'frozen', False):
        uv_file = Path(sys.executable).parent / 'settings' / 'MV_UserVariabelen.json'
    else:
        uv_file = Path(__file__).parent.parent / 'settings' / 'MV_UserVariabelen.json'

    try:
        with open(uv_file, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return username, 1

    logins = data.setdefault('logins', {})
    entry  = logins.setdefault(username, {'count': 0, 'last': ''})
    entry['count'] += 1
    entry['last']   = datetime.now().strftime('%d/%m/%Y %H:%M')

    try:
        with open(uv_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return username, entry['count']


class MainWindow(QMainWindow):
    window_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._store = None
        self._df_sb:         object = None   # prepare_statusbord output (alle aircraft)
        self._df_cal:        object = None   # get_calendar_inspections output
        self._df_cyc:        object = None   # get_cycle_inspections output
        self._df_cfg:        object = None   # prepare_configuratie output (statisch)
        self._ac_list:       list   = []
        self._sys_vars:      dict   = {}
        self._statusbord_fp: str    = ''     # sha1 van statusbord; opnieuw berekend na import
        # timer to poll for external changes (last_change.txt) + visible check counter
        self._last_flag = 0.0
        self._check_interval_sec = 2
        self._update_check_count = 1
        self._username = ''
        self._work_mode = 'Flight MVKK'
        self._meta_refresh_pending = False
        self._last_meta_refresh_at = 0.0
        self._meta_timer = QTimer(self)
        self._meta_timer.timeout.connect(self._check_for_updates)

        self._build_ui()
        self._meta_timer.start(self._check_interval_sec * 1000)   # iedere 5 seconden
        self._start_loading()

    # ------------------------------------------------------------------
    # UI opbouw
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle('Maintenance Viewer')
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(APP_QSS)
        self.setWindowIcon(QIcon(str(Path(__file__).parent.parent / 'assets' / 'NH90_taskbar.PNG')))
        username, login_count = _track_login()
        self._username = username

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._tabs.setStyleSheet(_TAB_QSS)
        self._tabs.setDocumentMode(True)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # Corner widget rechts â€” met ~8cm spacing rechts voor zichtbaarheid
        self._hide_cb = QCheckBox('Hide completed inspecties')
        _check_icon = str(Path(__file__).parent.parent / 'assets' / 'check.svg').replace('\\', '/')
        self._hide_cb.setStyleSheet(f"""
            QCheckBox {{ color: #1a1a1a; font-size: 12px; spacing: 8px; background: transparent; }}
            QCheckBox::indicator {{ width: 13px; height: 13px; border-radius: 3px;
                border: 1px solid #888; background: #ffffff; }}
            QCheckBox::indicator:checked {{ background: #ffffff; border: 1px solid #888;
                image: url({_check_icon}); }}
        """)
        self._hide_cb.stateChanged.connect(self._on_hide_completed_changed)
        _cb_block = QWidget()
        _cb_block.setStyleSheet('background: #b0b8c1; border-radius: 4px;')
        _cbl = QHBoxLayout(_cb_block)
        _cbl.setContentsMargins(10, 3, 10, 3)
        _cbl.addWidget(self._hide_cb)

        _corner = QWidget()
        _corner.setStyleSheet('background: transparent;')
        _cl = QHBoxLayout(_corner)
        _cl.setContentsMargins(0, 4, 0, 0)
        _cl.setSpacing(0)
        _cl.addWidget(_cb_block)
        _cl.addSpacing(420)
        self._tabs.setCornerWidget(_corner, Qt.Corner.TopRightCorner)
        _corner.setVisible(False)

        # Pagina 0: Home
        self._work_mode = self._load_work_mode()
        self._home_tab = HomeTab(username=self._username, work_mode=self._work_mode)
        self._home_tab.tab_switch_requested.connect(self._tabs.setCurrentIndex)
        self._home_tab.work_mode_changed.connect(self._on_work_mode_changed)
        self._home_tab.settings_saved.connect(self._refresh_overview)
        self._home_tab.import_completed.connect(self._reload_data)
        self._tabs.addTab(self._home_tab, 'Home')

        # Pagina 1: Overzicht
        self._overview_tab = OverviewTab()
        self._tabs.addTab(self._overview_tab, 'Overview')

        # Pagina 2: Planning
        self._planning_tab = PlanningTab()
        self._tabs.addTab(self._planning_tab, 'Planning')

        # Overige pagina's: placeholder
        for label, key in _NAV_ITEMS[3:-1]:
            ph = QLabel(label)
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph.setStyleSheet(f'font-size: 22px; color: {SLATE_600}; background: {SLATE_900};')
            self._tabs.addTab(ph, label)

        # Settings-tab
        self._settings_tab = SettingsTab()
        self._tabs.addTab(self._settings_tab, 'Info')

        self.setCentralWidget(self._tabs)

        # Statusbalk
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {SLATE_800};
                color: {SLATE_400};
                font-size: 12px;
                border-top: 1px solid {SLATE_700};
            }}
        """)
        self.setStatusBar(self._status_bar)

        _user_lbl = QLabel(f'  Welcome, {username}   |   Logins: {login_count}  ')
        _user_lbl.setStyleSheet(f'color: {SLATE_400}; font-size: 11px; background: transparent;')
        self._status_bar.addPermanentWidget(_user_lbl)

        self._update_lbl = QLabel('')
        self._update_lbl.setStyleSheet(f'color: {SLATE_400}; font-size: 11px; background: transparent;')
        self._status_bar.addPermanentWidget(self._update_lbl)
        self._render_update_counter()

    def _load_work_mode(self) -> str:
        try:
            from data.processor import load_user_variables, get_work_mode
            uv = load_user_variables()
            return get_work_mode(uv, username=self._username)
        except Exception:
            return 'Flight MVKK'

    def _on_work_mode_changed(self, mode: str) -> None:
        mode = str(mode)
        if mode == self._work_mode:
            return
        self._work_mode = mode
        self._refresh_overview()

    # ------------------------------------------------------------------
    # Laden
    # ------------------------------------------------------------------

    def _start_loading(self) -> None:
        self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        self._status_bar.showMessage('  Loading data...')

    def on_data_loaded(self, store) -> None:
        self._store = store
        self.unsetCursor()
        # stel de vlag in op huidige waarde, zodat we niet reloaden bij start
        try:
            from data.processor import last_meta
            self._last_flag = last_meta()
        except Exception:
            pass

        names = [
            ('statusbord',   'Statusbord',   store.statusbord),
            ('configuratie', 'Configuratie', store.configuratie),
            ('mis',          'MIS',          store.mis),
            ('3ms',          '3MS',          store.three_ms),
        ]
        parts = []
        for key, label, df in names:
            if key in store.load_errors:
                parts.append(f'{label}: ERROR')
            else:
                parts.append(f'{label}: {len(df):,} rows')
        self._status_bar.showMessage('v  Data loaded  |  ' + '   .   '.join(parts))

        try:
            from data.processor import (
                load_system_variables, load_user_variables,
                prepare_statusbord, prepare_configuratie,
                get_aircraft_list, get_calendar_inspections, get_cycle_inspections,
            )
            from ui.tabs.overview_tab import _statusbord_fingerprint
            sys_vars  = load_system_variables()
            user_vars = load_user_variables()

            # Bouw centrale cache op â€” Ã©Ã©nmalige berekening voor alle tabs.
            if store.statusbord is not None:
                df_sb               = prepare_statusbord(store.statusbord)
                self._df_sb         = df_sb
                self._df_cal        = get_calendar_inspections(df_sb)
                self._df_cyc        = get_cycle_inspections(df_sb)
                self._ac_list       = get_aircraft_list(df_sb)
                self._statusbord_fp = _statusbord_fingerprint(df_sb)
            if store.configuratie is not None:
                self._df_cfg = prepare_configuratie(store.configuratie)
            self._sys_vars = sys_vars

            self._home_tab.set_context(self._username, self._work_mode)
            self._home_tab.update_stats(
                store, sys_vars, user_vars,
                df_cal=self._df_cal, df_cyc=self._df_cyc,
            )
            from data.processor import get_hide_completed
            _hide = get_hide_completed(user_vars, username=self._username)
            self._hide_cb.blockSignals(True)
            self._hide_cb.setChecked(_hide)
            self._hide_cb.blockSignals(False)
            self._overview_tab.load_data(
                store, sys_vars, user_vars,
                username=self._username, work_mode=self._work_mode,
                df_sb=self._df_sb, df_cal=self._df_cal, df_cyc=self._df_cyc,
                df_cfg=self._df_cfg, statusbord_fp=self._statusbord_fp,
                hide_completed=_hide,
            )
            if self._df_cal is not None:
                self._planning_tab.load_data(self._ac_list, self._df_cal, self._df_cyc, sys_vars)
        except Exception as exc:
            self._status_bar.showMessage(f'  Load error: {exc}')

    # ------------------------------------------------------------------

    def _on_tab_changed(self, idx: int) -> None:
        self._tabs.cornerWidget(Qt.Corner.TopRightCorner).setVisible(idx == 1)
        # Planningdata wordt al geladen bij init en bij databron-refresh.
        # Voorkomt zichtbare delay bij elke tab-switch naar Planning.

    def _on_hide_completed_changed(self, _state: int) -> None:
        hide = self._hide_cb.isChecked()
        try:
            from data.processor import load_user_variables, save_user_variables, set_hide_completed
            uv = load_user_variables()
            set_hide_completed(uv, hide, username=self._username)
            save_user_variables(uv)
        except Exception:
            pass
        self._refresh_overview()

    def _refresh_overview(self, refresh_planning: bool = False) -> None:
        """Ververs overview en home stats.

        refresh_planning=False (default): alleen instellingen/filters gewijzigd â€”
            gebruik gecachede DataFrames, geen herberekening.
        refresh_planning=True: databron gewijzigd (import / meta-watcher) â€”
            herbouw volledige cache en update alle tabs inclusief planning.
        """
        if self._store is None:
            return
        try:
            from data.processor import (
                load_system_variables, load_user_variables,
                prepare_statusbord, prepare_configuratie,
                get_aircraft_list, get_calendar_inspections, get_cycle_inspections,
            )
            sys_vars  = load_system_variables()
            user_vars = load_user_variables()

            if refresh_planning:
                # Databron gewijzigd: herbouw centrale cache.
                from ui.tabs.overview_tab import _statusbord_fingerprint
                if self._store.statusbord is not None:
                    df_sb               = prepare_statusbord(self._store.statusbord)
                    self._df_sb         = df_sb
                    self._df_cal        = get_calendar_inspections(df_sb)
                    self._df_cyc        = get_cycle_inspections(df_sb)
                    self._ac_list       = get_aircraft_list(df_sb)
                    self._statusbord_fp = _statusbord_fingerprint(df_sb)
                if self._store.configuratie is not None:
                    self._df_cfg = prepare_configuratie(self._store.configuratie)
                self._sys_vars = sys_vars

            self._home_tab.update_stats(
                self._store, sys_vars, user_vars,
                df_cal=self._df_cal, df_cyc=self._df_cyc,
            )
            from data.processor import get_hide_completed
            self._overview_tab.load_data(
                self._store, sys_vars, user_vars,
                username=self._username, work_mode=self._work_mode,
                df_sb=self._df_sb, df_cal=self._df_cal, df_cyc=self._df_cyc,
                df_cfg=self._df_cfg, statusbord_fp=self._statusbord_fp,
                hide_completed=get_hide_completed(user_vars, username=self._username),
            )
            if refresh_planning and self._df_cal is not None:
                self._planning_tab.load_data(self._ac_list, self._df_cal, self._df_cyc, self._sys_vars)
        except Exception as exc:
            self._status_bar.showMessage(f'  Refresh error: {exc}')

    def _request_meta_refresh(self) -> None:
        if self._meta_refresh_pending:
            return
        self._meta_refresh_pending = True
        QTimer.singleShot(120, self._run_meta_refresh)

    def _run_meta_refresh(self) -> None:
        self._meta_refresh_pending = False
        now = time.monotonic()
        # Guard tegen refresh-storms bij veel externe writes.
        if now - self._last_meta_refresh_at < 0.35:
            self._request_meta_refresh()
            return
        self._last_meta_refresh_at = now
        self._refresh_overview(refresh_planning=True)

    # ------------------------------------------------------------------
    # metadata polling
    def _render_update_counter(self) -> None:
        self._update_lbl.setText(f'  Update check #{self._update_check_count}  ')

    def _check_for_updates(self):
        try:
            from data.processor import last_meta
            m = last_meta()
            if m != self._last_flag:
                self._last_flag = m
                self._request_meta_refresh()
        except Exception:
            logging.warning('_check_for_updates mislukt', exc_info=True)
        finally:
            self._update_check_count += 1
            self._render_update_counter()

    def _reload_data(self) -> None:
        """Herlaad alle data vanuit SQLite (bijv. na een import)."""
        from data.loader import DataLoader
        import data.store as store_module

        self._start_loading()
        loader = DataLoader()
        loader.finished.connect(self.on_data_loaded)
        loader.finished.connect(lambda s: setattr(store_module, 'data', s))
        loader.start()
        # Bewaar referentie zodat de thread niet vroegtijdig wordt opgeruimd
        self._active_loader = loader

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

