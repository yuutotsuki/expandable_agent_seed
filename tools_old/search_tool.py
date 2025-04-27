from typing import List, Dict
import os

def search_files_by_keyword(search_term: str, directory: str) -> Dict:
    """
    指定ディレクトリ内のファイル名にキーワードが含まれるファイルのパスを返す。
    
    Args:
        search_term (str): 検索キーワード
        directory (str): 検索対象のディレクトリパス
        
    Returns:
        Dict: 検索結果とメッセージを含む辞書
        
    Raises:
        ValueError: 検索キーワードまたはディレクトリパスが無効な場合、または検索結果が多すぎる場合
        FileNotFoundError: 指定されたディレクトリが存在しない場合
        NotADirectoryError: 指定されたパスがディレクトリではない場合
        PermissionError: ディレクトリへのアクセス権限がない場合
    """
    if not search_term or not isinstance(search_term, str) or not search_term.strip():
        return {
            "files": [],
            "message": "検索キーワードが取得できませんでした。もう一度わかりやすく教えてください。"
        }

    if not directory or not isinstance(directory, str):
        raise ValueError("ディレクトリパスは空でない文字列である必要があります")
    
    if not os.path.exists(directory):
        raise FileNotFoundError(f"指定されたディレクトリが存在しません: {directory}")
    
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"指定されたパスはディレクトリではありません: {directory}")
    
    matching_files = []
    search_term_lower = search_term.lower()

    try:
        for root, _, files in os.walk(directory):
            matching_files.extend(
                os.path.join(root, file)
                for file in files
                if search_term_lower in file.lower()
            )
            if len(matching_files) > 1000:
                raise ValueError("検索結果が多すぎます。より具体的な検索キーワードを使用してください")
    except PermissionError as e:
        raise PermissionError(f"ディレクトリへのアクセス権限がありません: {directory}") from e

    # ✅ 結果が0件ならその旨を返す
    if not matching_files:
        return {
            "files": [],
            "message": "該当するファイルが見つかりませんでした。別のキーワードでお試しください。"
        }

    # ✅ 検索結果があれば「最初のファイルを開くよ」と伝える！
    return {
        "files": matching_files,
        "message": f"{len(matching_files)} 件ヒットしました。最初のファイルを開いて中身を表示しますね。"
    }

# OpenAIツールのスキーマ定義
search_tool = {
    "type": "function",
    "function": {
        "name": "search_files_by_keyword",
        "description": "指定ディレクトリ内のファイル名にキーワードが含まれるファイルを検索します",
        "parameters": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "ファイル名で検索するキーワード"
                },
                "directory": {
                    "type": "string",
                    "description": "検索対象のディレクトリパス"
                }
            },
            "required": ["search_term", "directory"]
        }
    }
}
