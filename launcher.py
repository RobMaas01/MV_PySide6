"""
MV3 Launcher — klein opstartprogramma.

Leest mv_config.ini naast de launcher-exe:

    [paths]
    app_dir    = .           # map waar MV3_app.exe + _internal staan
    datasource = datasource  # absoluut of relatief t.o.v. launcher
    settings   = settings    # absoluut of relatief t.o.v. launcher

Toont een laad-popup, start MV3_app.exe en sluit de popup zodra
de app klaar is (WaitForInputIdle).
"""
import configparser
import ctypes
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path


def _launcher_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _resolve(raw: str, base: Path) -> Path:
    p = Path(raw)
    return p if p.is_absolute() else base / p


def _read_config(launcher_dir: Path) -> dict:
    defaults = {'app_dir': '.', 'datasource': '', 'settings': ''}
    cfg = configparser.ConfigParser()
    p = launcher_dir / 'mv_config.ini'
    if p.exists():
        cfg.read(p, encoding='utf-8')
        if 'paths' in cfg:
            for k in defaults:
                if k in cfg['paths']:
                    defaults[k] = cfg['paths'][k].strip()
    return defaults


def _show_splash(root: tk.Tk) -> None:
    root.title('')
    root.overrideredirect(True)
    root.configure(bg='#0f172a')
    root.attributes('-topmost', True)
    w, h = 420, 110
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
    tk.Label(
        root, text='Maintenance Viewer', bg='#0f172a', fg='#f8fafc',
        font=('Segoe UI', 16, 'bold'),
    ).pack(pady=(22, 4))
    tk.Label(
        root, text='App wordt geladen\u2026', bg='#0f172a', fg='#94a3b8',
        font=('Segoe UI', 10),
    ).pack()
    root.update()


def main() -> None:
    ld = _launcher_dir()
    cfg = _read_config(ld)

    app_dir = _resolve(cfg['app_dir'] or '.', ld)
    app_exe = app_dir / 'MV3_app.exe'

    if not app_exe.exists():
        ctypes.windll.user32.MessageBoxW(
            0,
            f'MV3_app.exe niet gevonden:\n{app_exe}\n\nPas mv_config.ini aan.',
            'MV3 \u2014 Fout',
            0x10,
        )
        sys.exit(1)

    env = os.environ.copy()
    if cfg['datasource']:
        env['MV3_DATASOURCE'] = str(_resolve(cfg['datasource'], ld))
    if cfg['settings']:
        env['MV3_SETTINGS'] = str(_resolve(cfg['settings'], ld))

    root = tk.Tk()
    _show_splash(root)

    proc = subprocess.Popen([str(app_exe)], env=env, cwd=str(app_dir))

    def _wait_then_close() -> None:
        try:
            PROCESS_ALL_ACCESS = 0x1F0FFF
            h = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, proc.pid)
            if h:
                ctypes.windll.user32.WaitForInputIdle(h, 30_000)
                ctypes.windll.kernel32.CloseHandle(h)
        except Exception:
            import time
            time.sleep(6)
        root.after(0, root.destroy)

    threading.Thread(target=_wait_then_close, daemon=True).start()
    root.mainloop()


if __name__ == '__main__':
    main()
