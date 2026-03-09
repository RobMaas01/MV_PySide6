"""
Kleurconstanten en QSS-stijlen voor MV3 (PySide6).
Zelfde kleurpalet als MV2 (Tailwind slate/blue).
"""

# ---------------------------------------------------------------------------
# Kleurconstanten
# ---------------------------------------------------------------------------

SLATE_900 = '#26374e'
SLATE_800 = '#364a65'
SLATE_700 = '#4b627f'
SLATE_600 = '#6b83a1'
SLATE_400 = '#c0ccda'
SLATE_200 = '#e2e8f0'
SLATE_50  = '#f8fafc'
BLUE_700  = '#1d4ed8'
BLUE_600  = '#2563eb'
WHITE     = '#f8fafc'
RED_400   = '#f87171'

# ---------------------------------------------------------------------------
# QSS-stijlen
# ---------------------------------------------------------------------------

# Gehele applicatie
APP_QSS = f"""
    QMainWindow, QWidget {{
        background-color: {SLATE_900};
        color: {WHITE};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
    }}
    QScrollBar:vertical {{
        background: {SLATE_800};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {SLATE_600};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QStatusBar {{
        background-color: {SLATE_800};
        color: {SLATE_400};
        font-size: 11px;
        border-top: 1px solid {SLATE_700};
    }}
    QMessageBox {{
        background-color: {SLATE_800};
    }}
    QMessageBox QLabel {{
        color: {WHITE};
        background: transparent;
    }}
    QMessageBox QPushButton {{
        background-color: #c7d8e6;
        color: #1a1a1a;
        border: 1px solid #8aa7bf;
        border-radius: 4px;
        padding: 4px 10px;
        min-width: 70px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: #d6e3ee;
    }}
"""

# Sidebar nav-knop: inactief
NAV_BTN_QSS = f"""
    QPushButton {{
        text-align: left;
        padding: 8px 12px;
        border-radius: 5px;
        border: none;
        color: {WHITE};
        background-color: transparent;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {SLATE_700};
    }}
"""

# Sidebar nav-knop: actief
NAV_BTN_ACTIVE_QSS = f"""
    QPushButton {{
        text-align: left;
        padding: 8px 12px;
        border-radius: 5px;
        border: none;
        color: {WHITE};
        background-color: {BLUE_700};
        font-size: 13px;
        font-weight: bold;
    }}
"""

# Login invoerveld
INPUT_QSS = f"""
    QLineEdit {{
        background-color: {SLATE_900};
        color: {WHITE};
        border: 1px solid {SLATE_600};
        border-radius: 4px;
        padding: 7px 9px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 1px solid {BLUE_700};
    }}
"""

# Primaire knop
BTN_PRIMARY_QSS = f"""
    QPushButton {{
        background-color: {BLUE_700};
        color: {WHITE};
        border: none;
        border-radius: 4px;
        padding: 9px;
        font-size: 13px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {BLUE_600};
    }}
    QPushButton:pressed {{
        background-color: {SLATE_700};
    }}
"""

# Logout-knop (subtiel)
LOGOUT_BTN_QSS = f"""
    QPushButton {{
        text-align: left;
        padding: 7px 12px;
        border-radius: 5px;
        border: none;
        color: {SLATE_400};
        background-color: transparent;
        font-size: 12px;
    }}
    QPushButton:hover {{
        color: {WHITE};
        background-color: {SLATE_700};
    }}
"""
