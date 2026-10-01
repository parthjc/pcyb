import os, sys, json, time, subprocess, hashlib
from pathlib import Path

APP = Path(os.environ.get('ProgramData', r'C:\ProgramData')) / 'PCYBI'
ROOT = APP / 'System'
DATA = APP / 'SecurityData'
REPORT = ROOT / 'health_report.json'

COMPONENTS = [
    'PCYBI_LOCKSCREEN.exe','PCYBI_EVENT_MONITOR.exe','PCYBI_WATCHDOG_SERVICE.exe',
    'PCYBI_SECURITY_CONSOLE.exe','PCYBI_INTEGRITY_CHECK.exe','PCYBI_DIAGNOSTICS.exe',
    'PCYBI_CONTROL_CENTER.exe','PCYBI_BACKUP.exe','PCYBI_FACE_SETUP.exe',
    'PCYBI_HEALTH_CHECK.exe','PCYBI_ADVANCED_CONTROL_CENTER.exe'
]

def run(cmd, timeout=6):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except Exception as e:
        return -1, repr(e)

def service_state():
    rc, out = run(['sc.exe','query','PCYBIWatchdog'])
    state = 'UNKNOWN'
    if 'RUNNING' in out: state = 'RUNNING'
    elif 'STOPPED' in out: state = 'STOPPED'
    elif 'START_PENDING' in out: state = 'START_PENDING'
    return state, out[-1500:]

def process_state(name):
    rc, out = run(['tasklist','/FI',f'IMAGENAME eq {name}','/NH'])
    return name.lower() in out.lower()

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    svc, svc_raw = service_state()
    files={}
    for n in COMPONENTS:
        p=ROOT/n
        files[n]={'present':p.is_file()}
        if p.is_file():
            try: files[n]['sha256']=sha256(p)
            except Exception as e: files[n]['sha256_error']=repr(e)
    report={
        'schema':'PCYBI-Health-v1',
        'timestamp':time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'service':{'name':'PCYBIWatchdog','state':svc,'query_tail':svc_raw},
        'processes':{n:process_state(n) for n in ['PCYBI_EVENT_MONITOR.exe','PCYBI_LOCKSCREEN.exe']},
        'registration':{
            'face_model':(DATA/'face_model.yml').is_file(),
            'master_password':(DATA/'master_password.json').is_file(),
            'security_enabled':(DATA/'security_enabled.flag').is_file(),
        },
        'integrity':{
            'baseline':(ROOT/'integrity.json').is_file(),
            'status_file':(ROOT/'integrity_status.json').is_file(),
            'status':None,
        },
        'audit':{'log':(DATA/'security_audit.log').is_file(),'state':(DATA/'security_audit_state.json').is_file()},
        'components':files,
    }
    try:
        p=ROOT/'integrity_status.json'
        if p.is_file(): report['integrity']['status']=json.loads(p.read_text(encoding='utf-8'))
    except Exception: pass
    report['overall']='HEALTHY'
    reasons=[]
    if svc != 'RUNNING': reasons.append('watchdog_service_not_running')
    if not report['registration']['face_model'] or not report['registration']['master_password']:
        reasons.append('owner_registration_incomplete')
    if not report['integrity']['baseline']: reasons.append('integrity_baseline_missing')
    missing=[n for n,v in files.items() if not v['present']]
    if missing: reasons.append('missing_components')
    if report['integrity']['status'] and report['integrity']['status'].get('ok') is False: reasons.append('integrity_failed')
    if reasons: report['overall']='ATTENTION'; report['reasons']=reasons
    else: report['reasons']=[]
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['overall']=='HEALTHY' else 2

if __name__=='__main__': raise SystemExit(main())
