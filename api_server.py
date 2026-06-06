#!/usr/bin/env python3
"""
freeWillAi local REST API — openclaw-style agent endpoint.
Runs on port 5001, allows external queries of agent state.
Usage: python3 api_server.py
"""
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
import urllib.parse

REPO = Path('/home/pi/freeWillAi')


def get_state():
    state_file = REPO / '.freeWill_state.json'
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def get_kv():
    kv_file = REPO / 'memory' / 'kv.json'
    if kv_file.exists():
        return json.loads(kv_file.read_text())
    return {}


def get_recent_log(n=20):
    log = REPO / 'daemon.log'
    if log.exists():
        lines = log.read_text().splitlines()
        return lines[-n:]
    return []


class AgentHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silent

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == '/' or path == '/status':
            state = get_state()
            goals = state.get('goals', [])
            active_goals = [g for g in goals if g.get('status') == 'active']
            self.send_json({
                'agent': 'freeWillAi',
                'iterations': state.get('iterations', 0),
                'last_run': state.get('last_run', 'unknown'),
                'improvements_made': len(state.get('improvements_made', [])),
                'active_goals': [g['description'][:100] for g in active_goals],
                'funding_attempts': state.get('funding_attempts', 0),
                'daemon_running': bool(subprocess.run(['pgrep', '-f', 'continuous_daemon.sh'],
                                                       capture_output=True).stdout.strip()),
            })

        elif path == '/log':
            self.send_json({'lines': get_recent_log(30)})

        elif path == '/memory':
            self.send_json({'kv': get_kv()})

        elif path == '/improvements':
            imp_dir = REPO / 'improvements'
            files = []
            if imp_dir.exists():
                for f in sorted(imp_dir.glob('iter_*.py'))[-10:]:
                    files.append({
                        'name': f.name,
                        'size': f.stat().st_size,
                        'preview': f.read_text()[:200]
                    })
            self.send_json({'count': len(list(imp_dir.glob('iter_*.py'))) if imp_dir.exists() else 0,
                           'recent': files})

        elif path == '/models':
            try:
                import requests
                r = requests.get('http://localhost:11434/api/tags', timeout=3)
                models = r.json().get('models', []) if r.status_code == 200 else []
                self.send_json({'local_models': [m['name'] for m in models]})
            except Exception as e:
                self.send_json({'error': str(e)}, 500)

        else:
            self.send_json({'error': 'not found', 'endpoints': ['/', '/status', '/log', '/memory', '/improvements', '/models']}, 404)


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 5001), AgentHandler)
    print('freeWillAi API running on http://0.0.0.0:5001')
    server.serve_forever()
