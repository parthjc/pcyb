import os,sys,json,subprocess,hashlib,time,platform
ROOT=os.path.join(os.environ.get('ProgramData',r'C:\ProgramData'),'ZYNTRASEC','System'); DATA=os.path.join(os.environ.get('ProgramData',r'C:\ProgramData'),'ZYNTRASEC','SecurityData')
os.makedirs(ROOT,exist_ok=True)
def cmd(args):
 try:
  r=subprocess.run(args,capture_output=True,text=True,timeout=12,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)); return r.returncode,r.stdout.strip(),r.stderr.strip()
 except Exception as e:return 99,'',repr(e)
def main():
 out={'timestamp':time.strftime('%Y-%m-%dT%H:%M:%S'),'os':platform.platform(),'python':platform.python_version(),'root':ROOT}
 code,stdout,err=cmd(['sc.exe','query','ZYNTRASECWatchdog']); out['service']={'code':code,'output':stdout,'error':err}
 for n in ['ZYNTRASEC_WATCHDOG_SERVICE.exe','ZYNTRASEC_EVENT_MONITOR.exe','ZYNTRASEC_LOCKSCREEN.exe','ZYNTRASEC_SECURITY_CONSOLE.exe','ZYNTRASEC_INTEGRITY_CHECK.exe']:
  p=os.path.join(ROOT,n); out.setdefault('components',{})[n]={'exists':os.path.isfile(p),'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest() if os.path.isfile(p) else None}
 for n in ['face_model.yml','master_password.json','auth_state.json','security_audit.log','security_audit_state.json']:
  p=os.path.join(DATA,n); out.setdefault('security_data',{})[n]=os.path.isfile(p)
 path=os.path.join(ROOT,'diagnostics_latest.json'); json.dump(out,open(path,'w',encoding='utf-8'),indent=2); print(json.dumps(out,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
