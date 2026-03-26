import json
import subprocess
import sys
import threading
import time
import uuid


class MCPClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._start_server()

    def _start_server(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "app.mcp.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # Give the server a moment to initialise
        time.sleep(0.3)

        if self.proc.poll() is not None:
            err = self.proc.stderr.read()
            raise RuntimeError(f"MCP server failed to start:\n{err}")

    def call_tool(self, tool_name: str, args: dict) -> dict:
        """
        Send a tools/call request to the MCP server and return the result.
        Thread-safe via internal lock.
        """
        with self._lock:
            # Restart server if it crashed
            if self.proc.poll() is not None:
                self._start_server()

            request = {
                "id":     str(uuid.uuid4()),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            }

            self.proc.stdin.write(json.dumps(request) + "\n")
            self.proc.stdin.flush()

            raw      = self.proc.stdout.readline()
            response = json.loads(raw)

            if "error" in response:
                raise RuntimeError(f"MCP tool error ({tool_name}): {response['error']}")

            # result is a JSON string — parse it into a dict
            result = response.get("result", "{}")
            if isinstance(result, str):
                return json.loads(result)
            return result

    def list_tools(self) -> list:
        """Return the list of tool schemas from the MCP server."""
        with self._lock:
            request = {"id": str(uuid.uuid4()), "method": "tools/list", "params": {}}
            self.proc.stdin.write(json.dumps(request) + "\n")
            self.proc.stdin.flush()
            raw = self.proc.stdout.readline()
            return json.loads(raw).get("result", [])
