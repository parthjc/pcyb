import os, sys, json, hashlib, subprocess, time, platform
from pathlib import Path

APP = Path(os.environ.get('ProgramData', r'C:\ProgramData')) / 'PCYBI'
ROOT = APP / 'System'
DATA = APP / 'SecurityData'

REQUIRED = [
    'PCYBI_FACE_SETUP.exe','PCYBI_WATCHDOG_SERVICE.exe','PCYBI_EVENT_MONITOR.exe',
    'PCYBI_LOCKSCREEN.exe','PCYBI_SECURITY_CONSOLE.exe','PCYBI_INTEGRITY_CHECK.exe',
    'PCYBI_DIAGNOSTICS.exe','PCYBI_CONTROL_CENTER.exe','PCYBI_BACKUP.exe',
    'PCYBI_HEALTH_CHECK.exe','PCYBI_ADVANCED_CONTROL_CENTER.exe','PCYBI_ALL_IN_ONE.exe'
]

def cmd(args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=8,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except Exception as e:
        return 99, repr(e)

def sha256(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def main():
    results = {}
    results['platform'] = platform.platform()
    results['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    results['components'] = {n: {'present': (ROOT/n).is_file(), 'sha256': sha256(ROOT/n) if (ROOT/n).is_file() else None} for n in REQUIRED}
    rc, out = cmd(['sc.exe','query','PCYBIWatchdog'])
    results['service'] = {'returncode': rc, 'running': 'RUNNING' in out.upper(), 'raw_tail': out[-1200:]}
    results['registration'] = {
        'face_model': (DATA/'face_model.yml').is_file(),
        'master_password': (DATA/'master_password.json').is_file(),
        'security_flag': (DATA/'security_enabled.flag').is_file(),
    }
    results['security_files'] = {
        n: (DATA/n).is_file() for n in ['auth_state.json','security_audit.log','security_audit_state.json']
    }
    results['integrity'] = {'baseline': (ROOT/'integrity.json').is_file(), 'status': None}
    try:
        if (ROOT/'integrity_status.json').is_file():
            results['integrity']['status'] = json.loads((ROOT/'integrity_status.json').read_text(encoding='utf-8'))
    except Exception as e:
        results['integrity']['read_error'] = repr(e)
    results['overall'] = 'PASS'
    failures = []
    missing = [n for n,v in results['components'].items() if not v['present']]
    if missing: failures.append('missing_components')
    if rc == 0 and not results['service']['running']: failures.append('watchdog_not_running')
    if not results['registration']['face_model'] or not results['registration']['master_password']:
        failures.append('owner_registration_incomplete')
    if not results['integrity']['baseline']: failures.append('integrity_baseline_missing')
    if failures:
        results['overall'] = 'ATTENTION'
        results['failures'] = failures
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT/'final_test_report.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
    return 0 if results['overall'] == 'PASS' else 2

if __name__ == '__main__': raise SystemExit(main())
