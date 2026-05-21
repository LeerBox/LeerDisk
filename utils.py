"""
LeerDisk - Utility Functions
Helper functions for file size formatting, disk queries, and safe file operations.
"""

import os
import shutil
from typing import Tuple


def format_bytes(size: int) -> str:
    """Convert byte count to a human-readable string (e.g. 1.23 GB)."""
    if size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    i = 0
    while value >= 1024.0 and i < len(units) - 1:
        value /= 1024.0
        i += 1
    return f"{int(value)} {units[i]}" if i == 0 else f"{value:.2f} {units[i]}"


def get_disk_usage(drive: str = "C:\\") -> Tuple[int, int, int]:
    """Return (total, used, free) bytes for the given drive letter path."""
    try:
        total, used, free = shutil.disk_usage(drive)
        return total, used, free
    except Exception:
        return 0, 0, 0


def get_folder_size(path: str) -> Tuple[int, int]:
    """
    Walk a directory tree and return (total_bytes, file_count).
    Silently skips files that cannot be accessed.
    """
    total = 0
    count = 0
    if not os.path.exists(path):
        return 0, 0
    try:
        for dirpath, _dirs, filenames in os.walk(path):
            for fname in filenames:
                try:
                    fp = os.path.join(dirpath, fname)
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
                        count += 1
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total, count


def get_file_size(path: str) -> int:
    """Return the size of a single file in bytes, or 0 on error."""
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
    except (OSError, PermissionError):
        pass
    return 0


def safe_remove_file(path: str) -> Tuple[bool, int]:
    """
    Delete a single file.
    Returns (success, bytes_freed).
    """
    try:
        size = os.path.getsize(path)
        os.remove(path)
        return True, size
    except Exception:
        return False, 0


def safe_remove_dir_contents(path: str) -> int:
    """
    Delete all files (and empty sub-directories) inside *path*.
    The directory itself is kept.  Returns total bytes freed.
    """
    freed = 0
    if not os.path.isdir(path):
        return 0
    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        for fname in filenames:
            fp = os.path.join(dirpath, fname)
            try:
                freed += os.path.getsize(fp)
                os.remove(fp)
            except Exception:
                pass
        for dname in dirnames:
            dp = os.path.join(dirpath, dname)
            try:
                os.rmdir(dp)
            except Exception:
                pass
    return freed


def safe_remove_tree(path: str) -> int:
    """
    Delete an entire directory tree.
    Returns total bytes freed.
    """
    if not os.path.exists(path):
        return 0
    freed, _ = get_folder_size(path)
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass
    return freed
