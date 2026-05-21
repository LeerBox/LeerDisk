"""
LeerDisk - Core Cleaning Engine
Defines all system cleaning categories and performs safe disk cleanup.
"""

import os
import glob
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Callable

from utils import (
    format_bytes,
    get_folder_size,
    get_file_size,
    safe_remove_file,
    safe_remove_dir_contents,
    safe_remove_tree,
)

# ──────────────────────────────────────────────────────────────────────────────
# Data Model
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CleanCategory:
    key:              str
    name:             str
    description:      str
    icon:             str  = "🗑"
    enabled:          bool = True
    requires_restart: bool = False
    # Populated after scan
    scan_size:        int  = 0
    scan_count:       int  = 0
    # Populated after clean
    cleaned_size:     int  = 0


# ──────────────────────────────────────────────────────────────────────────────
# Engine
# ──────────────────────────────────────────────────────────────────────────────

class DiskCleaner:
    """Manages all cleaning categories and executes cleanup operations."""

    # Resolve common environment variables once at class level
    _WINDIR       = os.environ.get("WINDIR",       r"C:\Windows")
    _USERPROFILE  = os.environ.get("USERPROFILE",  r"C:\Users\Default")
    _LOCAL_APP    = os.environ.get("LOCALAPPDATA", "")
    _APP_DATA     = os.environ.get("APPDATA",      "")
    _TEMP         = os.environ.get("TEMP",         "")

    def __init__(self):
        self.categories: List[CleanCategory] = self._build_categories()

    # ── Category definitions ──────────────────────────────────────────────────

    def _build_categories(self) -> List[CleanCategory]:
        return [
            CleanCategory(
                "temp_user",
                "User Temp Files",
                "Temporary files created by applications in your user profile",
                icon="\uE8B7",  # Folder
            ),
            CleanCategory(
                "temp_windows",
                "Windows Temp Files",
                "System temporary files stored in C:\\Windows\\Temp",
                icon="\uE770",  # Windows logo
            ),
            CleanCategory(
                "prefetch",
                "Prefetch Files",
                "Application launch cache — safe to delete, rebuilt automatically",
                icon="\uEC4A",  # Speed High
            ),
            CleanCategory(
                "windows_update",
                "Windows Update Cache",
                "Downloaded update packages — can be re-downloaded if needed",
                icon="\uE895",  # Sync
            ),
            CleanCategory(
                "delivery_optim",
                "Delivery Optimization Cache",
                "Peer-to-peer update delivery files stored locally",
                icon="\uE896",  # Download
            ),
            CleanCategory(
                "error_reports",
                "Windows Error Reports",
                "Crash reports and diagnostic error files",
                icon="\uE7BA",  # Warning
            ),
            CleanCategory(
                "memory_dump",
                "Memory Dump Files",
                "BSOD crash memory dump files (MEMORY.DMP, Minidump)",
                icon="\uE8F1",  # Processing / CPU
            ),
            CleanCategory(
                "recycle_bin",
                "Recycle Bin",
                "Permanently delete all files currently in the Recycle Bin",
                icon="\uE948",  # Recycle Bin
            ),
            CleanCategory(
                "thumbnails",
                "Thumbnail Cache",
                "Windows Explorer image thumbnail database files",
                icon="\uEB9F",  # Photo
            ),
            CleanCategory(
                "system_logs",
                "System Log Files",
                "CBS, DISM, MoSetup, and INF setup log files",
                icon="\uE8A5",  # Page
            ),
            CleanCategory(
                "old_windows",
                "Old Windows Installations",
                "Windows.old, $Windows.~BT, $Windows.~WS — leftover upgrade folders",
                icon="\uECAD",  # Archive
            ),
            CleanCategory(
                "recent_files",
                "Recent Files History",
                "Windows Quick Access recent files and jump-list entries",
                icon="\uE823",  # History / Clock
            ),
            CleanCategory(
                "dns_cache",
                "DNS Cache",
                "Flush the DNS resolver cache (fixes some network issues)",
                icon="\uE774",  # Globe
            ),
            CleanCategory(
                "clipboard",
                "Clipboard Contents",
                "Clear the current Windows clipboard",
                icon="\uF0E3",  # Clipboard
            ),
            CleanCategory(
                "font_cache",
                "Font Cache",
                "Windows font cache database — rebuilt automatically on next boot",
                icon="\uE8D2",  # Font
                requires_restart=True,
            ),
            CleanCategory(
                "icon_cache",
                "Icon Cache",
                "Windows icon cache database — rebuilt automatically",
                icon="\uE790",  # Colors
                requires_restart=True,
            ),
            CleanCategory(
                "windows_installer",
                "Windows Installer Logs",
                "MSI installer log files left behind after software installation",
                icon="\uE8F4",  # Package
            ),
        ]

    # ── Lookup helper ─────────────────────────────────────────────────────────

    def get_category(self, key: str) -> Optional[CleanCategory]:
        for cat in self.categories:
            if cat.key == key:
                return cat
        return None

    # ── Scanning ──────────────────────────────────────────────────────────────

    def scan_all(
        self,
        progress_callback: Optional[Callable[["CleanCategory"], None]] = None,
    ) -> int:
        """Scan every category and return total bytes found."""
        total = 0
        for cat in self.categories:
            size, count = self._scan(cat)
            cat.scan_size  = size
            cat.scan_count = count
            total += size
            if progress_callback:
                progress_callback(cat)
        return total

    def scan_single(self, key: str) -> Tuple[int, int]:
        """Scan one category by key.  Returns (bytes, file_count)."""
        cat = self.get_category(key)
        if not cat:
            return 0, 0
        size, count = self._scan(cat)
        cat.scan_size  = size
        cat.scan_count = count
        return size, count

    def _scan(self, cat: CleanCategory) -> Tuple[int, int]:  # noqa: C901
        k = cat.key
        W = self._WINDIR
        L = self._LOCAL_APP
        A = self._APP_DATA
        U = self._USERPROFILE
        T = self._TEMP

        size, count = 0, 0

        if k == "temp_user":
            for p in {T, os.path.join(L, "Temp")}:
                s, c = get_folder_size(p)
                size += s; count += c

        elif k == "temp_windows":
            s, c = get_folder_size(os.path.join(W, "Temp"))
            size += s; count += c

        elif k == "prefetch":
            s, c = get_folder_size(os.path.join(W, "Prefetch"))
            size += s; count += c

        elif k == "windows_update":
            s, c = get_folder_size(os.path.join(W, "SoftwareDistribution", "Download"))
            size += s; count += c

        elif k == "delivery_optim":
            for p in [
                os.path.join(W, "SoftwareDistribution", "DeliveryOptimization"),
                os.path.join(L, "Microsoft", "Windows", "DeliveryOptimization"),
            ]:
                s, c = get_folder_size(p)
                size += s; count += c

        elif k == "error_reports":
            for p in [
                os.path.join(L, "Microsoft", "Windows", "WER"),
                os.path.join(U, "AppData", "Local", "CrashDumps"),
                r"C:\ProgramData\Microsoft\Windows\WER",
            ]:
                s, c = get_folder_size(p)
                size += s; count += c

        elif k == "memory_dump":
            dump = os.path.join(W, "MEMORY.DMP")
            if os.path.isfile(dump):
                size += get_file_size(dump); count += 1
            s, c = get_folder_size(os.path.join(W, "Minidump"))
            size += s; count += c

        elif k == "recycle_bin":
            import string
            for letter in string.ascii_uppercase:
                rb = f"{letter}:\\$Recycle.Bin"
                if os.path.isdir(rb):
                    s, c = get_folder_size(rb)
                    size += s; count += c

        elif k == "thumbnails":
            thumb_dir = os.path.join(L, "Microsoft", "Windows", "Explorer")
            for f in glob.glob(os.path.join(thumb_dir, "thumbcache_*.db")):
                size += get_file_size(f); count += 1

        elif k == "system_logs":
            for p in [
                os.path.join(W, "Logs", "CBS"),
                os.path.join(W, "Logs", "DISM"),
                os.path.join(W, "Logs", "MoSetup"),
            ]:
                s, c = get_folder_size(p)
                size += s; count += c
            inf_dir = os.path.join(W, "inf")
            for f in glob.glob(os.path.join(inf_dir, "*.log")):
                size += get_file_size(f); count += 1

        elif k == "old_windows":
            for p in [r"C:\Windows.old", r"C:\$Windows.~BT", r"C:\$Windows.~WS"]:
                s, c = get_folder_size(p)
                size += s; count += c

        elif k == "recent_files":
            rf = os.path.join(A, "Microsoft", "Windows", "Recent")
            s, c = get_folder_size(rf)
            size += s; count += c

        elif k in ("dns_cache", "clipboard"):
            # Action-only categories — no measurable size
            size, count = 0, 0

        elif k == "font_cache":
            for p in [
                os.path.join(L, "Microsoft", "Windows", "Fonts"),
                os.path.join(
                    W, "ServiceProfiles", "LocalService",
                    "AppData", "Local", "FontCache"
                ),
            ]:
                s, c = get_folder_size(p)
                size += s; count += c

        elif k == "icon_cache":
            ic = os.path.join(L, "Microsoft", "Windows", "Explorer", "iconcache_*.db")
            for f in glob.glob(ic):
                size += get_file_size(f); count += 1

        elif k == "windows_installer":
            inst_dir = os.path.join(W, "Temp")
            for f in glob.glob(os.path.join(inst_dir, "*.log")):
                size += get_file_size(f); count += 1
            msi_log = os.path.join(L, "Temp")
            for f in glob.glob(os.path.join(msi_log, "*.log")):
                size += get_file_size(f); count += 1

        return size, count

    # ── Cleaning ──────────────────────────────────────────────────────────────

    def clean_category(
        self,
        key: str,
        progress_callback: Optional[Callable] = None,
    ) -> Tuple[int, List[str]]:
        """
        Clean one category.  Returns (bytes_freed, list_of_error_strings).
        """
        cat = self.get_category(key)
        if not cat:
            return 0, [f"Unknown category: {key}"]

        freed  = 0
        errors: List[str] = []
        k = key
        W = self._WINDIR
        L = self._LOCAL_APP
        A = self._APP_DATA
        U = self._USERPROFILE
        T = self._TEMP

        def _rm_dir(path: str):
            nonlocal freed
            freed += safe_remove_dir_contents(path)

        def _rm_file(path: str):
            nonlocal freed
            ok, sz = safe_remove_file(path)
            if ok:
                freed += sz

        if k == "temp_user":
            for p in {T, os.path.join(L, "Temp")}:
                _rm_dir(p)

        elif k == "temp_windows":
            _rm_dir(os.path.join(W, "Temp"))

        elif k == "prefetch":
            _rm_dir(os.path.join(W, "Prefetch"))

        elif k == "windows_update":
            _rm_dir(os.path.join(W, "SoftwareDistribution", "Download"))

        elif k == "delivery_optim":
            for p in [
                os.path.join(W, "SoftwareDistribution", "DeliveryOptimization"),
                os.path.join(L, "Microsoft", "Windows", "DeliveryOptimization"),
            ]:
                _rm_dir(p)

        elif k == "error_reports":
            for p in [
                os.path.join(L, "Microsoft", "Windows", "WER"),
                os.path.join(U, "AppData", "Local", "CrashDumps"),
                r"C:\ProgramData\Microsoft\Windows\WER",
            ]:
                _rm_dir(p)

        elif k == "memory_dump":
            _rm_file(os.path.join(W, "MEMORY.DMP"))
            _rm_dir(os.path.join(W, "Minidump"))

        elif k == "recycle_bin":
            try:
                subprocess.run(
                    ["PowerShell", "-NoProfile", "-Command",
                     "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                    capture_output=True, timeout=30,
                )
                freed += cat.scan_size  # approximate
            except Exception as e:
                errors.append(str(e))

        elif k == "thumbnails":
            thumb_dir = os.path.join(L, "Microsoft", "Windows", "Explorer")
            for f in glob.glob(os.path.join(thumb_dir, "thumbcache_*.db")):
                ok, sz = safe_remove_file(f)
                if ok:
                    freed += sz
                else:
                    errors.append(f"Locked (explorer running?): {f}")

        elif k == "system_logs":
            for p in [
                os.path.join(W, "Logs", "CBS"),
                os.path.join(W, "Logs", "DISM"),
                os.path.join(W, "Logs", "MoSetup"),
            ]:
                _rm_dir(p)
            inf_dir = os.path.join(W, "inf")
            for f in glob.glob(os.path.join(inf_dir, "*.log")):
                ok, sz = safe_remove_file(f)
                if ok:
                    freed += sz

        elif k == "old_windows":
            for p in [r"C:\Windows.old", r"C:\$Windows.~BT", r"C:\$Windows.~WS"]:
                freed += safe_remove_tree(p)

        elif k == "recent_files":
            rf = os.path.join(A, "Microsoft", "Windows", "Recent")
            _rm_dir(rf)

        elif k == "dns_cache":
            try:
                subprocess.run(
                    ["ipconfig", "/flushdns"],
                    capture_output=True, timeout=15,
                )
            except Exception as e:
                errors.append(str(e))

        elif k == "clipboard":
            try:
                subprocess.run(
                    ["PowerShell", "-NoProfile", "-Command",
                     "Set-Clipboard -Value $null"],
                    capture_output=True, timeout=10,
                )
            except Exception as e:
                errors.append(str(e))

        elif k == "font_cache":
            for p in [
                os.path.join(L, "Microsoft", "Windows", "Fonts"),
                os.path.join(
                    W, "ServiceProfiles", "LocalService",
                    "AppData", "Local", "FontCache"
                ),
            ]:
                _rm_dir(p)

        elif k == "icon_cache":
            ic_pattern = os.path.join(L, "Microsoft", "Windows", "Explorer", "iconcache_*.db")
            for f in glob.glob(ic_pattern):
                ok, sz = safe_remove_file(f)
                if ok:
                    freed += sz

        elif k == "windows_installer":
            for pattern in [
                os.path.join(W, "Temp", "*.log"),
                os.path.join(L, "Temp", "*.log"),
            ]:
                for f in glob.glob(pattern):
                    ok, sz = safe_remove_file(f)
                    if ok:
                        freed += sz

        cat.cleaned_size = freed
        if progress_callback:
            progress_callback(cat)
        return freed, errors

    def clean_selected(
        self,
        keys: List[str],
        progress_callback: Optional[Callable[["CleanCategory", int], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        Clean multiple categories.
        Returns (total_freed_bytes, count_cleaned, all_errors).
        """
        total_freed = 0
        cats_done   = 0
        all_errors: List[str] = []

        for key in keys:
            freed, errs = self.clean_category(key)
            total_freed += freed
            cats_done   += 1
            all_errors.extend(errs)
            if progress_callback:
                progress_callback(self.get_category(key), freed)

        return total_freed, cats_done, all_errors
