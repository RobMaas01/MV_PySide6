"""
Entry point voor MV3 (PySide6).
Start de applicatie en toont het hoofdvenster.
Data wordt geladen in een achtergrond-thread na het openen van het hoofdvenster.
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

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
from data.loader import DataLoader
import data.store as store_module




def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName('MV App')
    app.setQuitOnLastWindowClosed(True)
    app.setWindowIcon(QIcon(str(Path(__file__).parent / 'assets' / 'NH90_taskbar.PNG')))

    window = MainWindow()
    window.showMaximized()
    window.raise_()
    window.activateWindow()

    window._initial_loader = DataLoader()
    window._initial_loader.finished.connect(window.on_data_loaded)
    window._initial_loader.finished.connect(lambda store: setattr(store_module, 'data', store))
    window._initial_loader.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
