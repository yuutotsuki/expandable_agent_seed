import os
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 利用可能なモデル定数
AVAILABLE_MODELS = {
    'gpt4': 'gpt-4',
    'gpt35': 'gpt-3.5-turbo',
    'gpt4-turbo': 'gpt-4-turbo-preview',
    'gpt4-32k': 'gpt-4-32k',              # コンテキストウィンドウの大きいバージョン
    'gpt35-16k': 'gpt-3.5-turbo-16k',     # GPT-3.5の大容量バージョン
    # 将来的な追加例：
    # 'gpt5': 'gpt-5',                    # 将来リリースされた場合
    # 'gpt5-turbo': 'gpt-5-turbo',        # 将来のturboバージョン
}

# OpenAI API設定
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
model_key = os.getenv('OPENAI_MODEL', 'gpt4')
DEFAULT_MODEL = AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS['gpt4'])  # 存在しない場合はgpt-4を使用

# MCPサーバー設定
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://127.0.0.1:5001/')

# ドキュメントパス設定
DOCUMENTS_PATH = os.getenv('DOCUMENTS_PATH', os.path.expanduser('~/Documents'))

# アプリケーション設定
APP_NAME = "File Search Assistant"
VERSION = "1.0.0" 