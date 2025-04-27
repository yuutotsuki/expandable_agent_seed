import os

def read_file_content(file_path: str) -> dict:
    """
    指定されたファイルの内容を読み込んで返します。
    """
    if not os.path.exists(file_path):
        return {
            "content": f"⚠️ ファイルが存在しません: {file_path}"
        }
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_text = f.read()
            return {
                "content": file_text
            }
    except Exception as e:
        return {
            "content": f"⚠️ ファイルを開けませんでした: {str(e)}"
        }

read_file_content_tool = {
    "type": "function",
    "function": {
        "name": "read_file_content",
        "description": "指定されたファイルの内容を読み込んで返します。",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "読み込むファイルのフルパス"
                }
            },
            "required": ["file_path"]
        }
    }
}
