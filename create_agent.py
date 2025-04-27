# create_agent.py

import json
from openai import OpenAI
from tools.search_tool import search_tool
from tools.read_file_content_tool import read_file_content_tool  # ← 追加

client = OpenAI()

# 🔧 search_config.json を読み込み
with open("search_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

instructions_template = config["instructions"]
default_directory = config["default_directory"]

# 🔄 プレースホルダーを置換して最終 instructions を作成
instructions = instructions_template.replace("{default_directory}", default_directory)

# ✅ Assistant 作成
assistant = client.beta.assistants.create(
    name="ファイル検索アシスタント",
    instructions=instructions,
    tools=[search_tool, read_file_content_tool],  # ← ここに追加！
    model="gpt-4-1106-preview"
)

print("✅ エージェント作成成功！Assistant ID:", assistant.id)
