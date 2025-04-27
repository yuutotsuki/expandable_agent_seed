# core/utils.py

import re

def strip_prefix(path_line: str) -> str:
    """
    "  1: /data/foo.txt" や "1. /data/foo.txt"
    → "/data/foo.txt" に変換する関数
    """
    return re.sub(r"^\s*\d+\s*[.:]\s*", "", path_line).strip()
