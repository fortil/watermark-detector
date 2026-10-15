"""Local HTTP server that stands in for a provider's detection API."""
from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class _Mock:
    def __init__(self):
        self.url = ""
        self.requests: list[dict] = []


@contextmanager
def mock_verifier(response: dict | None = None, status: int = 200):
    mock = _Mock()
    payload = response if response is not None else {"result": {"likelihood": 0.87, "label": "likely"}}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            mock.requests.append({"headers": dict(self.headers), "body": body})
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    mock.url = f"http://127.0.0.1:{server.server_address[1]}/detect"
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield mock
    finally:
        server.shutdown()
        server.server_close()


def write_config(path: Path, url: str, name: str = "claude", api_key_env: str = "WMD_TEST_KEY", **overrides) -> Path:
    fields = {
        "endpoint": url,
        "api_key_env": api_key_env,
        "score_path": "result.likelihood",
        "label_path": "result.label",
    }
    fields.update(overrides)
    lines = [f"[verifiers.{name}]"]
    tables: dict[str, dict] = {}
    for k, v in fields.items():
        if isinstance(v, dict):
            tables[k] = v
        else:
            lines.append(f"{k} = {json.dumps(v)}")
    for k, v in tables.items():
        lines.append(f"[verifiers.{name}.{k}]")
        lines += [f"{kk} = {json.dumps(vv)}" for kk, vv in v.items()]
    path.write_text("\n".join(lines) + "\n")
    return path
