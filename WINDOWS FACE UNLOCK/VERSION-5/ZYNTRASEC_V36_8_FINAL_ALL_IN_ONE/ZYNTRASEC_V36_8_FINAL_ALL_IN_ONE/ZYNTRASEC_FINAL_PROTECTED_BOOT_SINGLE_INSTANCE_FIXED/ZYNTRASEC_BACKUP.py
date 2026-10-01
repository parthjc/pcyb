import os,sys,json,zipfile,tempfile,shutil,base64,getpass,time
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

APP=Path(os.environ.get('PROGRAMDATA',r'C:\ProgramData'))/'ZYNTRASEC'
DATA=APP/'SecurityData'; ROOT=APP/'System'; BACK=ROOT/'Backups'
MAGIC=b'ZYNTRASEC-V36-BACKUP\x00'
LEGACY_MAGIC=b'ZYNTRASEC-V34-BACKUP\x00'


def key(password,salt):
    return Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(password.encode('utf-8'))

def make_backup():
    BACK.mkdir(parents=True,exist_ok=True)
    password=getpass.getpass('Backup encryption password: ')
    confirm=getpass.getpass('Confirm backup password: ')
    if len(password)<10 or password!=confirm:
        print('Backup password must be at least 10 characters and match.'); return 2
    stamp=time.strftime('%Y%m%d_%H%M%S'); tmp=Path(tempfile.mkdtemp(prefix='zyntrasec_backup_'))
    try:
        names=['face_model.yml','master_password.json','auth_state.json','security_audit.log','security_audit_state.json']
        with zipfile.ZipFile(tmp/'payload.zip','w',zipfile.ZIP_DEFLATED) as z:
            manifest = {'schema':'ZYNTRASEC-Backup-v36','created':time.strftime('%Y-%m-%dT%H:%M:%S')}
            for name in names:
                p=DATA/name
                if p.is_file(): z.write(p,name)
            for name in ['integrity.json','pc_ybi_settings.json','integrity_status.json']:
                p=ROOT/name
                if p.is_file(): z.write(p,name)
            z.writestr('backup_manifest.json', json.dumps(manifest, indent=2))
        plain=(tmp/'payload.zip').read_bytes(); salt=os.urandom(16); nonce=os.urandom(12)
        blob=AESGCM(key(password,salt)).encrypt(nonce,plain,MAGIC)
        out=BACK/f'ZYNTRASEC_V36_BACKUP_{stamp}.zyntrasec'
        out.write_bytes(MAGIC+salt+nonce+blob)
        print(f'Encrypted backup created: {out}')
        return 0
    finally: shutil.rmtree(tmp,ignore_errors=True)

def restore(path):
    password=getpass.getpass('Backup decryption password: ')
    raw=Path(path).read_bytes()
    magic = MAGIC if raw.startswith(MAGIC) else (LEGACY_MAGIC if raw.startswith(LEGACY_MAGIC) else None)
    if magic is None: print('Invalid ZYNTRASEC backup.'); return 2
    salt=raw[len(magic):len(magic)+16]; nonce=raw[len(magic)+16:len(magic)+28]; blob=raw[len(magic)+28:]
    try: plain=AESGCM(key(password,salt)).decrypt(nonce,blob,magic)
    except Exception: print('Backup password is incorrect or backup is corrupted.'); return 3
    tmp=Path(tempfile.mkdtemp(prefix='zyntrasec_restore_'))
    try:
        (tmp/'payload.zip').write_bytes(plain)
        with zipfile.ZipFile(tmp/'payload.zip') as z:
            members=[m for m in z.namelist() if not m.startswith('/') and '..' not in Path(m).parts]
            for m in members:
                target=(DATA/m if m in ['face_model.yml','master_password.json','auth_state.json','security_audit.log','security_audit_state.json'] else ROOT/m)
                target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(z.read(m))
        print('ZYNTRASEC security data restored. Restart ZYNTRASEC components before using restored credentials.')
        return 0
    finally: shutil.rmtree(tmp,ignore_errors=True)

if __name__=='__main__':
    if len(sys.argv)==1: raise SystemExit(make_backup())
    if len(sys.argv)==3 and sys.argv[1]=='restore': raise SystemExit(restore(sys.argv[2]))
    print('Usage: ZYNTRASEC_BACKUP.exe   OR   ZYNTRASEC_BACKUP.exe restore <file.zyntrasec>'); raise SystemExit(1)
