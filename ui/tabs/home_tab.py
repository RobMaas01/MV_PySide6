"""
Home-tab: welkomstscherm met overzichtskaarten en helikopter-selectie.
"""
import json
import logging
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ui.theme import SLATE_400, SLATE_700, WHITE

_ICON_PATH   = Path(__file__).parent.parent.parent / 'assets' / 'NH90_Main.PNG'
_UV_FILE     = Path(__file__).parent.parent.parent / 'settings' / 'MV_UserVariabelen.json'

_CB_QSS = f"""
    QCheckBox {{
        color: {WHITE}; font-size: 13px; spacing: 8px; background: transparent;
    }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 4px;
        border: 1px solid {SLATE_700}; background: #0f172a;
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
            background: rgba(15, 30, 60, 210);
            border: 1px solid rgba(100, 140, 200, 80);
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


class HomeTab(QWidget):
    """Welkomstscherm — eerste tab in het hoofdvenster."""

    tab_switch_requested = Signal(int)
    work_mode_changed    = Signal(str)
    settings_saved       = Signal()
    import_completed     = Signal()

    def __init__(self, username: str = '', work_mode: str = 'B1', parent=None):
        super().__init__(parent)
        self._stat_labels: dict[str, QLabel] = {}
        self._heli_checkboxes: dict[str, QCheckBox] = {}
        self._username = (username or '').strip()
        self._work_mode = str(work_mode or 'B1').upper()

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
        heli_frame.setFixedWidth(210)
        heli_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 180);
                border: 1px solid rgba(100, 140, 200, 60);
                border-radius: 8px;
            }
        """)

        vh = QVBoxLayout(heli_frame)
        vh.setContentsMargins(14, 12, 14, 12)
        vh.setSpacing(6)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        mode_lbl = QLabel('Work mode')
        mode_lbl.setStyleSheet(
            f'color: {WHITE}; font-size: 10px; font-weight: bold; background: transparent; border: none;'
        )
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(['B1', 'B2', 'B3', 'BVP'])
        self._mode_combo.setCurrentText(self._work_mode)
        self._mode_combo.currentTextChanged.connect(lambda t: self.work_mode_changed.emit(t))
        mode_row.addWidget(mode_lbl)
        mode_row.addWidget(self._mode_combo, stretch=1)
        vh.addLayout(mode_row)

        lbl_h = QLabel('Helicopters in overview')
        lbl_h.setStyleSheet(
            f'color: {WHITE}; font-size: 12px; font-weight: bold; background: transparent; border: none;'
        )
        lbl_hs = QLabel('Select which aircraft are displayed')
        lbl_hs.setStyleSheet(
            f'color: {SLATE_400}; font-size: 10px; background: transparent; border: none;'
        )
        lbl_hs.setWordWrap(True)
        vh.addWidget(lbl_h)
        vh.addWidget(lbl_hs)

        self._ctx_lbl = QLabel('')
        self._ctx_lbl.setStyleSheet(
            f'color: {SLATE_400}; font-size: 10px; background: transparent; border: none;'
        )
        vh.addWidget(self._ctx_lbl)

        div_h = QFrame()
        div_h.setFixedHeight(1)
        div_h.setStyleSheet(f'background: {SLATE_700}; border: none; max-height: 1px;')
        vh.addWidget(div_h)

        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 4, 0, 0)

        if _UV_FILE.exists():
            with open(_UV_FILE, encoding='utf-8') as _f:
                _uv = json.load(_f)
            helis = sorted(_uv.get('helikopter', {}).keys())
            n_cols = 2
            n_rows = -(-len(helis) // n_cols)
            for i, name in enumerate(helis):
                cb = QCheckBox(name)
                cb.setStyleSheet(_CB_QSS)
                self._heli_checkboxes[name] = cb
                grid.addWidget(cb, i % n_rows, i // n_rows)

        vh.addLayout(grid)

        save_row = QHBoxLayout()
        save_row.setSpacing(10)
        save_btn = QPushButton('Save')
        save_btn.setStyleSheet(_BTN_QSS)
        save_btn.setFixedHeight(26)
        save_btn.clicked.connect(self._save_helis)
        self._heli_status = QLabel('')
        self._heli_status.setStyleSheet(
            'color: #4ade80; font-size: 11px; background: transparent; border: none;'
        )
        save_row.addWidget(save_btn)
        save_row.addWidget(self._heli_status)
        save_row.addStretch()
        vh.addLayout(save_row)

        self._import_btn = QPushButton('Import statusboard')
        self._import_btn.setStyleSheet(_BTN_QSS)
        self._import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._import_btn.setFixedWidth(210)
        self._import_btn.setFixedHeight(28)
        self._import_btn.clicked.connect(self._import_statusbord)
        right.addWidget(self._import_btn)
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

        from data.database import import_statusbord

        self._import_btn.setEnabled(False)
        result = import_statusbord(Path(path))
        self._import_btn.setEnabled(True)

        if result['error']:
            QMessageBox.warning(
                self, 'Import failed',
                f'Statusboard could not be imported:\n\n{result["error"]}'
            )
            return

        rows       = result['rows']
        previous   = result.get('previous', 0)
        copied_to  = result.get('copied_to', '')
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

    def set_context(self, username: str, work_mode: str) -> None:
        self._username = (username or '').strip()
        self._work_mode = str(work_mode or 'B1').upper()
        self._mode_combo.blockSignals(True)
        self._mode_combo.setCurrentText(self._work_mode)
        self._mode_combo.blockSignals(False)
        self._load_helis()

    def _load_helis(self) -> None:
        if not _UV_FILE.exists() or not self._heli_checkboxes:
            return
        from data.processor import load_user_variables, get_selected_aircraft
        uv = load_user_variables()
        selected = set(get_selected_aircraft(
            uv, username=self._username, work_mode=self._work_mode
        ))
        for name, cb in self._heli_checkboxes.items():
            cb.setChecked(name in selected)
        scope = 'personal' if self._work_mode == 'BVP' else 'shared group'
        self._ctx_lbl.setText(f'Context: {self._work_mode} ({scope})')

    def _save_helis(self) -> None:
        from data.processor import load_user_variables, save_user_variables, set_selected_aircraft
        uv = load_user_variables()
        selected = [name for name, cb in self._heli_checkboxes.items() if cb.isChecked()]
        set_selected_aircraft(uv, selected, username=self._username, work_mode=self._work_mode)
        save_user_variables(uv)
        self._heli_status.setText('v  Saved')
        self.settings_saved.emit()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def update_stats(self, store, sys_vars=None, user_vars=None) -> None:
        try:
            import pandas as pd
            from data.processor import (
                prepare_statusbord, get_aircraft_list,
                get_calendar_inspections, get_cycle_inspections,
            )

            df_sb   = prepare_statusbord(store.statusbord) if store.statusbord is not None else None
            ac_list = get_aircraft_list(
                df_sb, user_vars, username=self._username, work_mode=self._work_mode
            ) if df_sb is not None else []
            df_filtered = df_sb[df_sb['Aircraft'].isin(ac_list)] if df_sb is not None else None
            df_cal  = get_calendar_inspections(df_filtered) if df_filtered is not None else pd.DataFrame()
            df_cyc  = get_cycle_inspections(df_filtered)  if df_filtered is not None else pd.DataFrame()

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
