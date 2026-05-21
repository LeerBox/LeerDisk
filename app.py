"""
LeerDisk - Main Application UI
Professional Windows 11 disk cleaner built with CustomTkinter.
"""

import os
import string
import threading
import time
import subprocess
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from cleaner        import DiskCleaner
from browser_cleaner import BrowserCleaner
from utils          import format_bytes, get_disk_usage

# ──────────────────────────────────────────────────────────────────────────────
# Global theme defaults
# ──────────────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Palette (dark theme)
C = {
    "sidebar":       "#161616",
    "sidebar_hover": "#252525",
    "bg":            "#1F1F1F",
    "surface":       "#282828",
    "card":          "#313131",
    "border":        "#3A3A3A",
    "accent":        "#0078D4",
    "accent_dim":    "#005A9E",
    "success":       "#13A10E",
    "warning":       "#CA5010",
    "danger":        "#C42B1C",
    "text":          "#FFFFFF",
    "text_dim":      "#9D9D9D",
    "text_faint":    "#555555",
}

# ──────────────────────────────────────────────────────────────────────────────
# Font system  —  Segoe UI Variable (Windows 11 official typeface)
#   Display variant → bold headings / titles
#   Text variant    → normal body / descriptions
# ──────────────────────────────────────────────────────────────────────────────
_FONT_DISPLAY = "Segoe UI Variable Display"   # optical size for titles
_FONT_TEXT    = "Segoe UI Variable Text"       # optical size for body copy


def F(size: int, bold: bool = False) -> ctk.CTkFont:
    """
    Return a CTkFont using the correct Segoe UI Variable variant:
      • bold=True  → Display face, bold weight   (for titles / headings)
      • bold=False → Text face,    normal weight  (for descriptions / body)
    """
    return ctk.CTkFont(
        family=_FONT_DISPLAY if bold else _FONT_TEXT,
        size=size,
        weight="bold" if bold else "normal",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Icon system  —  Segoe Fluent Icons (Windows 11 official icon font)
# All codepoints from the E000–FFFF Private Use Area used by Microsoft.
# ──────────────────────────────────────────────────────────────────────────────
_ICON_FONT_FAMILY = "Segoe Fluent Icons"


def ICON(size: int) -> ctk.CTkFont:
    """Return a CTkFont using Segoe Fluent Icons (Windows 11 official icon font)."""
    return ctk.CTkFont(family=_ICON_FONT_FAMILY, size=size)


# Segoe Fluent Icons character constants
IC_HOME    = "\uE80F"   # Home
IC_BROOM   = "\uEF90"   # Broom (clean)
IC_GLOBE   = "\uE774"   # Globe (browser / network)
IC_GEAR    = "\uE713"   # Settings
IC_INFO    = "\uE946"   # Info
IC_SEARCH  = "\uE721"   # Search (scan)
IC_WARN    = "\uE7BA"   # Warning
IC_FOLDER  = "\uE8B7"   # Folder (temp files)
IC_WIN     = "\uE770"   # Windows logo
IC_SPEED   = "\uEC4A"   # Speed High (prefetch)
IC_SYNC    = "\uE895"   # Sync (windows update)
IC_DL      = "\uE896"   # Download (delivery optimisation)
IC_RECYCLE = "\uE948"   # Recycle Bin
IC_PHOTO   = "\uEB9F"   # Photo (thumbnails)
IC_PAGE    = "\uE8A5"   # Page (logs)
IC_ARCHIVE = "\uECAD"   # Archive (old windows)
IC_HIST    = "\uE823"   # History / Clock (recent files)
IC_CLIP    = "\uF0E3"   # Clipboard
IC_FONT    = "\uE8D2"   # Font
IC_COLOR   = "\uE790"   # Colors (icon cache)
IC_PKG     = "\uE8F4"   # Package (installer)
IC_CPU     = "\uE8F1"   # Processing (memory / CPU)
IC_DRIVE   = "\uEDA2"   # Hard Drive
IC_SHIELD  = "\uE83D"   # Shield (security)
IC_REPAIR  = "\uE90F"   # Repair / Wrench
IC_CHART   = "\uE9F9"   # Activity chart
IC_LAUNCH  = "\uE7FC"   # Launch (startup)
IC_BULB    = "\uE82F"   # Light Bulb
IC_EDGE    = "\uEB41"   # Microsoft Edge logo
IC_REFRESH = "\uE72C"   # Refresh


# ──────────────────────────────────────────────────────────────────────────────
# Reusable widget components
# ──────────────────────────────────────────────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """A small metric card with a colored top border, value, and subtitle."""

    def __init__(self, parent, title: str, value: str = "--",
                 subtitle: str = "", color: str = C["accent"], **kwargs):
        super().__init__(parent, fg_color=C["card"], corner_radius=10, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        # Colored top stripe
        ctk.CTkFrame(self, height=3, fg_color=color, corner_radius=0).grid(
            row=0, column=0, sticky="ew"
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=1, column=0, padx=16, pady=(10, 14), sticky="ew")
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inner, text=title,
            font=F(10),
            text_color=C["text_dim"],
        ).grid(row=0, column=0, sticky="w")

        self._val = ctk.CTkLabel(
            inner, text=value,
            font=F(21, True),
            text_color=C["text"],
        )
        self._val.grid(row=1, column=0, sticky="w")

        if subtitle:
            ctk.CTkLabel(
                inner, text=subtitle,
                font=F(9),
                text_color=C["text_faint"],
            ).grid(row=2, column=0, sticky="w")

    def set_value(self, value: str, color: str = C["text"]):
        try:
            if self._val.winfo_exists():
                self._val.configure(text=value, text_color=color)
        except Exception:
            pass


class IconButton(ctk.CTkFrame):
    """
    Compound button: Segoe Fluent Icons glyph + text label.
    Supports configure(state='normal'/'disabled', text='…').
    """

    def __init__(self, parent, icon: str, text: str,
                 command=None, state: str = "normal",
                 height: int = 36, width: int = 0,
                 fg_color=None, hover_color=None,
                 icon_size: int = 14, font=None,
                 corner_radius: int = 8, **kw):
        _fg    = fg_color    if fg_color    is not None else C["card"]
        _hover = hover_color if hover_color is not None else C["border"]
        super().__init__(
            parent,
            fg_color=_fg,
            corner_radius=corner_radius,
            height=height,
            **kw,
        )
        if width:
            super().configure(width=width)
        self._cmd   = command
        self._fg    = _fg
        self._hover = _hover
        self._state = state
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=0)
        self._ic = ctk.CTkLabel(inner, text=icon, font=ICON(icon_size), width=0)
        self._ic.pack(side="left", padx=(0, 5))
        self._tx = ctk.CTkLabel(inner, text=text, font=font or F(12, True), width=0)
        self._tx.pack(side="left")

        self._set_visuals(state)
        for w in (self, inner, self._ic, self._tx):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

    def _set_visuals(self, state: str):
        color = C["text"] if state == "normal" else C["text_faint"]
        try:
            self._ic.configure(text_color=color)
            self._tx.configure(text_color=color)
        except Exception:
            pass

    def _on_click(self, _=None):
        if self._state == "normal" and self._cmd:
            self._cmd()

    def _on_enter(self, _=None):
        if self._state == "normal":
            ctk.CTkFrame.configure(self, fg_color=self._hover)

    def _on_leave(self, _=None):
        ctk.CTkFrame.configure(self, fg_color=self._fg)

    def configure(self, **kw):  # noqa: A003
        if "state" in kw:
            self._state = kw.pop("state")
            self._set_visuals(self._state)
        if "text" in kw:
            try:
                self._tx.configure(text=kw.pop("text"))
            except Exception:
                kw.pop("text", None)
        if kw:
            super().configure(**kw)


class DriveBar(ctk.CTkFrame):
    """Horizontal disk-usage bar for one drive."""

    def __init__(self, parent, drive: str = "C:\\", **kwargs):
        super().__init__(parent, fg_color=C["card"], corner_radius=10, **kwargs)
        self._drive = drive
        self.grid_columnconfigure(0, weight=1)

        # Header row
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            hdr, text=f"Drive {drive[0]}:",
            font=F(12, True),
        ).grid(row=0, column=0, sticky="w")
        self._pct = ctk.CTkLabel(
            hdr, text="",
            font=F(10),
            text_color=C["text_dim"],
        )
        self._pct.grid(row=0, column=1, sticky="e")

        self._bar = ctk.CTkProgressBar(self, height=8, corner_radius=4)
        self._bar.grid(row=1, column=0, padx=16, pady=2, sticky="ew")
        self._bar.set(0)

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.grid(row=2, column=0, padx=16, pady=(2, 14), sticky="ew")
        foot.grid_columnconfigure((0, 1, 2), weight=1)

        self._lbl_used  = ctk.CTkLabel(foot, text="", font=F(9), text_color=C["text_dim"], anchor="w")
        self._lbl_free  = ctk.CTkLabel(foot, text="", font=F(9), text_color=C["success"])
        self._lbl_total = ctk.CTkLabel(foot, text="", font=F(9), text_color=C["text_dim"], anchor="e")
        self._lbl_used.grid(row=0, column=0, sticky="w")
        self._lbl_free.grid(row=0, column=1)
        self._lbl_total.grid(row=0, column=2, sticky="e")

        self.refresh()

    def refresh(self):
        total, used, free = get_disk_usage(self._drive)
        if total <= 0:
            self._pct.configure(text="N/A")
            return
        pct = used / total
        color = (
            C["danger"]  if pct > 0.90 else
            C["warning"] if pct > 0.70 else
            C["accent"]
        )
        self._bar.configure(progress_color=color)
        self._bar.set(pct)
        self._pct.configure(text=f"{pct * 100:.1f}% used")
        self._lbl_used.configure(text=f"Used: {format_bytes(used)}")
        self._lbl_free.configure(text=f"Free: {format_bytes(free)}")
        self._lbl_total.configure(text=f"Total: {format_bytes(total)}")


class SectionHeader(ctk.CTkLabel):
    def __init__(self, parent, text: str, **kwargs):
        super().__init__(
            parent, text=text,
            font=F(13, True),
            text_color=C["text"],
            **kwargs,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Main Application
# ──────────────────────────────────────────────────────────────────────────────

class LeerDiskApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("LeerDisk  —  Windows 11 Disk Cleaner")
        self.geometry("1160x740")
        self.minsize(960, 640)
        self.configure(fg_color=C["bg"])

        # Core engines
        self._cleaner = DiskCleaner()
        self._browser = BrowserCleaner()

        # UI state
        self._current_page = ""
        self._scanning     = False
        self._cleaning     = False
        self._cat_vars:    dict[str, tk.BooleanVar]  = {}
        self._cat_widgets: dict[str, dict]            = {}   # key → {frame, size_lbl}
        self._br_widgets:  dict[str, dict]            = {}   # browser name → {size_lbl, btn}
        self._dark_mode    = True

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._content_host = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content_host.grid(row=0, column=1, sticky="nsew")
        self._content_host.grid_columnconfigure(0, weight=1)
        self._content_host.grid_rowconfigure(0, weight=1)

        self._show_page("dashboard")

    # ──────────────────────────────────────────────────────────────────────────
    # Widget-safety helper
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _exists(widget) -> bool:
        """
        Return True only if *widget* still belongs to the live Tk hierarchy.
        Background threads must call this before scheduling any UI update on a
        page-specific widget, because _show_page() destroys widgets on
        navigation and old after() callbacks would otherwise raise TclError.
        """
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # SIDEBAR
    # ──────────────────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=220, fg_color=C["sidebar"], corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(8, weight=1)
        sb.grid_columnconfigure(0, weight=1)

        # Logo
        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, padx=20, pady=(26, 6), sticky="ew")
        ctk.CTkLabel(
            logo, text="LeerDisk",
            font=F(24, True),
            text_color=C["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo, text="Windows 11 Cleaner",
            font=F(10),
            text_color=C["text_faint"],
        ).pack(anchor="w")

        # Separator
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(8, 10)
        )

        # Nav items — Segoe Fluent Icons glyph + text, frame-based
        nav = [
            ("dashboard", "Dashboard",      IC_HOME),
            ("cleaner",   "System Cleaner", IC_BROOM),
            ("browser",   "Browser Cache",  IC_GLOBE),
            ("advanced",  "Advanced Tools", IC_GEAR),
            ("about",     "About",          IC_INFO),
        ]
        self._nav_items: dict[str, dict] = {}
        for i, (page, label, icon_char) in enumerate(nav):
            item_f = ctk.CTkFrame(sb, fg_color="transparent", corner_radius=8,
                                  cursor="hand2")
            item_f.grid(row=2 + i, column=0, padx=10, pady=2, sticky="ew")
            item_f.grid_columnconfigure(1, weight=1)

            ic_lbl = ctk.CTkLabel(item_f, text=icon_char, font=ICON(16),
                                  text_color=C["text_dim"], width=32)
            ic_lbl.grid(row=0, column=0, padx=(10, 2), pady=10)

            tx_lbl = ctk.CTkLabel(item_f, text=label, font=F(13),
                                  text_color=C["text_dim"], anchor="w")
            tx_lbl.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="w")

            for w in (item_f, ic_lbl, tx_lbl):
                w.bind("<Button-1>",
                       lambda e, p=page: self._show_page(p))
                w.bind("<Enter>",
                       lambda e, f=item_f, pg=page: f.configure(
                           fg_color=C["accent_dim"]
                           if pg == self._current_page
                           else C["sidebar_hover"]
                       ))
                w.bind("<Leave>",
                       lambda e, f=item_f, pg=page: f.configure(
                           fg_color=C["accent"]
                           if pg == self._current_page
                           else "transparent"
                       ))

            self._nav_items[page] = {"frame": item_f, "icon": ic_lbl, "text": tx_lbl}

        # Bottom separator
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).grid(
            row=8, column=0, sticky="ew", padx=16, pady=8
        )

        # Dark/Light toggle
        tog = ctk.CTkFrame(sb, fg_color="transparent")
        tog.grid(row=9, column=0, padx=18, pady=(0, 6), sticky="ew")
        tog.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            tog, text="Dark Mode",
            font=F(11),
            text_color=C["text_faint"],
        ).grid(row=0, column=0, sticky="w")
        self._theme_sw = ctk.CTkSwitch(
            tog, text="", width=46, height=22,
            onvalue="dark", offvalue="light",
            command=self._on_theme_toggle,
        )
        self._theme_sw.select()
        self._theme_sw.grid(row=0, column=1, sticky="e")

        # Version tag
        ctk.CTkLabel(
            sb, text="v1.0.0  ·  Win 11",
            font=F(9),
            text_color=C["text_faint"],
        ).grid(row=10, column=0, padx=18, pady=(0, 18))

    def _on_theme_toggle(self):
        mode = self._theme_sw.get()
        ctk.set_appearance_mode(mode)

    def _highlight_nav(self, page: str):
        for p, item in self._nav_items.items():
            if p == page:
                item["frame"].configure(fg_color=C["accent"])
                item["icon"].configure(text_color=C["text"])
                item["text"].configure(text_color=C["text"], font=F(13, True))
            else:
                item["frame"].configure(fg_color="transparent")
                item["icon"].configure(text_color=C["text_dim"])
                item["text"].configure(text_color=C["text_dim"], font=F(13))

    # ──────────────────────────────────────────────────────────────────────────
    # Page routing
    # ──────────────────────────────────────────────────────────────────────────

    def _show_page(self, page: str):
        if page == self._current_page:
            return
        for w in self._content_host.winfo_children():
            w.destroy()
        # Reset every row weight so leftover config from the previous page
        # (e.g. cleaner sets rows 0-3) doesn't corrupt the next page's layout.
        for r in range(8):
            self._content_host.grid_rowconfigure(r, weight=0, minsize=0, pad=0)
        self._content_host.grid_rowconfigure(0, weight=1)   # safe default
        self._current_page = page
        self._highlight_nav(page)
        dispatch = {
            "dashboard": self._page_dashboard,
            "cleaner":   self._page_cleaner,
            "browser":   self._page_browser,
            "advanced":  self._page_advanced,
            "about":     self._page_about,
        }
        dispatch.get(page, self._page_dashboard)()

    # ──────────────────────────────────────────────────────────────────────────
    # DASHBOARD PAGE
    # ──────────────────────────────────────────────────────────────────────────

    def _page_dashboard(self):
        host = self._content_host
        host.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(host, fg_color="transparent", corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Page header ──
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=30, pady=(30, 4), sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            hdr, text="Dashboard",
            font=F(26, True),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            hdr, text="Quick Scan & Clean",
            font=F(12, True),
            fg_color=C["accent"], hover_color=C["accent_dim"],
            height=38, corner_radius=8,
            command=self._quick_scan_clean,
        ).grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(
            scroll, text="System storage overview",
            font=F(11), text_color=C["text_dim"],
        ).grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        # ── Stat cards ──
        cards = ctk.CTkFrame(scroll, fg_color="transparent")
        cards.grid(row=2, column=0, padx=30, pady=(0, 18), sticky="ew")
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)

        total, used, free = get_disk_usage("C:\\")
        self._dash_stat_total = StatCard(cards, "Total (C:)", format_bytes(total), color=C["accent"])
        self._dash_stat_used  = StatCard(cards, "Used",       format_bytes(used),  color=C["warning"])
        self._dash_stat_free  = StatCard(cards, "Free",       format_bytes(free),  color=C["success"])
        self._dash_stat_junk  = StatCard(cards, "Est. Junk",  "Run a scan",        color=C["danger"])

        self._dash_stat_total.grid(row=0, column=0, padx=(0, 7), sticky="ew")
        self._dash_stat_used.grid( row=0, column=1, padx=7,      sticky="ew")
        self._dash_stat_free.grid( row=0, column=2, padx=7,      sticky="ew")
        self._dash_stat_junk.grid( row=0, column=3, padx=(7, 0), sticky="ew")

        # ── Drive bars ──
        SectionHeader(scroll, text="Storage").grid(
            row=3, column=0, padx=30, pady=(6, 8), sticky="w"
        )
        drive_row = ctk.CTkFrame(scroll, fg_color="transparent")
        drive_row.grid(row=4, column=0, padx=30, pady=(0, 18), sticky="ew")
        drive_row.grid_columnconfigure((0, 1), weight=1)

        drives = [f"{l}:\\" for l in string.ascii_uppercase if os.path.isdir(f"{l}:\\")]
        DriveBar(drive_row, drive=drives[0] if drives else "C:\\").grid(
            row=0, column=0, padx=(0, 8), sticky="ew"
        )
        if len(drives) > 1:
            DriveBar(drive_row, drive=drives[1]).grid(
                row=0, column=1, padx=(8, 0), sticky="ew"
            )

        # ── Feature tiles ──
        SectionHeader(scroll, text="Cleaning Categories").grid(
            row=5, column=0, padx=30, pady=(6, 8), sticky="w"
        )
        tiles = ctk.CTkFrame(scroll, fg_color="transparent")
        tiles.grid(row=6, column=0, padx=30, pady=(0, 18), sticky="ew")
        tiles.grid_columnconfigure((0, 1, 2), weight=1)

        tile_data = [
            (IC_FOLDER,  "Temp Files",     "User & system temp folders"),
            (IC_SYNC,    "Windows Update", "Update download cache"),
            (IC_GLOBE,   "Browser Cache",  "All installed browsers"),
            (IC_WARN,    "Error Reports",  "Crash dumps & WER files"),
            (IC_PHOTO,   "Thumbnails",     "Explorer thumb cache"),
            (IC_RECYCLE, "Recycle Bin",    "Files on all drives"),
        ]
        for i, (icon_char, name, desc) in enumerate(tile_data):
            r, c = divmod(i, 3)
            tile = ctk.CTkFrame(tiles, fg_color=C["card"], corner_radius=10)
            tile.grid(row=r, column=c, padx=5, pady=5, sticky="ew")
            tile.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(tile, text=icon_char, font=ICON(22)).grid(
                row=0, column=0, rowspan=2, padx=(14, 8), pady=12
            )
            ctk.CTkLabel(tile, text=name,
                         font=F(12, True)).grid(
                row=0, column=1, sticky="sw", pady=(12, 0)
            )
            ctk.CTkLabel(tile, text=desc,
                         font=F(10), text_color=C["text_dim"]).grid(
                row=1, column=1, sticky="nw", pady=(0, 12)
            )

        # ── Tip banner ──
        banner = ctk.CTkFrame(scroll, fg_color="#0D2137", corner_radius=10)
        banner.grid(row=7, column=0, padx=30, pady=(0, 30), sticky="ew")
        banner.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(banner, text=IC_BULB, font=ICON(22)).grid(
            row=0, column=0, padx=16, pady=14
        )
        tip = ctk.CTkFrame(banner, fg_color="transparent")
        tip.grid(row=0, column=1, pady=14, sticky="w")
        ctk.CTkLabel(tip, text="Keep Windows running at peak performance",
                     font=F(12, True)).pack(anchor="w")
        ctk.CTkLabel(tip, text="Run a full scan weekly to reclaim disk space and keep your PC responsive.",
                     font=F(10), text_color=C["text_dim"]).pack(anchor="w")
        ctk.CTkButton(
            banner, text="Full Scan →",
            font=F(11), fg_color=C["accent"],
            hover_color=C["accent_dim"], height=30, corner_radius=6, width=120,
            command=lambda: self._show_page("cleaner"),
        ).grid(row=0, column=2, padx=16, pady=14)

    def _quick_scan_clean(self):
        self._show_page("cleaner")
        self.after(200, self._start_scan)

    # ──────────────────────────────────────────────────────────────────────────
    # SYSTEM CLEANER PAGE
    # ──────────────────────────────────────────────────────────────────────────

    def _page_cleaner(self):
        host = self._content_host
        host.grid_rowconfigure(0, weight=0)
        host.grid_rowconfigure(1, weight=0)
        host.grid_rowconfigure(2, weight=0)
        host.grid_rowconfigure(3, weight=1)

        # ── Top action bar ──
        topbar = ctk.CTkFrame(host, fg_color=C["surface"], corner_radius=0, height=64)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.grid(row=0, column=0, padx=24, pady=12, sticky="w")
        ctk.CTkLabel(
            left, text="System Cleaner",
            font=F(19, True),
        ).pack(side="left", padx=(0, 14))
        self._cl_status = ctk.CTkLabel(
            left, text="Select categories and click Scan",
            font=F(11), text_color=C["text_dim"],
        )
        self._cl_status.pack(side="left")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.grid(row=0, column=1, padx=24, pady=12, sticky="e")

        for txt, cmd, w in [
            ("Select All", self._sel_all,   80),
            ("Clear All",  self._sel_none,  80),
        ]:
            ctk.CTkButton(
                right, text=txt, font=F(11),
                fg_color=C["card"], hover_color=C["border"],
                height=32, corner_radius=6, width=w, command=cmd,
            ).pack(side="left", padx=(0, 6))

        self._scan_btn = IconButton(
            right, icon=IC_SEARCH, text="Scan",
            fg_color=C["card"], hover_color=C["border"],
            height=36, corner_radius=8, width=108,
            command=self._start_scan,
        )
        self._scan_btn.pack(side="left", padx=(0, 8))

        self._clean_btn = IconButton(
            right, icon=IC_BROOM, text="Clean",
            fg_color=C["accent"], hover_color=C["accent_dim"],
            height=36, corner_radius=8, width=108,
            state="disabled",
            command=self._start_clean,
        )
        self._clean_btn.pack(side="left")

        # ── Progress bar (hidden initially) ──
        self._cl_progress = ctk.CTkProgressBar(host, height=3, corner_radius=0,
                                                progress_color=C["accent"])
        self._cl_progress.grid(row=1, column=0, sticky="ew")
        self._cl_progress.set(0)
        self._cl_progress.grid_remove()

        # ── Summary strip ──
        self._cl_summary_bar = ctk.CTkFrame(
            host, fg_color="#1A1A1A", corner_radius=0, height=36
        )
        self._cl_summary_bar.grid(row=2, column=0, sticky="ew")
        self._cl_summary_bar.grid_propagate(False)
        self._cl_summary_lbl = ctk.CTkLabel(
            self._cl_summary_bar, text="No scan performed yet.",
            font=F(11), text_color=C["text_faint"],
        )
        self._cl_summary_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # ── Category list ──
        self._cat_vars    = {}
        self._cat_widgets = {}

        scroll = ctk.CTkScrollableFrame(host, fg_color="transparent", corner_radius=0)
        scroll.grid(row=3, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        for cat in self._cleaner.categories:
            self._add_cat_row(scroll, cat)

    def _add_cat_row(self, parent, cat):
        var = tk.BooleanVar(value=cat.enabled)
        self._cat_vars[cat.key] = var

        row = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=9)
        row.grid(padx=20, pady=4, sticky="ew")
        row.grid_columnconfigure(2, weight=1)

        # Checkbox
        ctk.CTkCheckBox(
            row, text="", variable=var,
            width=20, checkbox_width=18, checkbox_height=18,
            corner_radius=4, fg_color=C["accent"], hover_color=C["accent_dim"],
        ).grid(row=0, column=0, rowspan=2, padx=(14, 2), pady=16)

        # Category icon (Segoe Fluent Icons)
        ctk.CTkLabel(
            row, text=cat.icon, font=ICON(18),
            text_color=C["text_dim"], width=28,
        ).grid(row=0, column=1, rowspan=2, padx=(4, 4), pady=16)

        # Labels
        name_row = ctk.CTkFrame(row, fg_color="transparent")
        name_row.grid(row=0, column=2, padx=8, pady=(12, 1), sticky="w")
        ctk.CTkLabel(
            name_row, text=cat.name,
            font=F(12, True),
        ).pack(side="left", padx=(0, 8))
        if cat.requires_restart:
            ctk.CTkLabel(
                name_row, text=" Needs Restart ",
                font=F(9), text_color="white",
                fg_color=C["warning"], corner_radius=4,
            ).pack(side="left")

        ctk.CTkLabel(
            row, text=cat.description,
            font=F(10), text_color=C["text_dim"],
        ).grid(row=1, column=2, padx=8, pady=(1, 12), sticky="w")

        # Size indicator (right side)
        # Pre-populate if we already have scan data
        if cat.scan_size > 0:
            size_text  = format_bytes(cat.scan_size)
            size_color = C["warning"] if cat.scan_size < 10 * 1024 * 1024 else C["danger"]
        elif cat.cleaned_size > 0:
            size_text  = f"Cleaned ✓\n{format_bytes(cat.cleaned_size)}"
            size_color = C["success"]
        else:
            size_text  = "—"
            size_color = C["text_faint"]

        size_lbl = ctk.CTkLabel(
            row, text=size_text,
            font=F(11),
            text_color=size_color,
            width=130, anchor="e", justify="right",
        )
        size_lbl.grid(row=0, column=3, rowspan=2, padx=(8, 16), pady=16)

        self._cat_widgets[cat.key] = {"row": row, "size_lbl": size_lbl}

    def _sel_all(self):
        for v in self._cat_vars.values():
            v.set(True)

    def _sel_none(self):
        for v in self._cat_vars.values():
            v.set(False)

    def _start_scan(self):
        if self._scanning or self._cleaning:
            return
        selected = [k for k, v in self._cat_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("LeerDisk", "Select at least one category to scan.")
            return

        self._scanning = True
        self._scan_btn.configure(state="disabled", text="Scanning…")
        self._clean_btn.configure(state="disabled")
        self._cl_progress.grid()
        self._cl_progress.set(0)

        def worker():
            grand_total = 0
            n = len(selected)
            for i, key in enumerate(selected):
                cat = self._cleaner.get_category(key)
                def _set_status(c=cat):
                    if self._exists(self._cl_status):
                        self._cl_status.configure(text=f"Scanning: {c.name}…")
                self.after(0, _set_status)
                size, count = self._cleaner.scan_single(key)
                grand_total += size

                wgt = self._cat_widgets.get(key)
                def _upd(w=wgt, s=size):
                    if not w:
                        return
                    lbl = w["size_lbl"]
                    if not self._exists(lbl):
                        return
                    if s == 0:
                        lbl.configure(text="Clean ✓", text_color=C["success"])
                    elif s < 10 * 1024 * 1024:
                        lbl.configure(text=format_bytes(s), text_color=C["warning"])
                    else:
                        lbl.configure(text=format_bytes(s), text_color=C["danger"])
                self.after(0, _upd)

                def _set_prog(p=(i + 1) / n):
                    if self._exists(self._cl_progress):
                        self._cl_progress.set(p)
                self.after(0, _set_prog)
                time.sleep(0.04)

            def done(total=grand_total, cnt=len(selected)):
                self._scanning = False
                try:
                    if self._exists(self._scan_btn):
                        self._scan_btn.configure(state="normal", text="Scan")
                    if self._exists(self._clean_btn):
                        self._clean_btn.configure(state="normal")
                    if self._exists(self._cl_progress):
                        self._cl_progress.grid_remove()
                    if self._exists(self._cl_status):
                        self._cl_status.configure(
                            text=f"Scan complete — {cnt} categories analysed")
                    if self._exists(self._cl_summary_lbl):
                        self._cl_summary_lbl.configure(
                            text=f"Found  {format_bytes(total)}  of junk across {cnt} categories",
                            text_color=C["warning"] if total > 0 else C["success"],
                        )
                except Exception:
                    pass
                # Update dashboard card only if it's still alive
                if hasattr(self, "_dash_stat_junk") and self._exists(self._dash_stat_junk):
                    self._dash_stat_junk.set_value(format_bytes(total), color=C["danger"])

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _start_clean(self):
        if self._scanning or self._cleaning:
            return
        selected = [k for k, v in self._cat_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("LeerDisk", "Select at least one category to clean.")
            return

        needs_restart = any(
            self._cleaner.get_category(k).requires_restart
            for k in selected
            if self._cleaner.get_category(k)
        )
        restart_note = "\n\nSome selected items require a restart to take full effect." if needs_restart else ""

        if not messagebox.askyesno(
            "LeerDisk — Confirm Clean",
            f"Permanently delete files from {len(selected)} categories?\n"
            f"This action cannot be undone.{restart_note}\n\nContinue?",
            icon="warning",
        ):
            return

        self._cleaning = True
        self._scan_btn.configure(state="disabled")
        self._clean_btn.configure(state="disabled", text="Cleaning…")
        self._cl_progress.grid()
        self._cl_progress.set(0)

        def worker():
            total_freed = 0
            n = len(selected)
            for i, key in enumerate(selected):
                cat = self._cleaner.get_category(key)
                def _set_status(c=cat):
                    if self._exists(self._cl_status):
                        self._cl_status.configure(text=f"Cleaning: {c.name}…")
                self.after(0, _set_status)
                freed, _errs = self._cleaner.clean_category(key)
                total_freed += freed

                wgt = self._cat_widgets.get(key)
                def _upd(w=wgt, f=freed):
                    if w and self._exists(w["size_lbl"]):
                        w["size_lbl"].configure(
                            text=f"Cleaned ✓\n{format_bytes(f)}",
                            text_color=C["success"],
                        )
                self.after(0, _upd)

                def _set_prog(p=(i + 1) / n):
                    if self._exists(self._cl_progress):
                        self._cl_progress.set(p)
                self.after(0, _set_prog)
                time.sleep(0.08)

            def done(total=total_freed, cnt=len(selected)):
                self._cleaning = False
                try:
                    if self._exists(self._scan_btn):
                        self._scan_btn.configure(state="normal", text="Scan")
                    if self._exists(self._clean_btn):
                        self._clean_btn.configure(state="disabled", text="Clean")
                    if self._exists(self._cl_progress):
                        self._cl_progress.grid_remove()
                    if self._exists(self._cl_status):
                        self._cl_status.configure(text="Clean complete!")
                    if self._exists(self._cl_summary_lbl):
                        self._cl_summary_lbl.configure(
                            text=f"✓  Freed  {format_bytes(total)}  of disk space across {cnt} categories",
                            text_color=C["success"],
                        )
                except Exception:
                    pass
                messagebox.showinfo(
                    "LeerDisk — Done",
                    f"Successfully freed  {format_bytes(total)}\n"
                    f"across {cnt} categories.",
                )

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # BROWSER CACHE PAGE
    # ──────────────────────────────────────────────────────────────────────────

    def _page_browser(self):
        host = self._content_host
        host.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(host, fg_color="transparent", corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=30, pady=(30, 4), sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            hdr, text="Browser Cache Cleaner",
            font=F(22, True),
        ).grid(row=0, column=0, sticky="w")

        btns = ctk.CTkFrame(hdr, fg_color="transparent")
        btns.grid(row=0, column=1, sticky="e")
        IconButton(
            btns, icon=IC_SEARCH, text="Scan All",
            fg_color=C["card"], hover_color=C["border"],
            height=36, corner_radius=8, width=120,
            command=self._br_scan_all,
        ).pack(side="left", padx=(0, 8))
        IconButton(
            btns, icon=IC_BROOM, text="Clean All",
            fg_color=C["accent"], hover_color=C["accent_dim"],
            height=36, corner_radius=8, width=120,
            command=self._br_clean_all,
        ).pack(side="left")

        ctk.CTkLabel(
            scroll, text="Detect and remove cached data from all installed browsers",
            font=F(11), text_color=C["text_dim"],
        ).grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        self._br_widgets = {}
        for i, browser in enumerate(self._browser.browsers):
            dot_color = C["success"] if browser.installed else C["border"]

            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=10)
            card.grid(row=2 + i, column=0, padx=30, pady=5, sticky="ew")
            card.grid_columnconfigure(2, weight=1)

            ctk.CTkFrame(card, width=8, height=8, corner_radius=4,
                         fg_color=dot_color).grid(
                row=0, column=0, rowspan=2, padx=(16, 8), pady=16
            )

            name_row = ctk.CTkFrame(card, fg_color="transparent")
            name_row.grid(row=0, column=1, padx=4, pady=(12, 1), sticky="w")
            ctk.CTkLabel(
                name_row,
                text=browser.icon, font=ICON(16),
                text_color=C["accent"] if browser.installed else C["text_dim"],
            ).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                name_row,
                text=browser.name,
                font=F(13, True),
            ).pack(side="left")
            if not browser.installed:
                ctk.CTkLabel(
                    name_row, text="  Not installed",
                    font=F(10), text_color=C["text_faint"],
                ).pack(side="left")

            prof_count = len(browser.profiles)
            prof_text  = f"{prof_count} profile{'s' if prof_count != 1 else ''} detected" if browser.installed else "Cache, cookies, and session data"
            ctk.CTkLabel(
                card, text=prof_text,
                font=F(10), text_color=C["text_dim"],
            ).grid(row=1, column=1, padx=4, pady=(1, 12), sticky="w")

            size_lbl = ctk.CTkLabel(
                card, text="—",
                font=F(12), text_color=C["text_dim"],
                width=110, anchor="e",
            )
            size_lbl.grid(row=0, column=2, rowspan=2, padx=12)

            btn = ctk.CTkButton(
                card, text="Clean Cache",
                font=F(11),
                fg_color=C["card"] if browser.installed else C["surface"],
                hover_color=C["border"],
                height=32, corner_radius=6, width=110,
                state="normal" if browser.installed else "disabled",
                command=lambda b=browser, sl=size_lbl: self._br_clean_single(b, sl),
            )
            btn.grid(row=0, column=3, rowspan=2, padx=(8, 16), pady=16)

            self._br_widgets[browser.name] = {
                "size_lbl": size_lbl, "btn": btn, "browser": browser,
            }

        # Warning note
        note = ctk.CTkFrame(scroll, fg_color="#201400", corner_radius=10)
        note.grid(row=2 + len(self._browser.browsers), column=0,
                  padx=30, pady=(14, 30), sticky="ew")
        note.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(note, text=IC_WARN, font=ICON(20)).grid(
            row=0, column=0, padx=14, pady=12
        )
        msg = ctk.CTkFrame(note, fg_color="transparent")
        msg.grid(row=0, column=1, pady=12, sticky="w")
        ctk.CTkLabel(
            msg, text="Close all browsers before cleaning",
            font=F(12, True), text_color=C["warning"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            msg, text="Cleaning while a browser is open may cause data corruption or incomplete cleanup.",
            font=F(10), text_color=C["text_dim"],
        ).pack(anchor="w")

    def _br_scan_all(self):
        def worker():
            for entry in self._browser.browsers:
                if entry.installed:
                    size = self._browser.scan_browser(entry)
                    wgt  = self._br_widgets.get(entry.name)
                    def _upd(w=wgt, s=size):
                        if w and self._exists(w["size_lbl"]):
                            color = C["warning"] if s > 0 else C["success"]
                            w["size_lbl"].configure(
                                text=format_bytes(s) if s > 0 else "Clean ✓",
                                text_color=color,
                            )
                    self.after(0, _upd)
        threading.Thread(target=worker, daemon=True).start()

    def _br_clean_single(self, browser, size_lbl):
        if not messagebox.askyesno(
            "LeerDisk",
            f"Clean cache for {browser.name}?\n\nEnsure {browser.name} is closed.",
        ):
            return

        def worker():
            freed, _errs = self._browser.clean_browser(browser)
            def done(f=freed):
                if self._exists(size_lbl):
                    size_lbl.configure(text="Cleaned ✓", text_color=C["success"])
                messagebox.showinfo(
                    "LeerDisk",
                    f"Cleaned  {format_bytes(f)}  from {browser.name}.",
                )
            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _br_clean_all(self):
        installed = self._browser.installed_browsers
        if not installed:
            messagebox.showinfo("LeerDisk", "No supported browsers were detected.")
            return
        names = "\n".join(f"  •  {b.name}" for b in installed)
        if not messagebox.askyesno(
            "LeerDisk — Clean All Browsers",
            f"Clean cache for:\n{names}\n\nMake sure all browsers are closed.\n\nContinue?",
            icon="warning",
        ):
            return

        def worker():
            total = 0
            for browser in installed:
                freed, _ = self._browser.clean_browser(browser)
                total += freed
                wgt = self._br_widgets.get(browser.name)
                def _upd(w=wgt, f=freed):
                    if w and self._exists(w["size_lbl"]):
                        w["size_lbl"].configure(text="Cleaned ✓", text_color=C["success"])
                self.after(0, _upd)
            self.after(0, lambda t=total: messagebox.showinfo(
                "LeerDisk", f"Cleaned  {format_bytes(t)}  from all browsers."
            ))

        threading.Thread(target=worker, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # ADVANCED TOOLS PAGE
    # ──────────────────────────────────────────────────────────────────────────

    def _page_advanced(self):
        host = self._content_host
        host.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(host, fg_color="transparent", corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            scroll, text="Advanced Tools",
            font=F(22, True),
        ).grid(row=0, column=0, padx=30, pady=(30, 4), sticky="w")
        ctk.CTkLabel(
            scroll, text="System maintenance, optimisation, and diagnostic utilities",
            font=F(11), text_color=C["text_dim"],
        ).grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        tools = [
            {
                "icon":  IC_DRIVE,
                "name":  "Disk Cleanup (Windows Built-in)",
                "desc":  "Open the built-in Disk Cleanup wizard",
                "btn":   "Open",
                "action": lambda: self._run("cleanmgr.exe"),
            },
            {
                "icon":  IC_REPAIR,
                "name":  "System File Checker  (sfc /scannow)",
                "desc":  "Scan and repair corrupted Windows system files",
                "btn":   "Run SFC",
                "action": lambda: self._run_in_cmd("sfc /scannow"),
            },
            {
                "icon":  IC_PKG,
                "name":  "DISM — Restore Health",
                "desc":  "Repair the Windows component store using DISM",
                "btn":   "Run DISM",
                "action": lambda: self._run_in_cmd(
                    "DISM /Online /Cleanup-Image /RestoreHealth"
                ),
            },
            {
                "icon":  IC_DRIVE,
                "name":  "Defragment & Optimise Drives",
                "desc":  "Open the Defragment and Optimise Drives tool",
                "btn":   "Open",
                "action": lambda: self._run("dfrgui.exe"),
            },
            {
                "icon":  IC_CHART,
                "name":  "Resource Monitor",
                "desc":  "View live CPU, memory, disk, and network usage",
                "btn":   "Open",
                "action": lambda: self._run("resmon.exe"),
            },
            {
                "icon":  IC_SPEED,
                "name":  "Startup Manager",
                "desc":  "Manage startup applications via Task Manager",
                "btn":   "Open",
                "action": lambda: self._run("taskmgr.exe"),
            },
            {
                "icon":  IC_GLOBE,
                "name":  "Flush DNS Cache",
                "desc":  "Run  ipconfig /flushdns  to clear the DNS resolver cache",
                "btn":   "Flush",
                "action": self._flush_dns,
            },
            {
                "icon":  IC_CPU,
                "name":  "Optimise RAM",
                "desc":  "Trigger .NET garbage collection to free idle memory",
                "btn":   "Optimise",
                "action": self._optimise_ram,
            },
            {
                "icon":  IC_SHIELD,
                "name":  "Windows Security",
                "desc":  "Open the Windows Security Center",
                "btn":   "Open",
                "action": lambda: self._run(
                    "start ms-settings:windowsdefender"
                ),
            },
            {
                "icon":  IC_GEAR,
                "name":  "Storage Settings",
                "desc":  "Open Windows Storage Sense and disk settings",
                "btn":   "Open",
                "action": lambda: self._run("start ms-settings:storagepolicies"),
            },
        ]

        for i, tool in enumerate(tools):
            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=10)
            card.grid(row=2 + i, column=0, padx=30, pady=5, sticky="ew")
            card.grid_columnconfigure(2, weight=1)

            ctk.CTkLabel(card, text=tool["icon"],
                         font=ICON(22)).grid(
                row=0, column=0, rowspan=2, padx=(16, 10), pady=14
            )
            ctk.CTkLabel(card, text=tool["name"],
                         font=F(12, True)).grid(
                row=0, column=1, padx=4, pady=(12, 1), sticky="w"
            )
            ctk.CTkLabel(card, text=tool["desc"],
                         font=F(10),
                         text_color=C["text_dim"]).grid(
                row=1, column=1, padx=4, pady=(1, 12), sticky="w"
            )
            ctk.CTkButton(
                card, text=tool["btn"],
                font=F(11),
                fg_color=C["surface"], hover_color=C["accent"],
                height=30, corner_radius=6, width=88,
                command=tool["action"],
            ).grid(row=0, column=3, rowspan=2, padx=(8, 16), pady=14)

        # Spacer at the bottom
        ctk.CTkFrame(scroll, height=30, fg_color="transparent").grid(
            row=2 + len(tools), column=0
        )

    def _run(self, cmd: str):
        try:
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            messagebox.showerror("LeerDisk", f"Failed to launch:\n{cmd}\n\n{e}")

    def _run_in_cmd(self, cmd: str):
        try:
            subprocess.Popen(f'start cmd /k "{cmd}"', shell=True)
        except Exception as e:
            messagebox.showerror("LeerDisk", f"Failed to run:\n{cmd}\n\n{e}")

    def _flush_dns(self):
        def worker():
            try:
                subprocess.run(["ipconfig", "/flushdns"],
                               capture_output=True, timeout=15)
                self.after(0, lambda: messagebox.showinfo(
                    "LeerDisk", "DNS cache flushed successfully!"))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror(
                    "LeerDisk", f"DNS flush failed:\n{err}"))
        threading.Thread(target=worker, daemon=True).start()

    def _optimise_ram(self):
        def worker():
            try:
                subprocess.run(
                    ["PowerShell", "-NoProfile", "-Command",
                     "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()"],
                    capture_output=True, timeout=15,
                )
                self.after(0, lambda: messagebox.showinfo(
                    "LeerDisk", "RAM optimisation complete.\n.NET garbage collection triggered."))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror(
                    "LeerDisk", f"Optimisation failed:\n{err}"))
        threading.Thread(target=worker, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # ABOUT PAGE
    # ──────────────────────────────────────────────────────────────────────────

    def _page_about(self):
        host = self._content_host
        host.grid_rowconfigure(0, weight=1)

        outer = ctk.CTkFrame(host, fg_color="transparent")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(outer, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center, text="LeerDisk",
            font=F(52, True),
            text_color=C["accent"],
        ).pack()
        ctk.CTkLabel(
            center, text="Professional Windows 11 Disk Cleaner",
            font=F(15), text_color=C["text_dim"],
        ).pack(pady=(4, 28))

        info_card = ctk.CTkFrame(center, fg_color=C["card"], corner_radius=12)
        info_card.pack(fill="x", padx=20, pady=(0, 20))

        rows = [
            ("Version",          "1.0.0"),
            ("Platform",         "Windows 10 / 11"),
            ("UI Framework",     "CustomTkinter"),
            ("Clean Categories", str(len(self._cleaner.categories))),
            ("Browsers Detected",
             str(len(self._browser.installed_browsers)) + " installed"),
        ]
        for lbl, val in rows:
            r = ctk.CTkFrame(info_card, fg_color="transparent")
            r.pack(fill="x", padx=20, pady=7)
            ctk.CTkLabel(
                r, text=lbl, width=160, anchor="w",
                font=F(12), text_color=C["text_dim"],
            ).pack(side="left")
            ctk.CTkLabel(
                r, text=val,
                font=F(12, True),
            ).pack(side="left")

        ctk.CTkLabel(
            center, text="Built for speed. Designed for Windows 11.",
            font=F(10), text_color=C["text_faint"],
        ).pack(pady=(8, 0))
