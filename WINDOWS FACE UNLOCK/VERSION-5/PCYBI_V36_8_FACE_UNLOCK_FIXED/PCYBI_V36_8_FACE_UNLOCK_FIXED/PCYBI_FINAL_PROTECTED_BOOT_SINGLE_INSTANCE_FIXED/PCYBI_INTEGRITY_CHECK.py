import os,sys,json,hashlib,time
ROOT=os.path.join(os.environ.get('ProgramData',r'C:\ProgramData'),'PCYBI','System')
DATA=os.path.join(os.environ.get('ProgramData',r'C:\ProgramData'),'PCYBI','SecurityData')
MAN=os.path.join(ROOT,'integrity.json'); LOG=os.path.join(ROOT,'tamper.log'); STATUS=os.path.join(ROOT,'integrity_status.json')
FILES=['PCYBI_LOCKSCREEN.exe','PCYBI_EVENT_MONITOR.exe','PCYBI_WATCHDOG_SERVICE.exe','PCYBI_SECURITY_CONSOLE.exe','PCYBI_INTEGRITY_CHECK.exe']
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def write_log(s):
 os.makedirs(ROOT,exist_ok=True)
 with open(LOG,'a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S ')+s+'\n')
def current(): return {n:sha(os.path.join(ROOT,n)) for n in FILES if os.path.isfile(os.path.join(ROOT,n))}
def snapshot():
 d=current(); os.makedirs(ROOT,exist_ok=True)
 with open(MAN,'w',encoding='utf-8') as f:json.dump(d,f,indent=2)
 write_log('INTEGRITY_BASELINE_CREATED'); json.dump({'ok':True,'changed':[],'timestamp':time.time()},open(STATUS,'w',encoding='utf-8'),indent=2); return d
def check():
 if not os.path.isfile(MAN): return snapshot(),True
 try: old=json.load(open(MAN,encoding='utf-8')); cur=current()
 except Exception as e:
  write_log('INTEGRITY_READ_ERROR '+repr(e)); return ['MANIFEST_READ_ERROR'],False
 bad=[n for n in set(old)|set(cur) if old.get(n)!=cur.get(n)]
 ok=not bad
 if not ok: write_log('TAMPER_DETECTED '+','.join(bad))
 with open(STATUS,'w',encoding='utf-8') as f: json.dump({'ok':ok,'changed':bad,'timestamp':time.time()},f,indent=2)
 return bad,ok
if __name__=='__main__':
 r,ok=check(); print('OK' if ok else 'TAMPER DETECTED: '+', '.join(r)); sys.exit(0 if ok else 2)
