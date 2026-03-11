"""
Entry point voor MV3 (PySide6).
Start direct de main window; de splash wordt getoond door de launcher (MV3.exe).
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


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName('MV App')
    app.setQuitOnLastWindowClosed(True)

    assets = Path(__file__).parent / 'assets'
    app.setWindowIcon(QIcon(str(assets / 'NH90_taskbar.ico')))

    from ui.main_window import MainWindow
    from data.loader import DataLoader
    import data.store as store_module

    window = MainWindow()
    window.setWindowIcon(QIcon(str(assets / 'NH90_taskbar.ico')))
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
