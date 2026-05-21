"""
LeerDisk - Entry Point
Handles UAC elevation and launches the main application.
"""

import ctypes
import os
import sys


def is_admin() -> bool:
    """Return True if the process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    """Re-launch this script with administrator privileges via ShellExecuteW."""
    script = os.path.abspath(__file__)
    args   = " ".join(f'"{a}"' for a in sys.argv[1:])
    params = f'"{script}" {args}'.strip()
    ctypes.windll.shell32.ShellExecuteW(
        None,            # hwnd
        "runas",         # verb  →  triggers UAC prompt
        sys.executable,  # file
        params,          # parameters
        None,            # working directory (inherit)
        1,               # SW_SHOWNORMAL
    )


def check_dependencies() -> bool:
    """Verify required third-party libraries are available."""
    missing = []
    for lib in ("customtkinter", "psutil"):
        try:
            __import__(lib)
        except ImportError:
            missing.append(lib)

    if missing:
        # tkinter is always available in CPython — use it for the error dialog
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "LeerDisk — Missing Libraries",
                "The following libraries are not installed:\n\n"
                + "\n".join(f"  •  {m}" for m in missing)
                + "\n\nPlease run  install.bat  and try again.",
            )
        except Exception:
            print(
                "ERROR: Missing libraries:", ", ".join(missing),
                "\nRun install.bat to install them.",
            )
        return False
    return True


def main():
    # ── Administrator check ──────────────────────────────────────────────────
    if not is_admin():
        elevate()
        sys.exit(0)

    # ── Dependency check ─────────────────────────────────────────────────────
    if not check_dependencies():
        sys.exit(1)

    # ── Launch app ───────────────────────────────────────────────────────────
    # Import here so missing-library errors are caught above first
    from app import LeerDiskApp  # noqa: PLC0415
    application = LeerDiskApp()
    application.mainloop()


if __name__ == "__main__":
    main()
