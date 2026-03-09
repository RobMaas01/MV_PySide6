"""
Home-tab: welkomstscherm met overzichtskaarten en helikopter-selectie.
"""
import logging
from datetime import date
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QDialog, QMessageBox, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from ui.theme import SLATE_400, SLATE_700, WHITE

_ICON_PATH = Path(__file__).parent.parent.parent / 'assets' / 'NH90_Main.PNG'

_CB_QSS = f"""
    QCheckBox {{
        color: {WHITE}; font-size: 14px; font-weight: 600; spacing: 6px; background: transparent;
    }}
    QCheckBox::indicator {{
        width: 12px; height: 12px; border-radius: 3px;
        border: 1px solid {SLATE_700}; background: #2a3a52;
    }}
    QCheckBox::indicator:checked {{
        background: #1d4ed8; border: 1px solid #3b82f6;
    }}
"""

_BTN_QSS = """
    QPushButton {
        background-color: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #8aafc0, stop:1 #afc4d0
        );
        color: #1a1a1a;
        border: 1px solid #8aafc0;
        border-bottom: 2px solid #3a5a6e;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        padding: 6px 20px;
    }
    QPushButton:hover {
        background-color: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #8aabb8, stop:1 #8aafc0
        );
    }
    QPushButton:pressed {
        background-color: #afc4d0;
        border-bottom: 1px solid #3a5a6e;
        padding-top: 9px;
    }
"""

_BTN_GHOST_QSS = _BTN_QSS


def _stat_card(title: str, init_value: str = '-', subtitle: str = '') -> tuple:
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background: rgba(48, 67, 95, 220);
            border: 1px solid rgba(140, 176, 224, 110);
            border-radius: 10px;
        }
    """)
    card.setFixedSize(143, 79)

    v = QVBoxLayout(card)
    v.setContentsMargins(14, 11, 14, 11)
    v.setSpacing(2)

    lbl_t = QLabel(title)
    lbl_t.setStyleSheet(
        f'color: {SLATE_400}; font-size: 9px; background: transparent; border: none;'
    )
    lbl_v = QLabel(init_value)
    lbl_v.setStyleSheet(
        f'color: {WHITE}; font-size: 22px; font-weight: bold; background: transparent; border: none;'
    )
    v.addWidget(lbl_t)
    v.addWidget(lbl_v)

    if subtitle:
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(
            'color: rgba(160,195,235,160); font-size: 8px; background: transparent; border: none;'
        )
        v.addWidget(lbl_s)

    return card, lbl_v


class _ImportWorker(QThread):
    """Voert statusbord-import uit in achtergrond-thread."""
    done = Signal(dict)

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self._path = path

    def run(self) -> None:
        from data.database import import_statusbord
        self.done.emit(import_statusbord(self._path))


class HomeTab(QWidget):
    """Welkomstscherm â€” eerste tab in het hoofdvenster."""

    tab_switch_requested    = Signal(int)
    work_mode_changed       = Signal(str)
    settings_saved          = Signal()
    import_completed        = Signal()

    def __init__(
        self,
        username: str = '',
        work_mode: str = 'Flight MVKK',
        parent=None,
        state_service: Any = None,
    ):
        super().__init__(parent)
        self._stat_labels: dict[str, QLabel] = {}
        self._heli_checkboxes: dict[str, QCheckBox] = {}
        self._username = (username or '').strip()
        self._work_mode = str(work_mode or 'Flight MVKK')
        self._state_service = state_service
        self._suspend_selection_events = False
        self._dirty = False
        self._status_clear_token = 0

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(lambda: self._persist_filters(force=True))

        self.setObjectName('HomeTab')
        self._build_ui()
        self._load_helis()

    # ------------------------------------------------------------------
    # UI-opbouw
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # -- Hoofd body: center + rechts --------------------------------
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Center kolom
        center = QVBoxLayout()
        center.setContentsMargins(80, 0, 80, 0)
        center.setSpacing(0)

        center.addStretch(2)

        # Logo + titel
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row.setSpacing(22)

        icon_lbl = QLabel()
        icon_pix = QPixmap(str(_ICON_PATH)).scaled(
            240, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        icon_lbl.setPixmap(icon_pix)
        icon_lbl.setStyleSheet('background: transparent;')
        logo_row.addWidget(icon_lbl)

        lbl_combined = QLabel(
            '<span style="font-size:34px; font-weight:bold; color:white; line-height:1;">'
            'Maintenance Viewer</span><br>'
            '<span style="font-size:14px; color:rgba(160,195,235,200); line-height:1;">'
            'NH90 Materiaal Logistiek Dashboard</span>'
        )
        lbl_combined.setTextFormat(Qt.TextFormat.RichText)
        lbl_combined.setStyleSheet('background: transparent; padding: 0; margin: 0;')
        logo_row.addWidget(lbl_combined)

        center.addLayout(logo_row)
        center.addSpacing(44)

        # Statistiekkaarten
        cards_row = QHBoxLayout()
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cards_row.setSpacing(18)

        card_defs = [
            ('aircraft', 'Aircraft',             ''),
            ('cal',      'Calendar inspections', 'next 7 days'),
            ('uren',     'Flight hrs inspections', '< 10 hrs remaining'),
            ('land',     'Landing inspections',   '< 20 landings'),
        ]
        for key, title, sub in card_defs:
            card, val_lbl = _stat_card(title, '-', sub)
            self._stat_labels[key] = val_lbl
            cards_row.addWidget(card)

        center.addLayout(cards_row)
        center.addSpacing(38)

        # Navigatieknoppen
        nav_defs = [
            ('Overview',      1),
            ('Planning',      2),
            ('Configuration', 3),
            ('Part. insp.',   4),
            ('MIS',           5),
        ]
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(10)
        for label, idx in nav_defs:
            btn = QPushButton(label)
            btn.setStyleSheet(_BTN_QSS)
            btn.setFixedWidth(120)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.tab_switch_requested.emit(i))
            btn_row.addWidget(btn)
        center.addLayout(btn_row)

        center.addStretch(3)

        body.addLayout(center, 1)

        # -- Rechter paneel: helikopter-selectie -----------------------
        right = QVBoxLayout()
        right.setContentsMargins(0, 20, 20, 20)
        right.setSpacing(0)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        heli_frame = QFrame()
        heli_frame.setFixedWidth(176)
        heli_frame.setStyleSheet("""
            QFrame {
                background: rgba(52, 72, 102, 224);
                border: 1px solid rgba(152, 192, 232, 170);
                border-radius: 8px;
            }
        """)

        vh = QVBoxLayout(heli_frame)
        vh.setContentsMargins(10, 10, 10, 10)
        vh.setSpacing(5)

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(['Flight MVKK', 'Out of area 1', 'Out of area 2', 'Out of area 3', 'BVP'])
        self._mode_combo.setCurrentText(self._work_mode)
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        vh.addWidget(self._mode_combo)
        vh.addSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        try:
            from data.processor import load_user_variables
            _uv = load_user_variables()
            helis = sorted(_uv.get('helikopter', {}).keys())
        except Exception:
            helis = []
        n_cols = 2
        n_rows = max(1, -(-len(helis) // n_cols))
        for i, name in enumerate(helis):
            cb = QCheckBox(name)
            cb.setStyleSheet(_CB_QSS)
            cb.stateChanged.connect(self._on_selection_changed)
            self._heli_checkboxes[name] = cb
            grid.addWidget(cb, i % n_rows, i // n_rows)

        vh.addLayout(grid)

        self._heli_status = QLabel('')
        self._heli_status.setStyleSheet(
            'color: #4ade80; font-size: 11px; background: transparent; border: none;'
        )
        vh.addWidget(self._heli_status)


        self._import_btn = QPushButton('Import statusboard')
        self._import_btn.setStyleSheet(_BTN_QSS)
        self._import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._import_btn.setFixedWidth(150)
        self._import_btn.setFixedHeight(28)
        self._import_btn.clicked.connect(self._import_statusbord)
        self._help_icon_btn = QToolButton()
        self._help_icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._help_icon_btn.setText('?')
        self._help_icon_btn.setFixedSize(24, 24)
        self._help_icon_btn.setToolTip('Help')
        self._help_icon_btn.setStyleSheet("""
            QToolButton {
                background: #d6e6f2;
                color: #0f2a43;
                border: 1px solid #8fb0c7;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                padding: 0px 0px 1px 0px;
            }
            QToolButton:hover { background: #e3f0fa; }
            QToolButton:pressed { background: #bfd5e6; }
        """)
        self._help_icon_btn.clicked.connect(self._show_help_popup)
        import_row = QHBoxLayout()
        import_row.setContentsMargins(0, 0, 0, 0)
        import_row.setSpacing(4)
        import_row.addWidget(self._import_btn)
        import_row.addWidget(self._help_icon_btn)
        import_row.addStretch()
        right.addLayout(import_row)
        right.addSpacing(8)

        right.addWidget(heli_frame)

        body.addLayout(right)

        outer.addLayout(body, 1)

        # -- Voettekst --------------------------------------------------
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('background: rgba(100,140,200,50);')
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        footer = QHBoxLayout()
        footer.setContentsMargins(20, 10, 20, 16)

        lbl_date = QLabel(date.today().strftime('%d %B %Y'))
        lbl_date.setStyleSheet(
            'color: rgba(160,195,235,140); font-size: 11px; background: transparent;'
        )
        footer.addStretch()
        footer.addWidget(lbl_date)
        outer.addLayout(footer)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def _import_statusbord(self) -> None:
        downloads = str(Path.home() / 'Downloads')
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select statusboard.xlsx', downloads, 'Excel files (*.xlsx *.xls)'
        )
        if not path:
            return
        self._import_btn.setEnabled(False)
        self._import_btn.setText('Importing...')
        self._import_worker = _ImportWorker(Path(path), self)
        self._import_worker.done.connect(self._on_import_done)
        self._import_worker.start()

    def _on_import_done(self, result: dict) -> None:
        self._import_btn.setEnabled(True)
        self._import_btn.setText('Import statusboard')
        if result['error']:
            QMessageBox.warning(
                self, 'Import failed',
                f'Statusboard could not be imported:\n\n{result["error"]}'
            )
            return
        rows      = result['rows']
        previous  = result.get('previous', 0)
        copied_to = result.get('copied_to', '')
        QMessageBox.information(
            self, 'Import successful',
            f'Statusboard imported successfully.\n\n'
            f'Imported: {rows:,} rows\n'
            f'Previous: {previous:,} rows\n'
            f'Saved to: {copied_to}\n\n'
            f'Screens will now be updated.'
        )
        self.import_completed.emit()

    # ------------------------------------------------------------------
    # Helikopter-selectie
    # ------------------------------------------------------------------

    def _show_help_popup(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dlg.setModal(True)
        dlg.setFixedWidth(560)
        dlg.setStyleSheet("""
            QDialog {
                background: rgba(56, 78, 110, 230);
                border: 1px solid rgba(188, 218, 244, 220);
                border-radius: 8px;
            }
            QLabel {
                color: #f8fafc;
                background: transparent;
                border: none;
            }
        """)

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        body = QWidget()
        body.setObjectName('helpBody')
        body.setStyleSheet("""
            QWidget#helpBody {
                background: rgba(56, 78, 110, 230);
                border-top: 1px solid rgba(214, 235, 252, 110);
                border-left: 1px solid rgba(214, 235, 252, 110);
                border-right: 1px solid rgba(214, 235, 252, 110);
                border-bottom: 1px solid rgba(214, 235, 252, 110);
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 12, 14, 10)
        bl.setSpacing(10)
        txt = QLabel(
            'Import statusboard:\n'
            'Gebruik dit om een nieuwere statusboard Excel-file te laden vanuit Downloads of een andere map.\n'
            'Het bestand wordt eerst gevalideerd (verplichte kolommen), daarna gekopieerd naar de app-datasource en geÃ¯mporteerd.\n'
            'Na een succesvolle import worden alle schermen ververst met de nieuwe data.\n\n'
            'Locatie:\n'
            'Kies het actieve werkgebied. Dit bepaalt welke data en standaardwaarden worden gebruikt.\n'
            'Als BVP is geselecteerd, wordt deze instelling alleen voor de huidige gebruiker opgeslagen.\n'
            'Alle andere locaties zijn gedeeld en gelden voor alle gebruikers.\n\n'
            'Helikopter-selectie:\n'
            'Selecteer welke helikopters zichtbaar zijn in Overview.'
        )
        txt.setWordWrap(True)
        txt.setStyleSheet('font-size: 12px; line-height: 1.35;')
        bl.addWidget(txt)

        row = QHBoxLayout()
        row.addStretch()
        close_btn = QPushButton('Close')
        close_btn.setStyleSheet(_BTN_QSS)
        close_btn.setFixedSize(72, 24)
        close_btn.clicked.connect(dlg.accept)
        row.addWidget(close_btn)
        bl.addLayout(row)
        outer.addWidget(body)

        dlg.exec()

    def _set_status(self, text: str = '', ttl_ms: int = 0) -> None:
        self._status_clear_token += 1
        token = self._status_clear_token
        self._heli_status.setText(text)
        if ttl_ms > 0 and text:
            QTimer.singleShot(ttl_ms, lambda: self._clear_status_if_current(token))

    def _clear_status_if_current(self, token: int) -> None:
        if token == self._status_clear_token:
            self._heli_status.setText('')

    def _collect_selected(self) -> list[str]:
        return [name for name, cb in self._heli_checkboxes.items() if cb.isChecked()]

    def _on_selection_changed(self) -> None:
        if self._suspend_selection_events:
            return
        self._dirty = True
        self._save_timer.start()

    def _on_mode_changed(self, text: str) -> None:
        mode = str(text)
        if mode == self._work_mode:
            return
        self._work_mode = mode
        self._load_helis()
        # Sla alleen de mode op â€” geen heli-selectie herschrijven, geen settings_saved.
        # work_mode_changed triggert Ã©Ã©n _refresh_overview via MainWindow.
        try:
            if self._state_service is not None:
                self._state_service.set_work_mode(mode, username=self._username)
            else:
                from data.processor import load_user_variables, save_user_variables, set_work_mode
                uv = load_user_variables()
                set_work_mode(uv, mode, username=self._username)
                save_user_variables(uv)
        except Exception:
            pass
        self.work_mode_changed.emit(text)

    def set_context(self, username: str, work_mode: str) -> None:
        self._username = (username or '').strip()
        self._work_mode = str(work_mode or 'Flight MVKK')
        self._mode_combo.blockSignals(True)
        self._mode_combo.setCurrentText(self._work_mode)
        self._mode_combo.blockSignals(False)
        self._set_status('')
        self._load_helis()

    def _load_helis(self) -> None:
        if not self._heli_checkboxes:
            return
        if self._state_service is not None:
            selected = set(self._state_service.get_selected_aircraft(
                username=self._username, work_mode=self._work_mode
            ))
        else:
            from data.processor import load_user_variables, get_selected_aircraft
            uv = load_user_variables()
            selected = set(get_selected_aircraft(
                uv, username=self._username, work_mode=self._work_mode
            ))
        self._suspend_selection_events = True
        for name, cb in self._heli_checkboxes.items():
            cb.setChecked(name in selected)
        self._suspend_selection_events = False
        self._set_status('')

    def _persist_filters(self, force: bool = False) -> None:
        if not force and not self._dirty:
            return
        try:
            selected = self._collect_selected()
            if self._state_service is not None:
                self._state_service.save_selection_and_mode(
                    selected=selected,
                    mode=self._work_mode,
                    username=self._username,
                )
            else:
                from data.processor import (
                    load_user_variables, save_user_variables,
                    set_selected_aircraft, set_work_mode,
                )
                uv = load_user_variables()
                set_work_mode(uv, self._work_mode, username=self._username)
                set_selected_aircraft(uv, selected, username=self._username, work_mode=self._work_mode)
                save_user_variables(uv)
        except Exception as exc:
            self._set_status('x  Save failed')
            QMessageBox.warning(self, 'Save failed', str(exc))
            return

        self._dirty = False
        self._set_status('v  Saved', ttl_ms=2200)
        self.settings_saved.emit()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def update_stats(self, store, sys_vars=None, user_vars=None,
                     df_cal=None, df_cyc=None) -> None:
        try:
            import pandas as pd
            from data.processor import get_selected_aircraft

            if df_cal is None or df_cyc is None:
                # Fallback: volledige berekening (bijv. eerste aanroep zonder cache).
                from data.processor import (
                    prepare_statusbord, get_aircraft_list,
                    get_calendar_inspections, get_cycle_inspections,
                )
                df_sb_loc = prepare_statusbord(store.statusbord) if store.statusbord is not None else None
                ac_list   = get_aircraft_list(
                    df_sb_loc, user_vars, username=self._username, work_mode=self._work_mode
                ) if df_sb_loc is not None else []
                df_f   = df_sb_loc[df_sb_loc['Aircraft'].isin(ac_list)] if df_sb_loc is not None else None
                df_cal = get_calendar_inspections(df_f) if df_f is not None else pd.DataFrame()
                df_cyc = get_cycle_inspections(df_f)    if df_f is not None else pd.DataFrame()
            else:
                # Snel pad: filter gecachede DataFrames op geselecteerde aircraft.
                ac_set  = set(get_selected_aircraft(user_vars, username=self._username, work_mode=self._work_mode)) if user_vars else set()
                ac_list = sorted(ac_set)
                df_cal  = df_cal[df_cal['Aircraft'].isin(ac_set)] if not df_cal.empty else df_cal
                df_cyc  = df_cyc[df_cyc['Aircraft'].isin(ac_set)] if not df_cyc.empty else df_cyc

            # Kalender: alleen items komende 7 dagen
            if not df_cal.empty and 'Rest' in df_cal.columns:
                df_cal = df_cal[df_cal['Rest'] <= 7]

            # Cycle opsplitsen op eenheid en drempelwaarde
            if not df_cyc.empty and 'Eenheid cyclus' in df_cyc.columns:
                df_uren = df_cyc[(df_cyc['Eenheid cyclus'] == 'UUR') & (pd.to_numeric(df_cyc['Rest'], errors='coerce') < 10)]
                df_land = df_cyc[(df_cyc['Eenheid cyclus'] == 'ST')  & (pd.to_numeric(df_cyc['Rest'], errors='coerce') < 20)]
            else:
                df_uren = pd.DataFrame()
                df_land = pd.DataFrame()

            self._stat_labels['aircraft'].setText(str(len(ac_list)))
            self._stat_labels['cal'].setText(str(len(df_cal)))
            self._stat_labels['uren'].setText(str(len(df_uren)))
            self._stat_labels['land'].setText(str(len(df_land)))

        except Exception:
            logging.warning('update_stats mislukt', exc_info=True)
