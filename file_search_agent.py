import asyncio
import json
import os
import requests
from agents import Agent, Runner, trace, gen_trace_id, function_tool
from typing import Optional, List
from config import *

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Message templates
MESSAGES = {
    'welcome': "Welcome to File Search Assistant v1.0.0\nType 'exit' or 'quit' to end the session",
    'file_found': "File found:",
    'files_found': "Related files found:",
    'no_files': "No files were found. Please try again with different keywords or check the file extension.",
    'type_open': 'Type "open" to open this file',
    'enter_number': "Please enter the number of the file you want to open.",
    'file_opened': "✓ File opened successfully",
    'file_error': "Error opening file:",
    'no_file_selected': "No file selected.",
    'invalid_number': "Invalid number. Please try again.",
    'search_tips': [
        "Make sure your spelling is correct.",
        "Try different or more general keywords.",
        "Try removing the file extension to broaden the search.",
        "Check if the file exists in the search directory."
    ]
}

# Function to get message
def get_message(key: str) -> str:
    return MESSAGES[key]

# -----------------------------
# Base Instructions
# -----------------------------
BASE_INSTRUCTIONS = r"""
You are a specialized file search agent.
When the input is in the format:
  search <pattern>
Please execute the following steps:
1. Extract the <pattern> part into variable PATTERN.
2. Call the search_files tool with {"pattern": PATTERN}.
   - Example: "search report" → {"pattern":"report"}
3. Return the results (path list) directly to standard output.

For other inputs, ignore them and guide the user about the correct usage.
"""

ORCHESTRATOR_INSTRUCTIONS = r"""
Please function as a file search system based on user instructions.

▼ Search and Open Decision
- When instructed to open a file:
  1. First search for the file
  2. If one result, ask "Would you like to open this file?"
  3. If multiple results, display numbered list and prompt for selection
  4. If no results, notify "Not found"

▼ Search Rules
- For file search instructions, extract keywords and
  pass "search <keyword>" to base_tool
- If extension specified, use "search <keyword>.<ext>" format
- Display results:
  - Single: "Type 'open' to open this file"
  - Multiple: Show numbered list and prompt "Please enter a number"

If no results (0 files), respond with "No files found"
and provide search tips.

▼ Response Examples
- Single result:
  
File found:
  - /data/reports/annual_report_2024.pdf
  Type "open" to open this file

- Multiple results:
  
Related files found:
  1: /data/reports/january_2024.pdf
  2: /data/reports/february_2024.pdf
  3: /data/reports/march_2024.pdf
  Please enter the number of the file you want to open.
"""

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
# 1. Custom MCP Client Implementation
# -----------------------------
class CustomMCPClient:
    def __init__(self, base_url):
        self.base_url = base_url

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def call(self, method, params=None):
        if method != "resources/list":
            raise ValueError(f"Unsupported method: {method}")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")
            
            resources = result.get("result", {})
            if isinstance(resources, list):
                return resources
            elif isinstance(resources, dict):
                return resources.get("resources", [])
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to MCP server: {e}")
            return []
        except Exception as e:
            print(f"Error processing MCP response: {e}")
            return []

# -----------------------------
# 2. MCP Client Configuration
# -----------------------------
fs_server = CustomMCPClient(base_url=MCP_SERVER_URL)

# -----------------------------
# 3. Convert Base Agent to Tool
# -----------------------------
@function_tool
async def search_files(pattern: str) -> List[str]:
    """Search for files matching the pattern.
    
    Args:
        pattern: Pattern to search for
    
    Returns:
        A list of matching file paths
    """
    try:
        params = {"pattern": pattern}
        results = await fs_server.call("resources/list", params)
        
        matches = []
        for result in results:
            if isinstance(result, dict):
                name = result.get("name", "")
                uri = result.get("uri", "")
                if pattern.lower() in name.lower() and uri.startswith("file:///"):
                    path = uri.replace("file:///", "")
                    matches.append(f"/data/{path}")
        
        return matches
        
    except Exception as e:
        print(f"Error during file search: {e}")
        return []

# -----------------------------
# 4. Main Orchestrator
# -----------------------------
orchestrator = Agent(
    name="File Search Orchestrator",
    instructions=ORCHESTRATOR_INSTRUCTIONS,
    tools=[search_files],
    model=DEFAULT_MODEL,
)

# -----------------------------
# 5. CLI Loop
# -----------------------------
last_search_results = []
selected_file = None

async def main() -> None:
    global last_search_results, selected_file
    trace_id = gen_trace_id()
    print(f"🔍 Trace ID: {trace_id}\n")
    print(get_message('welcome'))
    print()

    async with fs_server:
        with trace("File Search CLI", trace_id=trace_id):
            while True:
                try:
                    msg = input("Input> ")
                    if msg.lower() in {"exit", "quit"}:
                        break

                    # Handle number selection
                    if msg.isdigit() and last_search_results:
                        num = int(msg)
                        if 1 <= num <= len(last_search_results):
                            selected_file = last_search_results[num - 1].split(": ")[1].strip()
                            print(f"System> {get_message('type_open')}:\n - {selected_file}\n")
                            continue
                        else:
                            print(f"System> {get_message('invalid_number')}\n")
                            continue

                    # Handle "open" command
                    if msg.lower() == "open":
                        file_path = selected_file or (
                            last_search_results[0].strip("- ").strip()
                            if last_search_results and ":" not in last_search_results[0]
                            else None
                        )
                        if not file_path:
                            print(f"System> {get_message('no_file_selected')}\n")
                            continue

                        real_path = os.path.join(DOCUMENTS_PATH, file_path.replace("/data/", ""))
                        try:
                            os.startfile(real_path)
                            print(f"System> {get_message('file_opened')}\n")
                            selected_file = None  # Reset selection
                            continue
                        except Exception as e:
                            print(f"System> {get_message('file_error')} {str(e)}\n")
                            continue

                    # Handle regular search
                    res = await Runner.run(starting_agent=orchestrator, input=msg)
                    print("System>", res.final_output, "\n")

                    # Save search results
                    if "/data/" in res.final_output:
                        if "1:" in res.final_output:
                            last_search_results = [
                                line.strip()
                                for line in res.final_output.split("\n")
                                if line.strip().startswith(tuple(str(i)+":" for i in range(10)))
                            ]
                            selected_file = None
                        else:
                            last_search_results = [
                                line.strip() for line in res.final_output.split("\n") if "/data/" in line
                            ]
                            if "open" in res.final_output.split("\n")[-1].lower():
                                file_path = last_search_results[0].strip("- ").strip()
                                real_path = os.path.join(DOCUMENTS_PATH, file_path.replace("/data/", ""))
                                try:
                                    os.startfile(real_path)
                                    print(f"System> {get_message('file_opened')}\n")
                                except Exception as e:
                                    print(f"System> {get_message('file_error')} {str(e)}\n")
                    else:
                        last_search_results = []
                        selected_file = None

                except Exception as e:
                    print(f"System> Error occurred: {str(e)}\n")

if __name__ == "__main__":
    asyncio.run(main())