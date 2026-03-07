"""
Login-dialoogvenster voor MV3.
Professioneel scherm met NH90-achtergrond, donkere overlay en login-kaart.
"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from auth.auth import check_credentials, ensure_user_exists
from ui.theme import (
    BLUE_600, BLUE_700, RED_400, SLATE_400,
    WHITE, INPUT_QSS, BTN_PRIMARY_QSS,
)

_BG_PATH = Path(__file__).parent.parent / 'assets' / 'nh90_app_background.jpg'


class LoginDialog(QDialog):
    """Modaal inlogvenster. Na accept() is self.username ingevuld."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.username: str = ''
        self._bg = QPixmap(str(_BG_PATH))
        self._build_ui()

    # ------------------------------------------------------------------
    # Achtergrond tekenen
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.width(), self.height(), self._bg)
        painter.fillRect(self.rect(), QColor(8, 18, 42, 175))
        painter.end()

    # ------------------------------------------------------------------
    # UI opbouw
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle('Maintenance Viewer')
        self.setFixedSize(820, 490)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- Links: branding ----
        left = QWidget()
        left.setStyleSheet('background: transparent;')
        lv = QVBoxLayout(left)
        lv.setContentsMargins(56, 0, 30, 0)
        lv.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_title = QLabel('Maintenance\nViewer')
        lbl_title.setStyleSheet(
            'color: white; font-size: 38px; font-weight: bold; '
            'background: transparent; line-height: 1.1;'
        )

        accent = QFrame()
        accent.setFixedSize(52, 4)
        accent.setStyleSheet(f'background: {BLUE_700}; border-radius: 2px;')

        lbl_sub = QLabel('NH90 Maintenance Dashboard')
        lbl_sub.setStyleSheet(
            'color: rgba(180,205,240,210); font-size: 14px; '
            'background: transparent;'
        )

        lbl_ver = QLabel('v3.0  ·  Koninklijke Luchtmacht')
        lbl_ver.setStyleSheet(
            f'color: {SLATE_400}; font-size: 11px; background: transparent;'
        )

        lv.addWidget(lbl_title)
        lv.addSpacing(14)
        lv.addWidget(accent)
        lv.addSpacing(12)
        lv.addWidget(lbl_sub)
        lv.addSpacing(4)
        lv.addWidget(lbl_ver)

        outer.addWidget(left, stretch=1)

        # ---- Rechts: login-kaart ----
        right_wrap = QWidget()
        right_wrap.setStyleSheet('background: transparent;')
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(20, 40, 48, 40)
        rv.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        card = QFrame()
        card.setFixedWidth(300)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #0c1628;
                border-radius: 12px;
                border: 1px solid rgba(100, 140, 200, 70);
            }}
            QLabel {{
                background: transparent;
                color: {WHITE};
            }}
        """)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 32, 30, 32)
        cl.setSpacing(6)

        lbl_card_title = QLabel('Sign In')
        lbl_card_title.setStyleSheet(
            'font-size: 20px; font-weight: bold; color: white; background: transparent;'
        )
        lbl_card_sub = QLabel('Enter your credentials')
        lbl_card_sub.setStyleSheet(
            f'font-size: 12px; color: {SLATE_400}; background: transparent;'
        )
        cl.addWidget(lbl_card_title)
        cl.addWidget(lbl_card_sub)
        cl.addSpacing(18)

        # Gebruikersnaam
        lbl_u = QLabel('Username')
        lbl_u.setStyleSheet(f'font-size: 11px; color: {SLATE_400}; background: transparent;')
        cl.addWidget(lbl_u)
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText('username')
        self._user_edit.setStyleSheet(INPUT_QSS)
        self._user_edit.returnPressed.connect(self._try_login)
        cl.addWidget(self._user_edit)
        cl.addSpacing(8)

        # Wachtwoord
        lbl_p = QLabel('Password')
        lbl_p.setStyleSheet(f'font-size: 11px; color: {SLATE_400}; background: transparent;')
        cl.addWidget(lbl_p)
        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_edit.setPlaceholderText('password')
        self._pass_edit.setStyleSheet(INPUT_QSS)
        self._pass_edit.returnPressed.connect(self._try_login)
        cl.addWidget(self._pass_edit)

        # Foutmelding
        self._error_lbl = QLabel('')
        self._error_lbl.setStyleSheet(
            f'font-size: 12px; color: {RED_400}; background: transparent;'
        )
        self._error_lbl.setVisible(False)
        cl.addWidget(self._error_lbl)
        cl.addSpacing(14)

        # Inloggen-knop
        btn = QPushButton('Sign In')
        btn.setStyleSheet(BTN_PRIMARY_QSS)
        btn.setFixedHeight(38)
        btn.clicked.connect(self._try_login)
        cl.addWidget(btn)

        rv.addWidget(card, alignment=Qt.AlignmentFlag.AlignVCenter)
        outer.addWidget(right_wrap)

        self._user_edit.setFocus()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------
    # Logica
    # ------------------------------------------------------------------

    def _try_login(self) -> None:
        username = self._user_edit.text().strip()
        password = self._pass_edit.text()

        if not username or not password:
            self._show_error('Please enter username and password.')
            return

        if check_credentials(username, password):
            ensure_user_exists(username)
            self.username = username
            self.accept()
        else:
            self._show_error('Incorrect username or password.')
            self._pass_edit.clear()
            self._pass_edit.setFocus()

    def _show_error(self, msg: str) -> None:
        self._error_lbl.setText(msg)
        self._error_lbl.setVisible(True)
