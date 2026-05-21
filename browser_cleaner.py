"""
LeerDisk - Browser Cache Cleaner
Detects and cleans cache data for Chrome, Edge, Firefox, Brave, and Opera.
"""

import os
import glob
from dataclasses import dataclass, field
from typing import List, Tuple

from utils import get_folder_size, get_file_size, safe_remove_file, safe_remove_dir_contents


# ──────────────────────────────────────────────────────────────────────────────
# Data Model
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BrowserProfile:
    """One user profile inside a browser installation."""
    name:       str
    cache_dirs: List[str] = field(default_factory=list)
    # Future: cookies, history, downloads paths


@dataclass
class BrowserEntry:
    """Represents one supported browser on this machine."""
    name:     str
    icon:     str
    profiles: List[BrowserProfile] = field(default_factory=list)
    # Populated after scan
    cache_size:  int  = 0
    cache_count: int  = 0
    # Is the browser actually installed?
    installed:   bool = False


# ──────────────────────────────────────────────────────────────────────────────
# Engine
# ──────────────────────────────────────────────────────────────────────────────

class BrowserCleaner:
    """Detects installed browsers and provides cache scanning/cleaning."""

    _LOCAL_APP = os.environ.get("LOCALAPPDATA", "")
    _APP_DATA  = os.environ.get("APPDATA",      "")

    # Sub-folder names that Chromium-based browsers use for cache
    _CHROMIUM_CACHE_DIRS = [
        "Cache", "Cache2", "Code Cache",
        "GPUCache", "DawnCache", "ShaderCache",
        "Service Worker",
    ]

    def __init__(self):
        self.browsers: List[BrowserEntry] = self._detect_all()

    # ── Browser detection ─────────────────────────────────────────────────────

    def _detect_all(self) -> List[BrowserEntry]:
        return [
            self._detect_chromium("Google Chrome",   "\uE774",  # Globe
                os.path.join(self._LOCAL_APP, "Google", "Chrome", "User Data")),
            self._detect_chromium("Microsoft Edge",  "\uEB41",  # Edge logo
                os.path.join(self._LOCAL_APP, "Microsoft", "Edge", "User Data")),
            self._detect_chromium("Brave Browser",   "\uE83D",  # Shield (privacy)
                os.path.join(self._LOCAL_APP, "BraveSoftware", "Brave-Browser", "User Data")),
            self._detect_chromium("Opera",           "\uE774",  # Globe
                os.path.join(self._APP_DATA, "Opera Software", "Opera Stable")),
            self._detect_chromium("Opera GX",        "\uE774",  # Globe
                os.path.join(self._APP_DATA, "Opera Software", "Opera GX Stable")),
            self._detect_chromium("Vivaldi",         "\uE774",  # Globe
                os.path.join(self._LOCAL_APP, "Vivaldi", "User Data")),
            self._detect_firefox(),
        ]

    def _detect_chromium(self, name: str, icon: str, user_data: str) -> BrowserEntry:
        entry = BrowserEntry(name=name, icon=icon, installed=os.path.isdir(user_data))
        if not entry.installed:
            return entry

        # Collect all profile directories (Default + Profile 1, Profile 2 …)
        profile_dirs: List[str] = []
        default_dir = os.path.join(user_data, "Default")
        if os.path.isdir(default_dir):
            profile_dirs.append(default_dir)
        for p in glob.glob(os.path.join(user_data, "Profile *")):
            if os.path.isdir(p):
                profile_dirs.append(p)

        for pdir in profile_dirs:
            pname = os.path.basename(pdir)
            cache_dirs = []
            for cd in self._CHROMIUM_CACHE_DIRS:
                full = os.path.join(pdir, cd)
                if os.path.isdir(full):
                    cache_dirs.append(full)
            if cache_dirs:
                entry.profiles.append(BrowserProfile(name=pname, cache_dirs=cache_dirs))

        return entry

    def _detect_firefox(self) -> BrowserEntry:
        entry = BrowserEntry(name="Mozilla Firefox", icon="\uE774")  # Globe
        profiles_root = os.path.join(self._APP_DATA, "Mozilla", "Firefox", "Profiles")
        if not os.path.isdir(profiles_root):
            return entry

        entry.installed = True
        for profile_dir in glob.glob(os.path.join(profiles_root, "*")):
            if not os.path.isdir(profile_dir):
                continue
            cache_dirs = []
            for sub in ["cache2", "startupCache", "thumbnails", "safebrowsing"]:
                full = os.path.join(profile_dir, sub)
                if os.path.isdir(full):
                    cache_dirs.append(full)
            if cache_dirs:
                entry.profiles.append(
                    BrowserProfile(
                        name=os.path.basename(profile_dir),
                        cache_dirs=cache_dirs,
                    )
                )
        return entry

    # ── Scanning ──────────────────────────────────────────────────────────────

    def scan_browser(self, entry: BrowserEntry) -> int:
        """Scan one browser.  Populates entry.cache_size and returns it."""
        total_size  = 0
        total_count = 0
        for profile in entry.profiles:
            for d in profile.cache_dirs:
                s, c = get_folder_size(d)
                total_size  += s
                total_count += c
        entry.cache_size  = total_size
        entry.cache_count = total_count
        return total_size

    def scan_all(self) -> int:
        """Scan every installed browser.  Returns grand total bytes."""
        grand_total = 0
        for browser in self.browsers:
            if browser.installed:
                grand_total += self.scan_browser(browser)
        return grand_total

    # ── Cleaning ─────────────────────────────────────────────────────────────

    def clean_browser(self, entry: BrowserEntry) -> Tuple[int, List[str]]:
        """
        Delete all cache directories for *entry*.
        Returns (bytes_freed, errors).
        """
        freed  = 0
        errors: List[str] = []

        for profile in entry.profiles:
            for d in profile.cache_dirs:
                try:
                    freed += safe_remove_dir_contents(d)
                except Exception as e:
                    errors.append(f"{d}: {e}")

        entry.cache_size  = 0
        entry.cache_count = 0
        return freed, errors

    def clean_all(self) -> Tuple[int, List[str]]:
        """Clean every installed browser.  Returns (total_freed, all_errors)."""
        total_freed = 0
        all_errors: List[str] = []
        for browser in self.browsers:
            if browser.installed:
                freed, errs = self.clean_browser(browser)
                total_freed += freed
                all_errors.extend(errs)
        return total_freed, all_errors

    @property
    def installed_browsers(self) -> List[BrowserEntry]:
        return [b for b in self.browsers if b.installed]
