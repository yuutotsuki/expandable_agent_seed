import asyncio
import json
import os
import requests
import time
import re
from agents import Agent, Runner, trace, gen_trace_id, function_tool
from typing import Optional, List
from config import *
from pathlib import Path
from tools.search_files import search_files
from tools.list_recent_files import list_recent_files
from clients.mcp_client import CustomMCPClient
from core.messages import get_message
from core.utils import strip_prefix, resolve_real_path
from core.instructions import BASE_INSTRUCTIONS, ORCHESTRATOR_INSTRUCTIONS
from core.constants import DATA_ROOT, APP_NAME, APP_VERSION, DEFAULT_RECENT_FILES_COUNT


# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------
# 0. Restore base agent from JSON
# -----------------------------
with open(os.path.join(SCRIPT_DIR, "base_agent_config.json"), "r", encoding="utf-8") as f:
    cfg = json.load(f)

cfg.pop("tools", None)              # Remove tools key (will be injected by code)
cfg.setdefault("model", DEFAULT_MODEL)   # Set explicit model

# Base agent instructions
cfg["instructions"] = BASE_INSTRUCTIONS

base_agent = Agent(**cfg)


# -----------------------------
# 2. MCP Client Configuration
# -----------------------------
fs_server = CustomMCPClient(base_url=MCP_SERVER_URL)


# -----------------------------
# 4. Main Orchestrator
# -----------------------------
orchestrator = Agent(
    name="File Search Orchestrator",
    instructions=ORCHESTRATOR_INSTRUCTIONS,
    tools=[search_files, list_recent_files],
    model=DEFAULT_MODEL,
)

# -----------------------------
# 5. CLI Loop
# -----------------------------
last_search_results = []
selected_file = None

# Handle number selection
def handle_number_selection(msg: str) -> bool:
    global last_search_results, selected_file
    if msg.isdigit() and last_search_results:
        num = int(msg)
        if 1 <= num <= len(last_search_results):
            selected_file = strip_prefix(last_search_results[num - 1])
            print(f"System> {get_message('type_open')}:\n - {selected_file}\n")
        else:
            print(f"System> {get_message('invalid_number')}\n")
        return True
    return False

# Handle "open" command
def handle_open_command(msg: str) -> bool:
    global selected_file, last_search_results
    if msg.lower() == "open":
        selected_file = try_open_selected_file(selected_file, last_search_results)
        return True
    return False


async def main() -> None:
    global last_search_results, selected_file
    trace_id = gen_trace_id()
    print(f"🔍 Trace ID: {trace_id}\n")
    print(f"Welcome to {APP_NAME} {APP_VERSION}\nType 'exit' or 'quit' to end the session\n")
    print()

    async with fs_server:
        with trace("File Search CLI", trace_id=trace_id):
            while True:
                try:
                    msg = input("Input> ")
                    if msg.lower() in {"exit", "quit"}:
                        break

                    if handle_number_selection(msg):
                        continue

                    if handle_open_command(msg):
                        continue

                    # Handle regular search
                    res = await Runner.run(starting_agent=orchestrator, input=msg)
                    print("System>", res.final_output, "\n")
                    
                    if (
                        isinstance(res.final_output, str)
                        and hasattr(res, "tool_calls")
                        and res.tool_calls
                    ):
                        
                        for tool_call in res.tool_calls:
                            if tool_call.name == "list_recent_files":
                                last_search_results = tool_call.result
                                selected_file = None

                                print("System> Here are the last files you used:\n")
                                for idx, p in enumerate(last_search_results, 1):
                                    print(f"  {idx}: {p}")
                                print("\nPlease enter the number of the file you want to open.\n")
                                break  

                    # Save search results
                    if DATA_ROOT in res.final_output:
                        numbered = re.compile(r"^\s*\d+\s*[.:]")
                        last_search_results = [
                            strip_prefix(line)
                            for line in res.final_output.split("\n")
                            if numbered.match(line) or "/data/" in line 
                        ]
                        selected_file = None
                        continue
                        
                    else:
                        last_search_results = []
                        selected_file = None

                except Exception as e:
                    print(f"System> {get_message('error_occurred')} {str(e)}\n")

def try_open_selected_file(selected_file, last_search_results):
    """選択されたファイルを開こうとする。成功すればNoneを返す"""
    if selected_file:
        file_path = selected_file
    elif last_search_results:
        if ":" not in last_search_results[0]:
            file_path = last_search_results[0].strip("- ").strip()
        else:
            file_path = None
    else:
        file_path = None
    
    if not file_path:
        print(f"System> {get_message('no_file_selected')}\n")
        return selected_file  # 状態は変えない

    real_path = resolve_real_path(file_path)
    try:
        os.startfile(real_path)
        print(f"System> {get_message('file_opened')}\n")
        return None  # ファイル開けたら選択解除
    except Exception as e:
        print(f"System> {get_message('file_error')} {str(e)}\n")
        return selected_file  # エラー時は元のまま

if __name__ == "__main__":
    asyncio.run(main())