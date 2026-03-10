"""
Entry point voor MV3 (PySide6).
Toont direct een splash screen, laadt daarna alle modules en data.
"""
import sys
import ctypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Windows: eigen App ID zodat de taakbalk het NH90-icoon toont
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('MV.MaintenanceViewer.1')
except Exception:
    pass

# Alleen PySide6 basis - zo min mogelijk voor snelle splash
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

from ui.theme import SLATE_900, SLATE_800, SLATE_700, SLATE_400, SLATE_200, BLUE_700, WHITE


class SplashWidget(QWidget):
    """Simpel splash scherm met een indeterminate progress bar."""

    def __init__(self, assets: Path) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(520, 240)
        self.setStyleSheet(
            f"QWidget {{ background: {SLATE_900}; border: 1px solid {SLATE_700}; }}"
            f"QLabel#title {{ color: {WHITE}; font: 700 22px 'Segoe UI'; }}"
            f"QLabel#subtitle {{ color: {SLATE_400}; font: 11px 'Segoe UI'; }}"
            f"QLabel#status {{ color: {SLATE_200}; font: 10px 'Segoe UI'; }}"
            f"QProgressBar {{ border: 1px solid {SLATE_700}; border-radius: 3px; background: {SLATE_800}; height: 6px; }}"
            f"QProgressBar::chunk {{ background: {BLUE_700}; }}"
        )

        self._status = QLabel('Laden...')
        self._status.setObjectName('status')

        title = QLabel('Maintenance Viewer')
        title.setObjectName('title')
        subtitle = QLabel('MV3')
        subtitle.setObjectName('subtitle')

        logo_label = QLabel()
        logo_path = assets / 'NH90_Main.PNG'
        if logo_path.exists():
            logo = QPixmap(str(logo_path))
            if not logo.isNull():
                logo_label.setPixmap(logo.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation))

        text_layout = QVBoxLayout()
        text_layout.addStretch(1)
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        text_layout.addStretch(1)

        top = QHBoxLayout()
        top.addWidget(logo_label)
        top.addLayout(text_layout)
        top.addStretch(1)

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)  # indeterminate / busy
        self._bar.setTextVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.addLayout(top)
        layout.addStretch(1)
        layout.addWidget(self._status)
        layout.addWidget(self._bar)

    def set_status(self, text: str) -> None:
        self._status.setText(text)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName('MV App')
    app.setQuitOnLastWindowClosed(True)

    assets = Path(__file__).parent / 'assets'
    app.setWindowIcon(QIcon(str(assets / 'NH90_taskbar.ico')))

    # Splash direct tonen - voor zware imports
    splash = SplashWidget(assets)
    screen = app.primaryScreen()
    if screen is not None:
        geo = screen.availableGeometry()
        splash.move(
            geo.x() + (geo.width() - splash.width()) // 2,
            geo.y() + (geo.height() - splash.height()) // 2,
        )
    splash.show()
    app.processEvents()

    # Nu pas zware imports (PySide6 tabs, pandas, etc.)
    splash.set_status('Modules laden...')
    app.processEvents()

    from ui.main_window import MainWindow
    from data.loader import DataLoader
    import data.store as store_module

    splash.set_status('Interface bouwen...')
    app.processEvents()

    window = MainWindow()
    window.setWindowIcon(QIcon(str(assets / 'NH90_taskbar.ico')))
    window.showMaximized()
    window.raise_()
    window.activateWindow()

    splash.hide()

    window._initial_loader = DataLoader()
    window._initial_loader.finished.connect(window.on_data_loaded)
    window._initial_loader.finished.connect(lambda store: setattr(store_module, 'data', store))
    window._initial_loader.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
