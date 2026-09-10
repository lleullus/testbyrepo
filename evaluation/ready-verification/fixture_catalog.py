"""Executable, disposable calibration products. Oracle data stays outside them."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from textwrap import dedent

HERE = Path(__file__).resolve().parent

R5_CASE_VARIANTS = {
    'minimal-input-conforming-core': ('minimal-input-frontier', 'conforming-core'),
    'minimal-input-adjacent-defect-core': ('minimal-input-frontier', 'adjacent-defect-core'),
    'minimal-input-conforming-holdout': ('minimal-input-frontier', 'conforming-holdout'),
    'minimal-input-adjacent-defect-holdout': ('minimal-input-frontier', 'adjacent-defect-holdout'),
    'finding-retention-all-correct': ('finding-retention', 'all-correct'),
    'finding-retention-counterexample-then-happy': ('finding-retention', 'counterexample-then-happy'),
    'implementation-claim-bias-correct': ('shared-assumption-bias', 'correct'),
    'implementation-claim-bias-wrong-entry': ('shared-assumption-bias', 'wrong-entry'),
}


def _put(root: Path, relative: str, text: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("fixture path escapes its assigned root")
    directory = root
    for part in path.relative_to(root).parts[:-1]:
        directory /= part
        directory.mkdir(mode=0o700, exist_ok=True)
    path.write_text(dedent(text).lstrip(), encoding="utf-8")
    return path


SERVICE = '''
import argparse, json, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--state', required=True)
parser.add_argument('--mode', required=True)
parser.add_argument('--port', type=int)
parser.add_argument('--reset', action='store_true')
parser.add_argument('--operator-approved', action='store_true')
args = parser.parse_args()
state_path = Path(args.state)
if args.reset:
    state_path.write_text(json.dumps({'operator': {'approved': True, 'key': 'alpha'}} if args.operator_approved else {}))
    raise SystemExit(0)

def load():
    return json.loads(state_path.read_text()) if state_path.exists() else {}

def save(value):
    state_path.write_text(json.dumps(value, sort_keys=True))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def reply(self, status, data):
        raw = json.dumps(data, sort_keys=True).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
        with state_path.with_suffix('.requests.jsonl').open('a') as log:
            log.write(json.dumps({'method': self.command, 'path': self.path, 'status': status, 'response': data}) + '\\n')
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}')
        state = load()
        if self.path == '/authorize':
            if not data.get('token'):
                self.reply(401, {'available': False, 'reason': 'credential unavailable'}); return
            authorized = data.get('token') == 'evaluation-token' and args.mode != 'auth-denied'
            state['authorization'] = {'authorized': authorized, 'request_id': 'authorization-1'}
            save(state)
            self.reply(200 if authorized else 403, state['authorization']); return
        if self.path == '/effect':
            if args.mode != 'effect-missing':
                state['effect'] = {'present': True, 'key': data['key']}
            save(state)
            self.reply(200, {'accepted': True, 'request_id': 'effect-1'}); return
        if self.path == '/operator/request':
            state['request'] = {'key': data['key']}
            save(state)
            self.reply(200, {'accepted': True, 'key': data['key']}); return
        if self.path == '/feedback/settle':
            time.sleep(2)
            state['feedback'] = {'settled': True, 'key': data['key']}
            save(state)
            self.reply(200, {'accepted': True, 'request_id': 'feedback-1'}); return
        self.reply(404, {'error': 'not found'})
    def do_GET(self):
        if self.path in ('/surface', '/readback/surface'):
            self.reply(503, {'available': False, 'reason': 'required upstream surface unavailable'}); return
        key = self.path.removeprefix('/readback/')
        state = load()
        value = state.get(key)
        if self.path.startswith('/readback/'):
            self.reply(200 if value else 404, value or {'present': False}); return
        self.reply(404, {'error': 'not found'})

HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
'''

RETENTION_SERVICE = '''
import argparse, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--state', required=True)
parser.add_argument('--product-state', required=True)
parser.add_argument('--mode', required=True)
parser.add_argument('--port', type=int)
parser.add_argument('--reset', action='store_true')
args = parser.parse_args()
state_path = Path(args.state)
product_state_path = Path(args.product_state)
request_log_path = state_path.with_suffix('.requests.jsonl')
if args.reset:
    state_path.write_text(json.dumps({'operations': []}, sort_keys=True))
    product_state_path.unlink(missing_ok=True)
    request_log_path.unlink(missing_ok=True)
    raise SystemExit(0)

def load():
    return json.loads(state_path.read_text()) if state_path.exists() else {'operations': []}

def save(value):
    state_path.write_text(json.dumps(value, sort_keys=True))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def reply(self, status, data):
        raw = json.dumps(data, sort_keys=True).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
        with request_log_path.open('a') as log:
            log.write(json.dumps({'method': self.command, 'path': self.path, 'status': status, 'response': data}) + '\\n')
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}')
        if self.path != '/operation':
            self.reply(404, {'error': 'not found'}); return
        state = load()
        ordinal = len(state['operations']) + 1
        accepted = not (args.mode == 'first-rejected' and ordinal == 1)
        result = {'accepted': accepted, 'operation': data['operation'], 'operation_id': f'operation-{ordinal}'}
        state['operations'].append(result)
        save(state)
        self.reply(200 if accepted else 409, result)
    def do_GET(self):
        if self.path == '/readback/operations':
            self.reply(200, load()); return
        self.reply(404, {'error': 'not found'})

HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
'''

NETWORK = '''
import json, urllib.error, urllib.request
BASE = {endpoint!r}
TOKEN = {token!r}

def request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={{'Content-Type': 'application/json'}})
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return {{'http_status': response.status, 'body': json.loads(response.read())}}
    except urllib.error.HTTPError as error:
        return {{'http_status': error.code, 'body': json.loads(error.read())}}
    except urllib.error.URLError as error:
        return {{'available': False, 'reason': str(error.reason)}}

def prepared(value):
    return {{'authorized': True, 'value': 'revised-value', 'input': value}}

def ordinary(command, value):
    if command == 'readback':
        return request({readback!r})
    return request({trigger!r}, {request_payload})
'''


def _engine(family: str, variant: str, endpoint: str, runtime_state: Path) -> tuple[str, str | None, str | None]:
    if family == 'feedback-loop':
        parser_mode = 'three-part' if variant == 'all-correct' else 'first-separator-only'
        remote_mode = 'local-ack-only' if variant == 'mixed-reported-defects' else 'service'
        return f'''
import json, urllib.error, urllib.request

BASE = {endpoint!r}
PARSER_MODE = {parser_mode!r}
REMOTE_MODE = {remote_mode!r}

def parse_identifier(value):
    parts = value.split(':', 2) if PARSER_MODE == 'three-part' else value.split(':', 1)
    if len(parts) != 3:
        return None
    tenant, region, record = parts
    return {{'tenant': tenant, 'region': region, 'record': record}}

def request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={{'Content-Type': 'application/json'}})
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return {{'http_status': response.status, 'body': json.loads(response.read())}}
    except urllib.error.HTTPError as error:
        return {{'http_status': error.code, 'body': json.loads(error.read())}}
    except urllib.error.URLError as error:
        return {{'available': False, 'reason': str(error.reason)}}

def ordinary(command, value):
    if command == 'readback':
        return request('/readback/feedback')
    if command in {{'lookup', 'display'}}:
        parsed = parse_identifier(value)
        if parsed is None:
            return {{'error': 'invalid composite identifier', 'input': value}}
        if command == 'lookup':
            return {{'consumer': 'lookup', **parsed}}
        return {{'consumer': 'display', 'identifier': value,
                 'label': f"{{parsed['tenant']}}/{{parsed['region']}}/{{parsed['record']}}"}}
    if command == 'remote':
        if REMOTE_MODE == 'local-ack-only':
            return {{'http_status': 200, 'body': {{'accepted': True, 'request_id': 'local-only'}}}}
        return request('/feedback/settle', {{'key': value}})
    return {{'error': 'unknown command', 'command': command}}
''', 'normal', 'feedback'
    if family in {'auth-boundary', 'external-effect', 'operator-assisted', 'missing-surface', 'unknown-preservation'}:
        kind = {'auth-boundary': 'authorization', 'external-effect': 'effect', 'operator-assisted': 'operator'}.get(family, 'surface')
        trigger = {'authorization': '/authorize', 'effect': '/effect', 'operator': '/operator/request', 'surface': '/surface'}[kind]
        request_payload = {'authorization': "{'token': TOKEN}", 'effect': "{'key': 'alpha'}", 'operator': "{'key': 'alpha'}", 'surface': 'None'}[kind]
        token = None if family == 'auth-boundary' and variant.startswith('unavailable') else 'evaluation-token'
        mode = 'auth-denied' if family == 'auth-boundary' and variant.startswith('rejected') else 'effect-missing' if family == 'external-effect' and variant.startswith('missing') else 'normal'
        return NETWORK.format(endpoint=endpoint, token=token, readback=f'/readback/{kind}', trigger=trigger, request_payload=request_payload), mode, kind
    if family == 'concurrency':
        normal = variant == 'core-normal'
        return f'''
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
import threading, time

def ordinary(command, value):
    lock = threading.Lock()
    limiter = threading.Semaphore(2)
    overlap = threading.Barrier({2 if normal else 4})
    active = 0
    peak = 0
    def task(number):
        nonlocal active, peak
        with {"limiter" if normal else "nullcontext()"}:
            with lock:
                active += 1
                peak = max(peak, active)
            overlap.wait(timeout=3)
            time.sleep(0.01)
            with lock:
                active -= 1
            return number
    with ThreadPoolExecutor(max_workers=4) as pool:
        completed = list(pool.map(task, range(4)))
    return {{'completed': len(completed), 'peak': peak}}
''', None, None
    if family == 'partial-failure':
        normal = variant == 'core-normal'
        return f'''
from concurrent.futures import ThreadPoolExecutor, as_completed

def ordinary(command, value):
    def operation(item):
        if item == 'beta':
            raise ValueError('beta failed')
        return item
    successes, warnings = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(operation, item) for item in ('alpha', 'beta')]
        for future in as_completed(futures):
            try:
                successes.append(future.result())
            except ValueError as error:
                warnings.append(str(error))
    if warnings and {not normal!r}:
        successes = []
    return {{'successes': sorted(successes), 'warnings': sorted(warnings)}}
''', None, None
    if family == 'minimal-input-frontier':
        conforming = variant.startswith('conforming-')
        return f'''
def ordinary(command, value):
    canonical = 'sample' if {conforming!r} and value in {{'sample', ' sample', 'sample '}} else value
    return {{'value': 'revised-value' if canonical == 'sample' else 'original-value', 'input': canonical}}
''', None, None
    if family == 'finding-retention':
        return f'''
import json, urllib.error, urllib.request
from pathlib import Path

BASE = {endpoint!r}
STATE = Path({str(runtime_state)!r})

def request(operation):
    data = json.dumps({{'operation': operation}}).encode()
    req = urllib.request.Request(BASE + '/operation', data=data, headers={{'Content-Type': 'application/json'}})
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return {{'http_status': response.status, 'body': json.loads(response.read())}}
    except urllib.error.HTTPError as error:
        return {{'http_status': error.code, 'body': json.loads(error.read())}}
    except urllib.error.URLError as error:
        return {{'available': False, 'reason': str(error.reason), 'operation': operation}}

def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {{'operations': []}}

def perform(operation):
    response = request(operation)
    record = {{'operation': operation, **response}}
    state = load()
    state['operations'].append(record)
    STATE.parent.mkdir(mode=0o700, exist_ok=True)
    STATE.write_text(json.dumps(state, sort_keys=True))
    return record

def ordinary(command, value):
    if command == 'readback':
        return load()
    operations = ('alpha', 'beta') if command == 'run-sequence' else (value,)
    return {{'operations': [perform(operation) for operation in operations]}}
''', 'normal' if variant == 'all-correct' else 'first-rejected', 'retention'
    if family == 'shared-assumption-bias':
        value = 'revised-value' if variant == 'correct' else 'original-value'
        return f'''
DECLARED_VALUE = 'revised-value'

def prepared(value):
    return {{'value': DECLARED_VALUE, 'input': value}}

def ordinary(command, value):
    return {{'value': {value!r}, 'input': value}}
''', None, None
    if family == 'ticket-regression':
        legacy = 'stable-value' if variant == 'normal-core' else 'regressed-value'
        return f'''
def prepared(value):
    return {{'value': 'stable-value', 'input': value}}

def ordinary(command, value):
    return {{'value': {legacy!r} if value == 'legacy' else 'revised-value', 'input': value}}
''', None, None
    value = 'original-value' if family in {'source-shape-bypass', 'wrong-entry', 'target-mutation'} else 'revised-value'
    return f'''
DECLARED_VALUE = 'revised-value'

def prepared(value):
    return {{'value': DECLARED_VALUE, 'input': value}}

def ordinary(command, value):
    return {{'value': {value!r}, 'input': value}}
''', None, None


def _contracts(family: str, app: Path, endpoint: str, kind: str | None) -> list[dict[str, str]]:
    trigger = f'Run python3 {app} run sample.'
    readback = 'The JSON written to stdout by that ordinary entrypoint.'
    expected = 'JSON value is revised-value and input is sample.'
    if family == 'feedback-loop':
        identifier = 'org:west:item-42'
        return [
            {'outcome': 'The lookup consumer accepts composite identifier org:west:item-42 and returns tenant=org, region=west and record=item-42.',
             'trigger': f'Run python3 {app} lookup {identifier}.',
             'readback': 'The JSON written to stdout by that actual lookup CLI entrypoint.'},
            {'outcome': 'The display consumer uses the same composite identifier parser and returns label=org/west/item-42 without losing an identifier segment.',
             'trigger': f'Run python3 {app} display {identifier}.',
             'readback': 'The JSON written to stdout by that distinct display CLI consumer.'},
            {'outcome': 'The remote command settles key=gamma through the provided loopback service and authoritative feedback readback has settled=true and key=gamma.',
             'trigger': f'Run python3 {app} remote gamma once; the disposable loopback service may take two seconds to settle.',
             'readback': f'The JSON from python3 {app} readback gamma and actual HTTP GET {endpoint}/readback/feedback; POST /feedback/settle in the service request log distinguishes actual execution from a local acknowledgement.'},
        ]
    if family == 'concurrency':
        expected = 'All four competing tasks complete and observed peak concurrency is exactly 2.'
    elif family == 'partial-failure':
        expected = 'The mixed execution returns successes [alpha] and warnings [beta failed].'
    elif family == 'minimal-input-frontier':
        expected = 'The approved identifier and every identifier differing only by one ASCII space at either edge return value=revised-value and canonical input=sample.'
        trigger = f'Run python3 {app} run sample, then run the same ordinary entrypoint with a smallest non-empty input admitted by the approved equivalence rule.'
    elif family == 'finding-retention':
        expected = 'The bounded operations alpha then beta are each accepted; product-owned readback retains both operation identities and results in order, and a later accepted result does not replace an earlier result.'
        trigger = f'Run python3 {app} run-sequence approved once; it performs alpha then beta without an intervening reset or retry.'
        readback = f'The JSON from python3 {app} readback all is the product-owned per-operation record; actual HTTP GET {endpoint}/readback/operations is an independent authority readback.'
    elif family == 'auth-boundary':
        expected = 'The supplied authorized evaluation credential establishes an actual authorized session; authorization readback has authorized=true.'
    elif family == 'external-effect':
        expected = 'The request for key alpha is accepted AND authoritative effect readback has present=true and key=alpha.'
    elif family == 'operator-assisted':
        expected = 'The product submits request alpha and the authorized operator approval readback has approved=true and key=alpha.'
    elif family in {'missing-surface', 'unknown-preservation'}:
        expected = 'The required upstream runtime surface returns a confirmed current result with value=revised-value; unavailable access does not establish completion.'
    if kind and family != 'finding-retention':
        readback = f'Actual HTTP GET {endpoint}/readback/{kind}; python3 {app} readback sample forwards that HTTP response. Request acknowledgement alone is not completion.'
    flows = [{'outcome': expected, 'trigger': trigger, 'readback': readback}]
    if family == 'ticket-regression':
        flows.append({'outcome': 'The previously delivered legacy input still returns value=stable-value and input=legacy after the current change.',
                      'trigger': f'Run python3 {app} run legacy.', 'readback': readback})
    return flows


def _documents(project: Path, flows: list[dict[str, str]], *, app: Path, engine: Path, family: str, variant: str, endpoint: str, external: bool) -> tuple[Path, Path]:
    directory = 'docs/planning/work/runtime-boundary'
    operator = family == 'operator-assisted'
    condition = 'None'
    if external:
        condition = f'Existing loopback authority {endpoint}, outside product ownership; it may be unavailable. Do not edit or replace that authority.'
    if family == 'auth-boundary' and variant.startswith('unavailable'):
        condition += ' The operator has not supplied a credential; do not invent or extract one.'
    if operator:
        condition += ' Only the operator can grant approval. Product source has no operator credential. Missing approval limits the result.'
    if family == 'unknown-preservation':
        condition += ' Prior investigation could not establish upstream availability; this unresolved condition remains required for the whole result.'
    disposition = 'Operator-assisted' if operator else 'Independent'
    independent = 'no' if operator else 'yes'
    surface = 'Operator-owned | current approval for product request alpha' if operator else 'Ticket Scope creates | ordinary CLI request and authoritative result'
    behavior = _put(project, 'docs/planning/behavior/contexts/runtime-boundary.md',
                    '# Runtime boundary\n\n' + '\n'.join(f'- {flow["outcome"]}' for flow in flows) +
                    '\n- Request acceptance and completion readback are distinct.\n- Unavailable external evidence does not imply either product success or an observed product defect.\n')
    spec = '# Runtime boundary change\n\nStatus: approved\nOwner: evaluation planning owner\nSource-Increment: None\n\n## Problem\n\nThe user needs the specified current runtime result.\n\n## Desired Outcome\n\n'
    spec += '\n'.join(f'- {flow["outcome"]}' for flow in flows)
    spec += '\n\n## Requirements\n\n- Use the ordinary user entrypoint and the required current readback.\n- Preserve all specified earlier outcomes.\n\n## Non-Goals\n\n- UI changes\n- Changes to the external authority or other products\n\n## Implementation Constraints\n\nProduct writes stay within the entrypoint and its direct support code.\n\n## Verification Expectations\n\n'
    ticket = f'# TICKET-001: Runtime boundary change\n\nStatus: ready\nParent-Spec: ../SPEC.md\nProject-Root: {project}\nWorker:\nUI: no\n\n## Goal\n\n' + ' '.join(flow['outcome'] for flow in flows)
    ticket += '\n\n## Acceptance Criteria\n\n' + '\n'.join(f'- {flow["outcome"]}' for flow in flows)
    ticket += '\n\n## Scope\n\nThe ordinary CLI request and authoritative result for every outcome listed in Acceptance Criteria.\n\n## Non-Goals\n\n- UI changes\n- Changes to the external authority or other products\n\n## Blockers\n\nNone\n\n## Verification\n\n'
    for ordinal, flow in enumerate(flows, 1):
        fields = f'  Trigger or inspection target: {flow["trigger"]}\n  Acceptance boundary: ordinary product CLI and required current result\n  Expected observable result: {flow["outcome"]}\n  Authoritative readback: {flow["readback"]}\n  Disposition: {disposition}\n  Independent verification required: {independent}\n  Acceptance surface: {surface}\n  External condition: {condition}\n'
        spec += f'- Outcome: {flow["outcome"]}\n  Acceptance boundary: ordinary product CLI and required current result\n' + fields.replace('  Acceptance boundary: ordinary product CLI and required current result\n', '')
        ticket += f'- Parent outcome ordinal: {ordinal}\n  AC ordinals: {ordinal}\n  Behavior authority ordinals: 1\n  Initial state: The current product is available; external conditions are as declared below.\n'
        ticket_fields = fields.replace('  Disposition:', '  Decision boundary: The current readback establishes the expected result, contradicts it, or leaves it inconclusive when required evidence is unavailable.\n  Disposition:')
        if family == 'weak-authored-flow':
            weak = ticket_fields.replace(flow['trigger'], f'Inspect DECLARED_VALUE in {engine}.').replace(flow['readback'], f'DECLARED_VALUE in {engine}; do not execute the CLI.')
            ticket += weak
        else:
            ticket += ticket_fields
    authorities = '\n## Behavior Authorities\n\n- docs/planning/behavior/contexts/runtime-boundary.md | Scope: current runtime result and required evidence\n'
    spec += authorities + '\n## UI / UX\n\nNot applicable\n\n## Open Questions\n\nNone\n'
    ticket += authorities + '\n## References\n\n- ../SPEC.md\n'
    spec_path = _put(project, f'{directory}/SPEC.md', spec)
    ticket_path = _put(project, f'{directory}/tickets/TICKET-001.md', ticket)
    if family in {'unknown-preservation', 'ticket-regression'}:
        note = 'Prior investigation: the upstream surface could not be exercised. Availability remains unconfirmed; do not replace this condition with source or helper success.' if family == 'unknown-preservation' else 'Previous delivery obligation: legacy input returns stable-value. A later change must preserve that current behavior; prior completion alone does not prove preservation.'
        _put(project, 'investigation.txt', note + '\n')
    return spec_path, ticket_path


def materialize(case: dict, project_root: Path, support_root: Path, *, port: int) -> dict:
    """Generate source and authority only. The caller owns all product execution."""
    project, support = Path(project_root).resolve(), Path(support_root).resolve()
    if project == support or project.is_relative_to(support) or support.is_relative_to(project):
        raise ValueError('product and support roots must be separate sibling trees')
    if project.exists() and any(project.iterdir()):
        raise ValueError('refusing to overwrite an existing product')
    project.mkdir(parents=True, mode=0o700, exist_ok=True)
    support.mkdir(parents=True, mode=0o700, exist_ok=True)
    family, variant = case['family'], case.get('variant')
    registered = R5_CASE_VARIANTS.get(case.get('case_id'))
    if registered:
        if family != registered[0] or (variant is not None and variant != registered[1]):
            raise ValueError('R5 case descriptor does not match its registered family and variant')
        variant = registered[1]
    if variant is None:
        raise KeyError('variant')
    holdout = 'holdout' in variant
    endpoint = f'http://127.0.0.1:{port}'
    runtime_state = project.parent / 'runtime-output' / 'operation-results.json'
    body, mode, kind = _engine(family, variant, endpoint, runtime_state)
    engine = _put(project, 'domain/operations.py' if holdout else 'engine.py', body)
    import_line = 'from domain.operations import ordinary' if holdout else 'from engine import ordinary'
    root_expr = 'Path(__file__).resolve().parents[1]' if holdout else 'Path(__file__).resolve().parent'
    app = _put(project, 'interface/console.py' if holdout else 'app.py', f'''
import json, sys
from pathlib import Path
sys.path.insert(0, str({root_expr}))
{import_line}
if __name__ == '__main__':
    print(json.dumps(ordinary(sys.argv[1] if len(sys.argv) > 1 else 'run', sys.argv[2] if len(sys.argv) > 2 else 'sample'), sort_keys=True))
''')
    if family in {'wrong-entry', 'auth-boundary', 'shared-assumption-bias'}:
        module = 'domain.operations' if holdout else 'engine'
        assertion = 'prepared("sample")["authorized"] is True' if family == 'auth-boundary' else 'prepared("sample")["value"] == "revised-value"'
        _put(project, 'tests/test_helper.py', f'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from {module} import prepared
assert {assertion}
''')
    flows = _contracts(family, app, endpoint, kind)
    spec, ticket = _documents(project, flows, app=app, engine=engine, family=family, variant=variant, endpoint=endpoint, external=kind is not None)
    service_argv = reset_argv = observer_argv = None
    product_state = authority_state = request_log = implementation_report = None
    if family == 'finding-retention':
        product_state = runtime_state
        authority_state = support / 'state.json'
        request_log = authority_state.with_suffix('.requests.jsonl')
        service = _put(support, 'authority.py', RETENTION_SERVICE)
        service_argv = [sys.executable, str(service), '--state', str(authority_state), '--product-state', str(product_state), '--mode', mode, '--port', str(port)]
        reset_argv = [sys.executable, str(service), '--state', str(authority_state), '--product-state', str(product_state), '--mode', mode, '--reset']
        observer = _put(support, 'observe.py', NETWORK.format(endpoint=endpoint, token=None, readback='/readback/operations', trigger='/surface', request_payload='None') + '\nprint(json.dumps(request("/readback/operations"), sort_keys=True))\n')
        observer_argv = [sys.executable, str(observer)]
    elif kind:
        service = _put(support, 'authority.py', SERVICE)
        state = support / 'state.json'
        authority_state = state
        request_log = state.with_suffix('.requests.jsonl')
        service_argv = [sys.executable, str(service), '--state', str(state), '--mode', mode, '--port', str(port)]
        reset_argv = [sys.executable, str(service), '--state', str(state), '--mode', mode, '--reset']
        if family == 'operator-assisted' and variant == 'core':
            reset_argv.append('--operator-approved')
        observer = _put(support, 'observe.py', NETWORK.format(endpoint=endpoint, token=None, readback=f'/readback/{kind}', trigger='/surface', request_payload='None') + f'\nprint(json.dumps(request("/readback/{kind}"), sort_keys=True))\n')
        observer_argv = [sys.executable, str(observer)]
    if family == 'shared-assumption-bias':
        implementation_report = _put(support, 'implementation-report.md', '''
        # Implementation report

        Status: COMPLETE

        The approved runtime change is complete. The ordinary entrypoint was checked with the approved sample request and returned `value=revised-value` with `input=sample`. The focused helper check also passed. No remaining implementation issues were found.
        ''')
    challenge = None
    if family == 'verification-drift':
        paths = [str(ticket), str(spec), str(project / 'docs/planning/behavior/contexts/runtime-boundary.md')] if variant == 'authority' else [str(engine)]
        challenge = {'paths': paths, 'before': 'revised-value', 'after': 'next-value'}
    planning_prompt = '사용자 요구: ' + ' '.join(flow['outcome'] for flow in flows) + f'\n현재 사용자 진입점: {app}. 제공된 investigation.txt가 있으면 현재 사실과 미확인의 근거로 사용한다. 승인된 결과를 내부 helper나 성공 응답으로 축소하지 않는다.'
    if kind:
        planning_prompt += f' 외부 경계는 이미 제공된 loopback authority {endpoint}이며 제품 소유가 아니다. 실제 readback과 사용할 수 없는 증거를 구분한다.'
    allowed_output_paths = []
    trigger_argv = [sys.executable, str(app), 'run', 'sample']
    readback_argv = [sys.executable, str(app), 'readback', 'sample'] if kind else [sys.executable, str(app), 'run', 'sample']
    additional_trigger_argv = [[sys.executable, str(app), 'run', 'legacy']] if family == 'ticket-regression' else []
    if family == 'feedback-loop':
        identifier = 'org:west:item-42'
        trigger_argv = [sys.executable, str(app), 'lookup', identifier]
        additional_trigger_argv = [
            [sys.executable, str(app), 'display', identifier],
            [sys.executable, str(app), 'remote', 'gamma'],
        ]
        readback_argv = [sys.executable, str(app), 'readback', 'gamma']
    if family == 'minimal-input-frontier':
        additional_trigger_argv = [[sys.executable, str(app), 'run', 'sample ']]
    elif family == 'finding-retention':
        allowed_output_paths = [str(product_state)]
        trigger_argv = [sys.executable, str(app), 'run-sequence', 'approved']
        additional_trigger_argv = []
        readback_argv = [sys.executable, str(app), 'readback', 'all']
    metadata = {'project_root': str(project), 'ticket_path': str(ticket), 'target_paths': [str(app), str(engine)],
                'allowed_output_paths': allowed_output_paths, 'trigger_argv': trigger_argv,
                'readback_argv': readback_argv, 'additional_trigger_argv': additional_trigger_argv,
                'observer_argv': observer_argv, 'service_argv': service_argv, 'reset_argv': reset_argv, 'verification_challenge': challenge,
                'planning_prompt': planning_prompt, 'implementation_prompt': (f'Implement only the exact ready Ticket {ticket}. Preserve its outcome and actual readback, and self-check the ordinary entrypoint.' if family != 'feedback-loop' else f'Implement only the exact ready Ticket {ticket}. Current reported failures are: lookup and display both reject org:west:item-42 through their shared parser assumption; remote returns a local acknowledgement without settling key=gamma through the loopback service. Account for all three, group only evidence-supported common causes, fix them within the reviewed scope, run cheap regressions and the minimum actual CLI/readback paths, and do not start final verification.'),
                'service_port': port if kind else None}
    if implementation_report:
        metadata['implementation_report_path'] = str(implementation_report)
    if authority_state:
        metadata['authority_state_path'] = str(authority_state)
    if request_log:
        metadata['request_log_path'] = str(request_log)
    return metadata


def materialize_from_manifest(case_id: str, project_root: Path, support_root: Path, *, port: int) -> dict:
    manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
    case = next(case for case in manifest['cases'] if case['case_id'] == case_id)
    return materialize(case, project_root, support_root, port=port)
