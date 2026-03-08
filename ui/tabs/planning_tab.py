"""
Planning-tab: toon aankomende inspecties op basis van datum, vluchturen
en beoogd gebruik.
"""
import pandas as pd
from PySide6.QtCore import (
    Qt, QDate, QSize, QTimer, Signal,
    QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QPoint, QRect,
)
from PySide6.QtGui import QBrush, QColor, QFontMetrics, QIcon, QPainter, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox,
    QFrame, QGroupBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QStyledItemDelegate, QTableView, QVBoxLayout, QWidget,
)


class _CompactItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        sh = super().sizeHint(option, index)
        return sh.__class__(sh.width(), 20)


from ui.theme import SLATE_400, SLATE_900, SLATE_800, SLATE_700, SLATE_600, WHITE
from ui.tabs.overview_tab import (
    _BgDelegate, _TBL_QSS,
    TBL_BG, TBL_ALT, TBL_TEXT, TBL_BDR, NEG_BG, NEG_FG,
    AC_COL_HDR, AC_COL_BDR,
)

AMBER_BG  = '#f5e17a'
ORANGE_BG = '#f5a85e'

_EXPORT_BTN_QSS = """
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
    QPushButton:disabled { background: #4a5568; color: #94a3b8; border: 1px solid #4a5568; }
"""

_FILTER_QSS = f"""
    QLabel {{ color: {WHITE}; font-size: 10px; }}
    QComboBox, QDateEdit, QDoubleSpinBox {{
        background-color: {SLATE_700}; color: {WHITE}; border: 1px solid {SLATE_600};
        border-radius: 3px; padding: 1px 4px; font-size: 10px; max-height: 18px;
    }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{ background-color: {SLATE_700}; color: {WHITE}; selection-background-color: {SLATE_600}; }}
    QDateEdit::drop-down {{ background: #4a7da8; border-left: 1px solid #3a6a90; border-radius: 0 3px 3px 0; width: 20px; }}
    QDateEdit::drop-down:hover {{ background: #5b90bc; }}
    QDateEdit::down-arrow {{ width: 10px; height: 10px; }}
    QCalendarWidget QWidget {{ background: {SLATE_800}; color: {WHITE}; }}
    QCalendarWidget QToolButton {{ color: {WHITE}; background: {SLATE_700}; border: none; border-radius: 3px; padding: 3px 6px; font-size: 12px; }}
    QCalendarWidget QToolButton:hover {{ background: {SLATE_600}; }}
    QCalendarWidget QAbstractItemView {{ background: {SLATE_800}; color: {WHITE}; selection-background-color: {SLATE_600}; selection-color: {WHITE}; }}
    QCalendarWidget QAbstractItemView:disabled {{ color: {SLATE_600}; }}
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 16px; }}
    QGroupBox {{
        color: {WHITE}; font-size: 10px; font-weight: bold; border: 1px solid {SLATE_600};
        border-radius: 4px; margin-top: 7px; padding-top: 5px; background: {SLATE_800};
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 3px; color: {WHITE}; }}
"""


# ---------------------------------------------------------------------------
# Table model
# ---------------------------------------------------------------------------

class PlanningTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._df   = pd.DataFrame()
        self._cols: list[str] = []
        self._rest_col = -1
        self._date_col = -1

    def load(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df       = df.reset_index(drop=True)
        self._cols     = list(df.columns)
        self._rest_col = self._cols.index('Rest') if 'Rest' in self._cols else -1
        self._date_col = self._cols.index('Geplande datum') if 'Geplande datum' in self._cols else -1
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._cols)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        val  = self._df.iloc[r, c]
        text = '' if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)

        if role == Qt.ItemDataRole.DisplayRole:
            return text

        if role == Qt.ItemDataRole.UserRole:          # numeric sort key
            if c == self._date_col and text:
                try:
                    return pd.to_datetime(text, dayfirst=True).timestamp()
                except Exception:
                    return None
            try:
                return float(text) if text else None
            except ValueError:
                return None

        if role == Qt.ItemDataRole.BackgroundRole:
            if c == self._rest_col and text:
                try:
                    v = float(text)
                    if v < 0:    return QColor(NEG_BG)
                    if v <= 7:   return QColor(ORANGE_BG)
                    if v <= 30:  return QColor(AMBER_BG)
                except (ValueError, TypeError):
                    pass
            return QColor(TBL_BG) if r % 2 == 0 else QColor(TBL_ALT)

        if role == Qt.ItemDataRole.ForegroundRole:
            if c == self._rest_col and text:
                try:
                    if float(text) < 0:
                        return QColor(NEG_FG)
                except (ValueError, TypeError):
                    pass
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if c == self._rest_col:
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._cols[section] if section < len(self._cols) else ''
        return None

    def col_name(self, col: int) -> str:
        return self._cols[col] if 0 <= col < len(self._cols) else ''

    def full_df(self) -> pd.DataFrame:
        return self._df.copy()


# ---------------------------------------------------------------------------
# Sort / filter proxy
# ---------------------------------------------------------------------------

class MultiColumnFilterProxy(QSortFilterProxyModel):
    filtersChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters: dict[int, set] = {}
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def set_filter(self, col: int, allowed: set | None):
        if allowed is None:
            self._filters.pop(col, None)
        else:
            self._filters[col] = allowed
        self.invalidateFilter()
        self.filtersChanged.emit()

    def has_filter(self, col: int) -> bool:
        return col in self._filters

    def current_filter(self, col: int) -> set | None:
        return self._filters.get(col)

    def clear_all_filters(self):
        self._filters.clear()
        self.invalidateFilter()
        self.filtersChanged.emit()

    def unique_values(self, col: int) -> list[str]:
        model = self.sourceModel()
        if model is None:
            return []
        vals: set[str] = set()
        for r in range(model.rowCount()):
            v = model.data(model.index(r, col), Qt.ItemDataRole.DisplayRole)
            vals.add('' if v is None else str(v))
        try:
            return sorted(vals, key=lambda x: float(x) if x else float('-inf'))
        except ValueError:
            return sorted(vals, key=lambda x: (x == '', x.lower()))

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        for col, allowed in self._filters.items():
            v = model.data(model.index(source_row, col, source_parent), Qt.ItemDataRole.DisplayRole)
            if ('' if v is None else str(v)) not in allowed:
                return False
        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        lv = self.sourceModel().data(left,  Qt.ItemDataRole.UserRole)
        rv = self.sourceModel().data(right, Qt.ItemDataRole.UserRole)
        if lv is not None and rv is not None:
            try:
                return float(lv) < float(rv)
            except (ValueError, TypeError):
                pass
        ls = str(self.sourceModel().data(left,  Qt.ItemDataRole.DisplayRole) or '')
        rs = str(self.sourceModel().data(right, Qt.ItemDataRole.DisplayRole) or '')
        return ls.lower() < rs.lower()

    def visible_df(self) -> pd.DataFrame:
        model = self.sourceModel()
        if model is None or not hasattr(model, 'full_df'):
            return pd.DataFrame()
        src_df = model.full_df()
        rows = [self.mapToSource(self.index(r, 0)).row() for r in range(self.rowCount())]
        return src_df.iloc[rows].reset_index(drop=True) if rows else pd.DataFrame(columns=src_df.columns)


# ---------------------------------------------------------------------------
# Filter popup
# ---------------------------------------------------------------------------

class _FilterPopup(QFrame):
    applied = Signal(object)   # set[str] | None
    sorted  = Signal(int)      # Qt.SortOrder value

    def __init__(self, values: list[str], current: set | None, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName('filterPopup')
        self._all_values = values
        self.setStyleSheet(f"""
            QFrame#filterPopup {{
                background: {SLATE_800}; border: 1px solid {SLATE_600}; border-radius: 4px;
            }}
            QLineEdit {{
                background: {SLATE_700}; color: {WHITE}; border: 1px solid {SLATE_600};
                border-radius: 3px; padding: 2px 5px; font-size: 10px;
            }}
            QListWidget {{
                background: {SLATE_700}; color: {WHITE}; border: 1px solid {SLATE_600};
                font-size: 10px; outline: none;
            }}
            QListWidget::item {{ padding: 2px 6px; }}
            QListWidget::item:hover {{ background: {SLATE_600}; }}
            QPushButton {{
                background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #8aafc0,stop:1 #afc4d0);
                color: #1a1a1a; border: 1px solid #8aafc0; border-bottom: 2px solid #3a5a6e;
                border-radius: 4px; padding: 4px 12px; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #8aabb8,stop:1 #8aafc0); }}
            QCheckBox {{ color: {WHITE}; font-size: 10px; padding: 2px 4px; }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(4)

        # Sorteerknoppen
        sort_row = QHBoxLayout()
        sort_row.setSpacing(4)
        btn_asc  = QPushButton('↑  A → Z')
        btn_desc = QPushButton('↓  Z → A')
        btn_asc.setFixedHeight(22)
        btn_desc.setFixedHeight(22)
        btn_asc.clicked.connect(lambda: (
            self.sorted.emit(Qt.SortOrder.AscendingOrder.value), self.close()))
        btn_desc.clicked.connect(lambda: (
            self.sorted.emit(Qt.SortOrder.DescendingOrder.value), self.close()))
        sort_row.addWidget(btn_asc)
        sort_row.addWidget(btn_desc)
        v.addLayout(sort_row)

        # Zoekbalk (Enter = filter, leeg + Enter = reset)
        self._search = QLineEdit()
        self._search.setPlaceholderText('Bevat...  [Enter]')
        self._search.setFixedHeight(22)
        v.addWidget(self._search)

        self._chk_all = QCheckBox('(Select All)')
        v.addWidget(self._chk_all)

        self._lst = QListWidget()
        self._lst.setMaximumHeight(220)
        self._lst.setMinimumWidth(200)

        all_checked = current is None
        self._lst.blockSignals(True)
        for val in values:
            item = QListWidgetItem(val if val != '' else '(empty)')
            item.setData(Qt.ItemDataRole.UserRole, val)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = all_checked or (current is not None and val in current)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self._lst.addItem(item)
        self._lst.blockSignals(False)
        v.addWidget(self._lst)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        btn_ok     = QPushButton('OK')
        btn_cancel = QPushButton('Cancel')
        btn_ok.setFixedHeight(22)
        btn_cancel.setFixedHeight(22)
        btn_ok.clicked.connect(self._apply)
        btn_cancel.clicked.connect(self.close)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        v.addLayout(btn_row)

        self._search.returnPressed.connect(self._on_search)
        self._chk_all.stateChanged.connect(self._toggle_all)
        self._lst.itemChanged.connect(self._update_chk_all)
        self._update_chk_all()
        self.adjustSize()

    def _on_search(self):
        txt = self._search.text().lower()
        for i in range(self._lst.count()):
            item = self._lst.item(i)
            item.setHidden(bool(txt) and txt not in item.text().lower())
        self._update_chk_all()
        # Pas de tabelfilter direct toe op Enter
        if txt:
            visible = {self._lst.item(i).data(Qt.ItemDataRole.UserRole)
                       for i in range(self._lst.count())
                       if not self._lst.item(i).isHidden()}
            self.applied.emit(visible or None)
        else:
            self.applied.emit(None)
        self.close()

    def _toggle_all(self, state):
        if state == Qt.CheckState.PartiallyChecked.value:
            return
        ck = Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked
        self._lst.blockSignals(True)
        for i in range(self._lst.count()):
            if not self._lst.item(i).isHidden():
                self._lst.item(i).setCheckState(ck)
        self._lst.blockSignals(False)

    def _update_chk_all(self):
        visible = [self._lst.item(i) for i in range(self._lst.count()) if not self._lst.item(i).isHidden()]
        if not visible:
            return
        checked = sum(1 for it in visible if it.checkState() == Qt.CheckState.Checked)
        self._chk_all.blockSignals(True)
        if   checked == 0:          self._chk_all.setCheckState(Qt.CheckState.Unchecked)
        elif checked == len(visible): self._chk_all.setCheckState(Qt.CheckState.Checked)
        else:                        self._chk_all.setCheckState(Qt.CheckState.PartiallyChecked)
        self._chk_all.blockSignals(False)

    def _apply(self):
        n        = self._lst.count()
        selected = {self._lst.item(i).data(Qt.ItemDataRole.UserRole)
                    for i in range(n)
                    if self._lst.item(i).checkState() == Qt.CheckState.Checked}
        self.applied.emit(None if len(selected) == n else (selected or None))
        self.close()


# ---------------------------------------------------------------------------
# Custom header with per-column filter arrows
# ---------------------------------------------------------------------------

class FilterHeaderView(QHeaderView):
    filterArrowClicked = Signal(int, QPoint)

    _AW = 16   # arrow area width

    def __init__(self, proxy: MultiColumnFilterProxy, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._proxy = proxy
        self.setSectionsClickable(True)
        self.setHighlightSections(False)
        proxy.filtersChanged.connect(self.viewport().update)

    def paintSection(self, painter, rect, logical_index):
        super().paintSection(painter, rect, logical_index)
        painter.save()
        painter.setClipRect(rect)
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)
        ax = rect.right() - self._AW + 4
        cy = rect.center().y()
        pts = QPolygon([QPoint(ax, cy - 2), QPoint(ax + 8, cy - 2), QPoint(ax + 4, cy + 3)])
        color = QColor('#5b90bc') if self._proxy.has_filter(logical_index) else QColor('#6a7f90')
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(pts)
        painter.restore()

    def mousePressEvent(self, event):
        logical = self.logicalIndexAt(event.pos())
        if logical >= 0:
            x = self.sectionViewportPosition(logical)
            w = self.sectionSize(logical)
            if QRect(x + w - self._AW, 0, self._AW, self.height()).contains(event.pos()):
                self.filterArrowClicked.emit(logical, event.globalPosition().toPoint())
                return
        super().mousePressEvent(event)


def _make_clear_filter_icon(size: int = 18) -> QIcon:
    """Filter-off icoon: trechter met diagonale rode streep."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    # Trechter (funnel) in slate-blauw
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor('#6a9ab8')))
    pts = QPolygon([
        QPoint(1, 2), QPoint(s - 1, 2),
        QPoint(s // 2 + 2, s // 2 - 1),
        QPoint(s // 2 + 2, s - 2),
        QPoint(s // 2 - 2, s - 2),
        QPoint(s // 2 - 2, s // 2 - 1),
    ])
    p.drawPolygon(pts)
    # Diagonale streep (filter = uit)
    from PySide6.QtGui import QPen as _QPen
    p.setPen(_QPen(QColor('#e05050'), 2.2, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap))
    p.drawLine(s - 3, 1, 1, s - 2)
    p.end()
    return QIcon(pm)


# ---------------------------------------------------------------------------
# Planning tab
# ---------------------------------------------------------------------------

class PlanningTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._df_cal:   pd.DataFrame | None = None
        self._df_cyc:   pd.DataFrame | None = None
        self._sys_vars: dict = {}
        self._df_usage: pd.DataFrame = pd.DataFrame()
        self._last_col_signature: tuple[str, ...] | None = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._do_refresh)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.setStyleSheet(f'background: {SLATE_900};')
        main = QVBoxLayout(self)
        main.setContentsMargins(8, 6, 6, 6)
        main.setSpacing(4)

        # Top row
        top_container = QWidget()
        top_row = QHBoxLayout(top_container)
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{ background: {SLATE_800}; border-radius: 4px; border: 1px solid {SLATE_600}; }}
        """ + _FILTER_QSS)
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(8, 4, 8, 4)
        fl.setSpacing(10)

        ac_box = QVBoxLayout()
        ac_box.setSpacing(2)
        ac_box.setContentsMargins(0, 14, 0, 0)
        ac_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        ac_lbl = QLabel('Aircraft')
        ac_lbl.setFixedHeight(14)
        ac_lbl.setStyleSheet('font-size: 12px; color: white;')
        ac_box.addWidget(ac_lbl)
        ac_box.addWidget(self._make_combo())
        fl.addLayout(ac_box)

        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(2)
        for r, (lbl_text, factory) in enumerate([
            ('Until date:',     self._make_date),
            ('Flight hours:',   self._make_spin_hours),
            ('Weeks on board:', self._make_spin_weeks),
        ]):
            lbl = QLabel(lbl_text)
            lbl.setFixedWidth(100)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(lbl, r, 0)
            grid.addWidget(factory(), r, 1)
        gw = QVBoxLayout()
        gw.setSpacing(0)
        gw.addLayout(grid)
        fl.addLayout(gw)
        top_row.addWidget(filter_frame)

        usage_group = QGroupBox('Intended use')
        usage_group.setStyleSheet(_FILTER_QSS)
        ug = QVBoxLayout(usage_group)
        ug.setContentsMargins(4, 2, 4, 2)
        self._usage_widget = QWidget()
        self._usage_grid   = QGridLayout(self._usage_widget)
        self._usage_grid.setContentsMargins(0, 0, 0, 0)
        self._usage_grid.setHorizontalSpacing(1)
        self._usage_grid.setVerticalSpacing(1)
        self._usage_edits: dict[str, QLineEdit] = {}
        ug.addWidget(self._usage_widget, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        ug.addStretch()
        top_row.addWidget(usage_group, stretch=1)
        main.addWidget(top_container)

        # Info bar
        info_bar = QWidget()
        info_bar.setFixedHeight(50)
        info_bar.setStyleSheet(f'background: {SLATE_800}; border-radius: 4px;')
        ib = QHBoxLayout(info_bar)
        ib.setContentsMargins(10, 0, 10, 0)
        ib.setSpacing(12)
        self._lbl_count = QLabel('No inspections loaded')
        self._lbl_count.setStyleSheet(f'color: {WHITE}; font-size: 11px; background: transparent;')
        ib.addWidget(self._lbl_count)
        ib.addSpacing(75)  # ~2 cm
        self._btn_clear_filter = QPushButton()
        self._btn_clear_filter.setIcon(_make_clear_filter_icon(16))
        self._btn_clear_filter.setToolTip('Verwijder alle filters')
        self._btn_clear_filter.setFixedSize(22, 22)
        self._btn_clear_filter.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; }}
            QPushButton:hover {{ background: rgba(255,255,255,30); border-radius: 3px; }}
        """)
        # verbinding na proxy-aanmaak
        ib.addWidget(self._btn_clear_filter)
        ib.addStretch()
        self._btn_export = QPushButton('')
        self._btn_export.setStyleSheet(_EXPORT_BTN_QSS)
        self._btn_export.setFixedSize(40, 32)
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._export_xls)
        try:
            import tempfile, os
            from PySide6.QtWidgets import QFileIconProvider
            from PySide6.QtCore import QFileInfo
            _t = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
            _t.close()
            self._btn_export.setIcon(QFileIconProvider().icon(QFileInfo(_t.name)))
            self._btn_export.setIconSize(QSize(26, 26))
            os.unlink(_t.name)
        except Exception:
            pass
        ib.addWidget(self._btn_export)
        # Table
        self._model = PlanningTableModel(self)
        self._proxy = MultiColumnFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.filtersChanged.connect(self._update_count)
        self._btn_clear_filter.clicked.connect(self._proxy.clear_all_filters)

        self._tbl = QTableView()
        self._tbl.setStyleSheet(
            _TBL_QSS
            + f'QTableView {{ color: {TBL_TEXT}; gridline-color: {TBL_BDR}; }}'
            + f'QTableView::item {{ color: {TBL_TEXT}; background-color: {TBL_BG}; padding-left: 4px; padding-right: 4px; }}'
        )
        self._tbl.setModel(self._proxy)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.verticalHeader().setDefaultSectionSize(18)
        self._tbl.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self._tbl.setAlternatingRowColors(False)
        self._tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tbl.setSortingEnabled(True)

        self._hdr = FilterHeaderView(self._proxy, self._tbl)
        self._hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hdr.setFixedHeight(28)
        self._tbl.setHorizontalHeader(self._hdr)
        self._hdr.filterArrowClicked.connect(self._show_filter_popup)

        # Info bar + tabel samen verschoven (~2cm)
        right_col = QVBoxLayout()
        right_col.setContentsMargins(50, 0, 0, 0)
        right_col.setSpacing(4)
        right_col.addWidget(info_bar)
        right_col.addWidget(self._tbl, stretch=1)
        main.addLayout(right_col, stretch=1)

    def _make_combo(self) -> QComboBox:
        self._combo_ac = QComboBox()
        self._combo_ac.setFixedWidth(95)
        self._combo_ac.setMaxVisibleItems(30)
        self._combo_ac.setItemDelegate(_CompactItemDelegate(self._combo_ac))
        self._combo_ac.setStyleSheet("""
            QComboBox { font-size: 12px; background-color: #d0d0d0; color: #1a1a1a; padding: 1px 4px; max-height: 20px; }
            QComboBox QAbstractItemView { font-size: 13px; background-color: #d0d0d0; color: #1a1a1a; selection-background-color: #a0a8b0; }
        """)
        self._combo_ac.currentTextChanged.connect(self._refresh)
        return self._combo_ac

    def _make_date(self) -> QDateEdit:
        self._date_edit = QDateEdit()
        self._date_edit.setDisplayFormat('dd MMM yyyy')
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate().addDays(90))
        self._date_edit.setFixedSize(115, 18)
        self._date_edit.dateChanged.connect(self._refresh)
        return self._date_edit

    def _make_spin_hours(self) -> QDoubleSpinBox:
        self._spin_hours = QDoubleSpinBox()
        self._spin_hours.setRange(0, 9999)
        self._spin_hours.setDecimals(1)
        self._spin_hours.setSingleStep(5)
        self._spin_hours.setSpecialValueText('-')
        self._spin_hours.setValue(0)
        self._spin_hours.setFixedSize(80, 18)
        self._spin_hours.valueChanged.connect(self._on_hours_changed)
        return self._spin_hours

    def _make_spin_weeks(self) -> QDoubleSpinBox:
        self._spin_weeks = QDoubleSpinBox()
        self._spin_weeks.setRange(0, 52)
        self._spin_weeks.setDecimals(1)
        self._spin_weeks.setSingleStep(1)
        self._spin_weeks.setSpecialValueText('-')
        self._spin_weeks.setValue(0)
        self._spin_weeks.setFixedSize(80, 18)
        self._spin_weeks.valueChanged.connect(self._on_weeks_changed)
        return self._spin_weeks

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def load_data(self, aircraft_list: list, df_cal: pd.DataFrame,
                  df_cyc: pd.DataFrame, sys_vars: dict) -> None:
        # Cache datetime parsing once; avoids repeated parsing on aircraft switch.
        self._df_cal   = df_cal.copy()
        if self._df_cal is not None and not self._df_cal.empty and 'Geplande datum_dt' not in self._df_cal.columns:
            self._df_cal['Geplande datum_dt'] = pd.to_datetime(
                self._df_cal['Geplande datum'], format='%d-%m-%Y', errors='coerce'
            )
        self._df_cyc   = df_cyc
        self._sys_vars = sys_vars
        from data.planning_processor import get_usage_items
        self._df_usage = get_usage_items(sys_vars)
        self._populate_usage_table()
        self._combo_ac.blockSignals(True)
        self._combo_ac.clear()
        self._combo_ac.addItems(aircraft_list)
        self._combo_ac.blockSignals(False)
        self._schedule_refresh(0)

    # ------------------------------------------------------------------
    # Intended use table
    # ------------------------------------------------------------------

    def _populate_usage_table(self):
        items   = self._sys_vars.get('GlimsCycles', {})
        df_full = pd.DataFrame.from_dict(items, orient='index')
        df_full = df_full.loc[
            (df_full['inSAP'] == True) & (df_full['viewID'] > 0)
        ].sort_values('viewID')
        if df_full.empty:
            return
        for i in reversed(range(self._usage_grid.count())):
            w = self._usage_grid.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._usage_edits.clear()
        groups: dict[int, list] = {}
        for _, row in df_full.iterrows():
            groups.setdefault(int(float(row['viewID'])), []).append(row)
        kenmerk_val = {row['kenmerk']: row['gebruik'] for _, row in self._df_usage.iterrows()}
        LBL_W, VAL_W, ROW_H = 100, 46, 16
        for g_idx, (_, items_in_group) in enumerate(sorted(groups.items())):
            col_k, col_v = g_idx * 2, g_idx * 2 + 1
            for r, row in enumerate(items_in_group):
                naam    = str(row['naam']) if 'naam' in row.index and pd.notna(row.get('naam')) else str(row.name)
                kenmerk = str(row['kenmerk'])
                lbl = QLabel()
                lbl.setFixedSize(LBL_W, ROW_H)
                lbl.setText(QFontMetrics(lbl.font()).elidedText(naam, Qt.TextElideMode.ElideRight, LBL_W - 6))
                lbl.setToolTip(naam)
                lbl.setStyleSheet(f'background:{SLATE_800}; color:{WHITE}; font-size:9px; padding:1px 3px;')
                self._usage_grid.addWidget(lbl, r, col_k)
                val = kenmerk_val.get(kenmerk)
                le  = QLineEdit('' if val is None else str(val))
                le.setFixedSize(VAL_W, ROW_H)
                le.setStyleSheet(f'background:{TBL_BG}; color:#1e293b; border:1px solid {SLATE_600}; font-size:9px; padding:1px 2px;')
                le.editingFinished.connect(self._on_usage_changed)
                self._usage_edits[kenmerk] = le
                self._usage_grid.addWidget(le, r, col_v)

    def _get_flat_usage(self) -> dict:
        flat = {}
        for kenmerk, le in self._usage_edits.items():
            t = le.text().strip()
            try:
                flat[kenmerk] = float(t) if t else None
            except ValueError:
                flat[kenmerk] = None
        return flat

    def _update_usage_display(self):
        kv = {row['kenmerk']: row['gebruik'] for _, row in self._df_usage.iterrows()}
        for kenmerk, le in self._usage_edits.items():
            val = kv.get(kenmerk)
            le.blockSignals(True)
            le.setText('' if val is None else str(val))
            le.blockSignals(False)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_hours_changed(self, hours):
        fh = hours if hours > 0 else None
        wk = self._spin_weeks.value() if self._spin_weeks.value() > 0 else None
        if not self._df_usage.empty:
            from data.planning_processor import calculate_usage
            self._df_usage = calculate_usage(self._df_usage, fh, wk)
            self._update_usage_display()
        self._schedule_refresh(0)

    def _on_weeks_changed(self, weeks):
        fh = self._spin_hours.value() if self._spin_hours.value() > 0 else None
        wk = weeks if weeks > 0 else None
        if not self._df_usage.empty:
            from data.planning_processor import calculate_usage
            self._df_usage = calculate_usage(self._df_usage, fh, wk)
            self._update_usage_display()
        self._schedule_refresh(0)

    def _on_usage_changed(self):
        self._schedule_refresh(0)

    # ------------------------------------------------------------------
    # Refresh / populate
    # ------------------------------------------------------------------

    def _schedule_refresh(self, delay_ms: int = 20):
        self._refresh_timer.start(max(0, int(delay_ms)))

    def _refresh(self):
        # Backward-compatible wrapper for existing signal connections.
        self._schedule_refresh(20)

    def _do_refresh(self):
        if self._df_cal is None or self._df_cyc is None:
            return
        aircraft = self._combo_ac.currentText()
        if not aircraft:
            return
        from data.planning_processor import get_planning_inspections
        df = get_planning_inspections(
            aircraft,
            self._date_edit.date().toString('yyyy-MM-dd'),
            self._spin_hours.value() if self._spin_hours.value() > 0 else None,
            self._get_flat_usage(),
            self._df_cal, self._df_cyc,
        )
        self._populate_table(df)

    def _populate_table(self, df: pd.DataFrame):
        self._proxy.clear_all_filters()
        self._model.load(df)
        if df.empty:
            self._lbl_count.setText('No inspections found')
            self._btn_export.setEnabled(False)
            return
        sig = tuple(df.columns)
        if sig != self._last_col_signature:
            QTimer.singleShot(0, self._tbl.resizeColumnsToContents)
            self._last_col_signature = sig
        self._update_count()
        self._btn_export.setEnabled(True)

    def _update_count(self):
        aircraft = self._combo_ac.currentText()
        visible  = self._proxy.rowCount()
        total    = self._model.rowCount()
        if visible == total:
            self._lbl_count.setText(
                f'Aircraft: {aircraft}  \u2022  {total} inspection{"s" if total != 1 else ""} found'
            )
        else:
            self._lbl_count.setText(
                f'Aircraft: {aircraft}  \u2022  {visible} of {total} inspections shown'
            )

    # ------------------------------------------------------------------
    # Filter popup
    # ------------------------------------------------------------------

    def _show_filter_popup(self, col: int, pos: QPoint):
        popup = _FilterPopup(
            self._proxy.unique_values(col),
            self._proxy.current_filter(col),
            self,
        )
        popup.applied.connect(lambda sel, c=col: self._proxy.set_filter(c, sel))
        popup.sorted.connect(lambda order, c=col: self._tbl.sortByColumn(
            c, Qt.SortOrder(order)))
        popup.adjustSize()
        popup.move(pos.x() - popup.width() // 2, pos.y() + 4)
        popup.show()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_xls(self):
        import os, tempfile
        df = self._proxy.visible_df()
        if df.empty:
            return
        aircraft = self._combo_ac.currentText()
        path = os.path.join(tempfile.gettempdir(), f'Planning_{aircraft}.xlsx')
        from export.xls_export import export_planning_xls
        export_planning_xls(df, aircraft, path)
        os.startfile(path)
