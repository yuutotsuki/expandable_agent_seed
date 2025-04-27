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
