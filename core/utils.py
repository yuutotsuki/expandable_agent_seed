import os
import re
from core.constants import DOCUMENTS_PATH, DATA_ROOT

def strip_prefix(path_line: str) -> str:
    """
    "  1: /data/foo.txt" や "1. /data/foo.txt"
    → "/data/foo.txt" に変換する関数
    """
    return re.sub(r"^\s*\d+\s*[.:]\s*", "", path_line).strip()

def resolve_real_path(file_path: str) -> str:
    """
    ファイルパス "/data/..." を実際のファイルパスに変換する関数
    """
    # "/data/" を消して実ファイルパスにする
    relative_path = file_path.replace(DATA_ROOT + "/", "")
    return os.path.join(DOCUMENTS_PATH, relative_path)