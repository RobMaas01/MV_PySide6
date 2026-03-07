"""
Hoofdvenster voor MV3 (PySide6).
Navigatie als tabbalk bovenaan — geen zijbalk.
Content neemt de volledige breedte in.
"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow, QStatusBar, QTabWidget,
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
    ('Settings',      'settings'),
]

_TAB_QSS = f"""
    QTabWidget::pane {{
        border: none;
        background: {SLATE_900};
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


class MainWindow(QMainWindow):
    window_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._store = None
        self._build_ui()
        self._start_loading()

    # ------------------------------------------------------------------
    # UI opbouw
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle('Maintenance Viewer')
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(APP_QSS)
        self.setWindowIcon(QIcon(str(Path(__file__).parent.parent / 'assets' / 'NH90.PNG')))

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._tabs.setStyleSheet(_TAB_QSS)
        self._tabs.setDocumentMode(True)

        # Pagina 0: Home
        self._home_tab = HomeTab()
        self._home_tab.tab_switch_requested.connect(self._tabs.setCurrentIndex)
        self._home_tab.settings_saved.connect(self._refresh_overview)
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
        self._tabs.addTab(self._settings_tab, 'Settings')
        self._settings_tab.settings_saved.connect(self._refresh_overview)
        self._settings_tab.import_completed.connect(self._reload_data)

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

    # ------------------------------------------------------------------
    # Laden
    # ------------------------------------------------------------------

    def _start_loading(self) -> None:
        self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        self._status_bar.showMessage('  Loading data...')

    def on_data_loaded(self, store) -> None:
        self._store = store
        self.unsetCursor()

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
                prepare_statusbord, get_aircraft_list,
                get_calendar_inspections, get_cycle_inspections,
            )
            sys_vars  = load_system_variables()
            user_vars = load_user_variables()

            self._home_tab.update_stats(store, sys_vars, user_vars)
            self._overview_tab.load_data(store, sys_vars, user_vars)

            if store.statusbord is not None:
                df_sb   = prepare_statusbord(store.statusbord)
                df_cal  = get_calendar_inspections(df_sb)
                df_cyc  = get_cycle_inspections(df_sb)
                ac_list = get_aircraft_list(df_sb)
                self._planning_tab.load_data(ac_list, df_cal, df_cyc, sys_vars)
        except Exception as exc:
            self._status_bar.showMessage(f'  Load error: {exc}')

    # ------------------------------------------------------------------

    def _refresh_overview(self) -> None:
        if self._store is None:
            return
        try:
            from data.processor import (
                load_system_variables, load_user_variables,
                prepare_statusbord, get_aircraft_list,
                get_calendar_inspections, get_cycle_inspections,
            )
            sys_vars  = load_system_variables()
            user_vars = load_user_variables()
            self._home_tab.update_stats(self._store, sys_vars, user_vars)
            self._overview_tab.load_data(self._store, sys_vars, user_vars)

            if self._store.statusbord is not None:
                df_sb   = prepare_statusbord(self._store.statusbord)
                df_cal  = get_calendar_inspections(df_sb)
                df_cyc  = get_cycle_inspections(df_sb)
                ac_list = get_aircraft_list(df_sb)
                self._planning_tab.load_data(ac_list, df_cal, df_cyc, sys_vars)
        except Exception as exc:
            self._status_bar.showMessage(f'  Refresh error: {exc}')

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
