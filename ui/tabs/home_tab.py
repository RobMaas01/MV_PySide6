"""
Home-tab: welkomstscherm met overzichtskaarten en helikopter-selectie.
"""
import json
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

from ui.theme import BLUE_600, BLUE_700, SLATE_400, SLATE_700, WHITE

_ICON_PATH   = Path(__file__).parent.parent.parent / 'assets' / 'NH90.PNG'
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

_BTN_QSS = f"""
    QPushButton {{
        background: {BLUE_700};
        color: {WHITE};
        border: none;
        border-radius: 6px;
        padding: 10px 32px;
        font-size: 13px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background: {BLUE_600};
    }}
"""

_BTN_GHOST_QSS = f"""
    QPushButton {{
        background: transparent;
        color: {WHITE};
        border: 1px solid rgba(100,140,200,120);
        border-radius: 6px;
        padding: 10px 32px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: rgba(100,140,200,40);
    }}
"""


def _stat_card(title: str, init_value: str = '-', subtitle: str = '') -> tuple:
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background: rgba(15, 30, 60, 210);
            border: 1px solid rgba(100, 140, 200, 80);
            border-radius: 10px;
        }
    """)
    card.setFixedSize(190, 105)

    v = QVBoxLayout(card)
    v.setContentsMargins(18, 14, 18, 14)
    v.setSpacing(3)

    lbl_t = QLabel(title)
    lbl_t.setStyleSheet(
        f'color: {SLATE_400}; font-size: 11px; background: transparent; border: none;'
    )
    lbl_v = QLabel(init_value)
    lbl_v.setStyleSheet(
        f'color: {WHITE}; font-size: 30px; font-weight: bold; background: transparent; border: none;'
    )
    v.addWidget(lbl_t)
    v.addWidget(lbl_v)

    if subtitle:
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(
            'color: rgba(160,195,235,160); font-size: 10px; background: transparent; border: none;'
        )
        v.addWidget(lbl_s)

    return card, lbl_v


class HomeTab(QWidget):
    """Welkomstscherm — eerste tab in het hoofdvenster."""

    tab_switch_requested = Signal(int)
    settings_saved       = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stat_labels: dict[str, QLabel] = {}
        self._heli_checkboxes: dict[str, QCheckBox] = {}

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
            72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        icon_lbl.setPixmap(icon_pix)
        icon_lbl.setStyleSheet('background: transparent;')
        logo_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        lbl_title = QLabel('Maintenance Viewer')
        lbl_title.setStyleSheet(
            'color: white; font-size: 34px; font-weight: bold; background: transparent;'
        )
        lbl_sub = QLabel('NH90 Maintenance Dashboard')
        lbl_sub.setStyleSheet(
            'color: rgba(160,195,235,200); font-size: 14px; background: transparent;'
        )
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)
        logo_row.addLayout(title_col)

        center.addLayout(logo_row)
        center.addSpacing(44)

        # Statistiekkaarten
        cards_row = QHBoxLayout()
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cards_row.setSpacing(18)

        card_defs = [
            ('aircraft', 'Aircraft',             ''),
            ('cal',      'Calendar inspections', 'next 30 days'),
            ('cyc',      'Cycle items',          'next 30 days'),
            ('warn',     'Warnings',             'expired / critical'),
        ]
        for key, title, sub in card_defs:
            card, val_lbl = _stat_card(title, '-', sub)
            self._stat_labels[key] = val_lbl
            cards_row.addWidget(card)

        center.addLayout(cards_row)
        center.addSpacing(38)

        # Navigatieknoppen
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(14)

        btn_ov = QPushButton('Overview')
        btn_ov.setStyleSheet(_BTN_QSS)
        btn_ov.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ov.clicked.connect(lambda: self.tab_switch_requested.emit(1))

        btn_pl = QPushButton('Planning')
        btn_pl.setStyleSheet(_BTN_GHOST_QSS)
        btn_pl.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pl.clicked.connect(lambda: self.tab_switch_requested.emit(2))

        btn_row.addWidget(btn_ov)
        btn_row.addWidget(btn_pl)
        center.addLayout(btn_row)

        center.addStretch(3)

        body.addLayout(center, 1)

        # -- Rechter paneel: helikopter-selectie -----------------------
        right = QVBoxLayout()
        right.setContentsMargins(0, 20, 20, 20)
        right.setSpacing(0)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        heli_frame = QFrame()
        heli_frame.setFixedWidth(300)
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
        save_btn = QPushButton('Opslaan')
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE_700}; color: {WHITE};
                border: none; border-radius: 5px;
                padding: 4px 14px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {BLUE_600}; }}
        """)
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
    # Helikopter-selectie
    # ------------------------------------------------------------------

    def _load_helis(self) -> None:
        if not _UV_FILE.exists() or not self._heli_checkboxes:
            return
        with open(_UV_FILE, encoding='utf-8') as f:
            uv = json.load(f)
        helis = uv.get('helikopter', {})
        for name, cb in self._heli_checkboxes.items():
            cb.setChecked(helis.get(name, {}).get('Location_1', False))

    def _save_helis(self) -> None:
        if not _UV_FILE.exists():
            return
        with open(_UV_FILE, encoding='utf-8') as f:
            uv = json.load(f)
        for name, cb in self._heli_checkboxes.items():
            if name in uv.get('helikopter', {}):
                uv['helikopter'][name]['Location_1'] = cb.isChecked()
        with open(_UV_FILE, 'w', encoding='utf-8') as f:
            json.dump(uv, f, indent=2, ensure_ascii=False)
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
            ac_list = get_aircraft_list(df_sb, user_vars) if df_sb is not None else []
            df_cal  = get_calendar_inspections(df_sb) if df_sb is not None else pd.DataFrame()
            df_cyc  = get_cycle_inspections(df_sb)  if df_sb is not None else pd.DataFrame()

            self._stat_labels['aircraft'].setText(str(len(ac_list)))
            self._stat_labels['cal'].setText(str(len(df_cal)))
            self._stat_labels['cyc'].setText(str(len(df_cyc)))

            warn = 0
            if not df_cal.empty and 'days_remaining' in df_cal.columns:
                warn += int((df_cal['days_remaining'] <= 0).sum())
            if not df_cyc.empty and 'remaining' in df_cyc.columns:
                warn += int((df_cyc['remaining'] <= 0).sum())
            self._stat_labels['warn'].setText(str(warn))

        except Exception:
            pass
