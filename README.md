# LeerDisk

> **Professional Windows 11 disk cleaner with a native-feeling UI.**

LeerDisk scans and removes junk files across 17 system categories and 7 browsers, reclaiming disk space without touching anything important. It is built with Python and CustomTkinter, uses the official **Segoe UI Variable** typeface and **Segoe Fluent Icons** throughout, and requests administrator privileges automatically so every cleaning operation has the access it needs.

![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078D4?logo=windows)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

| | |
|---|---|
| **17 cleaning categories** | Temp files, update cache, prefetch, recycle bin, thumbnails, DNS cache, font & icon cache, and more |
| **7 browser engines** | Chrome, Edge, Brave, Opera, Opera GX, Vivaldi, Firefox — all profiles detected automatically |
| **Per-category scan** | See exactly how much each category holds before you delete anything |
| **Non-blocking UI** | All scanning and cleaning runs in background threads; the window stays responsive |
| **UAC elevation** | Requests admin rights on launch via `ShellExecuteW runas` — no manual "Run as administrator" needed |
| **Dark / Light mode** | Toggle in the sidebar; powered by CustomTkinter's appearance system |
| **Advanced Tools** | Quick-launch SFC, DISM, Disk Cleanup, Defrag, Resource Monitor, DNS flush, and more |
| **Windows 11 typography** | `Segoe UI Variable Display` for headings, `Segoe UI Variable Text` for body — exactly how Windows 11 itself uses the two optical-size variants |
| **Windows 11 icons** | Every icon is a `Segoe Fluent Icons` glyph — the same font used in Settings and File Explorer |

---

## Screenshots

> *Add your screenshots here.*

---

## Requirements

- **Windows 10 or 11** (64-bit recommended)
- **Python 3.10+** — [python.org](https://www.python.org/downloads/) (tick *Add Python to PATH* during install)
- The following pip packages (installed automatically by `install.bat`):

| Package | Version |
|---|---|
| `customtkinter` | ≥ 5.2.0 |
| `psutil` | ≥ 5.9.0 |
| `pillow` | ≥ 10.0.0 |

---

## Installation

```bat
git clone https://github.com/LeerBox/LeerDisk.git
cd LeerDisk
install.bat
```

`install.bat` upgrades pip and runs `pip install -r requirements.txt`. That is the only step.

---

## Running

```bat
LeerDisk.bat
```

Or directly:

```bat
python main.py
```

A UAC prompt will appear if the process is not already elevated. Accept it and the app opens.

---

## Cleaning Categories

| Category | What it removes |
|---|---|
| User Temp Files | `%TEMP%` — temporary files created by applications |
| Windows Temp Files | `C:\Windows\Temp` — system-level temp files |
| Prefetch Files | `C:\Windows\Prefetch` — launch-cache files (rebuilt automatically) |
| Windows Update Cache | `C:\Windows\SoftwareDistribution\Download` — downloaded update packages |
| Delivery Optimization Cache | Peer-to-peer update delivery files |
| Windows Error Reports | `%LOCALAPPDATA%\Microsoft\Windows\WER` — crash reports |
| Memory Dump Files | `MEMORY.DMP` and `Minidump\*.dmp` — BSOD crash dumps |
| Recycle Bin | All drives — permanently empties the bin |
| Thumbnail Cache | `%LOCALAPPDATA%\Microsoft\Windows\Explorer` — Explorer image database |
| System Log Files | CBS, DISM, MoSetup, and INF setup logs |
| Old Windows Installations | `Windows.old`, `$Windows.~BT`, `$Windows.~WS` |
| Recent Files History | Quick Access recent files and jump-list entries |
| DNS Cache | Runs `ipconfig /flushdns` |
| Clipboard Contents | Clears the Windows clipboard |
| Font Cache | `FNTCACHE.DAT` — rebuilt on next boot *(requires restart)* |
| Icon Cache | `IconCache.db` and related files *(requires restart)* |
| Windows Installer Logs | MSI log files left behind after software installs |

Categories marked **requires restart** are flagged in the UI before cleaning.

---

## Browser Support

| Browser | Engine | Profile detection |
|---|---|---|
| Google Chrome | Chromium | Default + all `Profile *` directories |
| Microsoft Edge | Chromium | Default + all `Profile *` directories |
| Brave Browser | Chromium | Default + all `Profile *` directories |
| Opera | Chromium | Single profile |
| Opera GX | Chromium | Single profile |
| Vivaldi | Chromium | Default + all `Profile *` directories |
| Mozilla Firefox | Gecko | All profiles under `Mozilla\Firefox\Profiles` |

**Cache paths cleaned per profile:** `Cache`, `Cache2`, `Code Cache`, `GPUCache`, `DawnCache`, `ShaderCache`, `Service Worker` (Chromium); `cache2`, `startupCache`, `thumbnails`, `safebrowsing` (Firefox).

> Close all browsers before cleaning. Cleaning while a browser is open may result in incomplete cleanup or file-lock errors.

---

## Advanced Tools

Quick-launch shortcuts to built-in Windows utilities, accessible from the *Advanced Tools* page:

- **Disk Cleanup** — `cleanmgr.exe`
- **System File Checker** — `sfc /scannow` in a new terminal
- **DISM Restore Health** — `DISM /Online /Cleanup-Image /RestoreHealth`
- **Defragment & Optimise Drives** — `dfrgui.exe`
- **Resource Monitor** — `resmon.exe`
- **Startup Manager** — Task Manager startup tab
- **Flush DNS Cache** — `ipconfig /flushdns` (runs silently, shows result)
- **Optimise RAM** — triggers .NET garbage collection
- **Windows Security** — `ms-settings:windowsdefender`
- **Storage Settings** — `ms-settings:storagepolicies`

---

## Project Structure

```
LeerDisk/
├── main.py              # Entry point — UAC elevation + dependency check
├── app.py               # Full UI: 5 pages, font system, icon system, IconButton
├── cleaner.py           # DiskCleaner engine — 17 cleaning categories
├── browser_cleaner.py   # BrowserCleaner engine — 7 browsers, multi-profile
├── utils.py             # format_bytes, get_disk_usage, safe_remove_* helpers
├── requirements.txt     # pip dependencies
├── install.bat          # One-click dependency installer
└── LeerDisk.bat         # Launcher
```

---

## How It Works

1. **`main.py`** checks for admin rights via `ctypes.windll.shell32.IsUserAnAdmin()`. If not elevated, it calls `ShellExecuteW` with verb `"runas"`, which triggers the UAC prompt and re-launches the process elevated.

2. **`app.py`** builds the UI using CustomTkinter. All scanning and cleaning operations are dispatched to daemon threads. Threads communicate back to the UI exclusively via `self.after(0, callback)`, and every callback guards against stale widget references using the `_exists(widget)` helper.

3. **`cleaner.py`** (`DiskCleaner`) and **`browser_cleaner.py`** (`BrowserCleaner`) contain only file-system logic — no UI imports. Each exposes a `scan_*` method that returns a byte count and a `clean_*` method that returns `(bytes_freed, errors)`.

4. **Typography:** `Segoe UI Variable Display` (bold titles) and `Segoe UI Variable Text` (body copy) — the two optical-size variants Windows 11 uses natively.

5. **Icons:** Every glyph is rendered via `Segoe Fluent Icons`, Windows 11's official icon font, using its Private Use Area codepoints (`U+E000–U+FFFF`). No image files are required.

---

## License

MIT — see [LICENSE](LICENSE) for details.
