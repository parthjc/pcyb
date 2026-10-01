import tkinter as tk
from tkinter import simpledialog, messagebox
import threading, time, subprocess, winsound, ctypes, os, sys
from common import MODEL, detector, verify, has_master_password, verify_master_password, live_authenticate, load_auth_state, save_auth_state, clear_auth_state, audit

class Lock:
    MAX_FACE_FAILURES = 5
    MAX_PASSWORD_FAILURES = 5
    COOLDOWN_SECONDS = 60
    def __init__(self):
        # Single-instance guard: logon + unlock triggers can fire close together.
        # A named Windows mutex prevents duplicate ZYNTRASEC overlays.
        self._mutex = ctypes.windll.kernel32.CreateMutexW(None, False, r'Global\ZYNTRASEC_FACE_SECURITY_SINGLE_INSTANCE')
        if ctypes.windll.kernel32.GetLastError() == 183:
            raise SystemExit(0)
        self.auth_state=load_auth_state()
        self.root=tk.Tk(); self.root.title('ZYNTRASEC // PRIVATE ACCESS'); self.root.attributes('-fullscreen',True); self.root.attributes('-topmost',True); self.root.configure(bg='black'); self.root.protocol('WM_DELETE_WINDOW',lambda:None)
        tk.Label(self.root,text='ZYNTRASEC // PRIVATE ACCESS',fg='#00ff66',bg='black',font=('Segoe UI',28,'bold')).pack(pady=(90,10))
        tk.Label(self.root,text='FACE AUTHENTICATION REQUIRED',fg='white',bg='black',font=('Segoe UI',14,'bold')).pack()
        tk.Label(self.root,text='WINDOWS CAMERA\n\nZYNTRASEC stays over the desktop/taskbar while Camera captures automatically and verifies the registered face.\nAfter repeated live-video verification failures, the master password becomes available.',fg='#b8ffcf',bg='black',font=('Segoe UI',12),justify='center').pack(pady=45)
        self.s=tk.StringVar(value='STARTING...'); tk.Label(self.root,textvariable=self.s,fg='#00ff66',bg='black',font=('Segoe UI',11,'bold'),wraplength=800).pack()
        self._voice_lock = threading.Lock()
        self._voice_proc = None
        self._last_voice_text = ''
        self._last_voice_time = 0.0
        self.root.bind('<Escape>',lambda e:'break'); self.root.bind('<Alt-F4>',lambda e:'break'); self.root.after(500,lambda:threading.Thread(target=self.work,daemon=True).start())
    def overlay(self,active):
        try:
            if active:
                self.root.deiconify(); self.root.attributes('-fullscreen',True); self.root.attributes('-topmost',True); self.root.lift()
            else:
                self.root.attributes('-topmost',False); self.root.withdraw()
        except Exception: pass
    def status(self,x): self.root.after(0,self.s.set,x)
    def voice(self, text, alert=False):
        try:
            cfg_path = os.path.join(os.environ.get('ProgramData', r'C:\ProgramData'), 'ZYNTRASEC', 'System', 'pc_ybi_settings.json')
            cfg = {'voice_enabled': True, 'voice_volume': 100, 'voice_rate': -1}
            if os.path.isfile(cfg_path):
                import json as _json
                with open(cfg_path, 'r', encoding='utf-8') as _f:
                    cfg.update(_json.load(_f))
            if not cfg.get('voice_enabled', True):
                return
            _volume = max(0, min(100, int(cfg.get('voice_volume', 100))))
            _rate = max(-10, min(10, int(cfg.get('voice_rate', -1))))
            now = time.monotonic()
            with self._voice_lock:
                if text == self._last_voice_text and (now - self._last_voice_time) < 2.5:
                    return
                self._last_voice_text = text
                self._last_voice_time = now
                if alert:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                if self._voice_proc is not None and self._voice_proc.poll() is None:
                    try:
                        self._voice_proc.terminate()
                        self._voice_proc.wait(timeout=1.0)
                    except Exception:
                        pass
                safe=text.replace("'", "''")
                cmd=["powershell.exe","-NoProfile","-WindowStyle","Hidden","-Command",
                     f"Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate={_rate}; $s.Volume={_volume}; $s.Speak('{safe}')"]
                self._voice_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                                     creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except Exception:
            pass
    def master_password(self):
        self.overlay(True)
        import threading as _threading
        state=load_auth_state()
        now=time.time()
        if state['cooldown_until'] > now:
            remaining=int(state['cooldown_until']-now)
            self.status(f'MASTER PASSWORD COOLDOWN — {remaining}s REMAINING')
            audit('PASSWORD_COOLDOWN_ACTIVE', str(remaining))
            time.sleep(max(1, min(remaining, self.COOLDOWN_SECONDS)))
            return False
        for n in range(1, self.MAX_PASSWORD_FAILURES + 1):
            done = _threading.Event(); result={'ok':False}
            def build():
                box=tk.Frame(self.root,bg='black'); box.place(relx=0.5,rely=0.58,anchor='center')
                tk.Label(box,text='FACE VERIFICATION FAILED',fg='white',bg='black',font=('Segoe UI',14,'bold')).pack(pady=(0,14))
                tk.Label(box,text='ENTER MASTER PASSWORD',fg='#00ff66',bg='black',font=('Segoe UI',15,'bold')).pack(pady=(0,10))
                var=tk.StringVar(); entry=tk.Entry(box,textvariable=var,show='*',width=32,bg='#101010',fg='#00ff66',insertbackground='#00ff66',font=('Segoe UI',14),relief='solid',bd=1,justify='center')
                entry.pack(ipady=8,pady=(0,10)); msg=tk.StringVar(value=f'Attempt {n}/{self.MAX_PASSWORD_FAILURES} — press Enter')
                tk.Label(box,textvariable=msg,fg='#b8ffcf',bg='black',font=('Segoe UI',10)).pack()
                def submit(event=None):
                    pw=var.get()
                    if not pw: msg.set('ENTER PASSWORD'); return
                    if verify_master_password(pw):
                        result['ok']=True; msg.set('MASTER PASSWORD VERIFIED ✓'); audit('MASTER_PASSWORD_SUCCESS')
                    else:
                        state=load_auth_state(); state['failures']+=1; save_auth_state(state); msg.set('INCORRECT MASTER PASSWORD'); audit('MASTER_PASSWORD_FAILURE',str(state['failures']))
                    self.root.after(250,finish)
                def finish():
                    try: box.destroy()
                    except Exception: pass
                    done.set()
                entry.bind('<Return>',submit); entry.focus_force(); self.root.after(100,entry.focus_force)
            self.root.after(0,build); done.wait()
            if result['ok']:
                clear_auth_state(); self.status('MASTER PASSWORD VERIFIED ✓  ACCESS GRANTED'); self.voice('Master authentication verified. Welcome back, Sir.'); time.sleep(1); return True
            time.sleep(0.3)
        state=load_auth_state(); state['cooldown_until']=time.time()+self.COOLDOWN_SECONDS; state['failures']=0; save_auth_state(state)
        audit('PASSWORD_COOLDOWN_STARTED',str(self.COOLDOWN_SECONDS))
        self.status('MASTER PASSWORD LOCKED — 60 SECOND COOLDOWN'); self.voice('Security lockout activated. Please wait sixty seconds.',alert=True)
        time.sleep(self.COOLDOWN_SECONDS); return False

    def work(self):
        try:
            if not MODEL.exists():
                if has_master_password():
                    self.status('FACE MODEL UNAVAILABLE — MASTER AUTHENTICATION AVAILABLE')
                    if self.master_password(): self.root.after(0,self.root.destroy); return
                    return
                self.status('NO SECURITY SETUP — RUN ZYNTRASEC_FACE_SETUP.exe FIRST'); return
            if not has_master_password():
                self.status('MASTER PASSWORD NOT FOUND — RUN ZYNTRASEC_FACE_SETUP.exe FIRST'); return
            d=detector(); failures=0
            self.voice('Live face authentication required. Please look at the camera.')
            while True:
                self.status('LIVE VIDEO → LOOK AT THE CAMERA AND HOLD NATURALLY')
                result=live_authenticate(d,None,None,verify,seconds=3.5)
                if result is None:
                    failures+=1; live=False; valid=[]; records=[]
                else:
                    live,valid,records=result
                    if live:
                        best=min(x[2] for x in valid) if valid else 999.0
                        audit('FACE_AUTH_SUCCESS', f'{best:.1f}')
                        clear_auth_state()
                        self.status(f'LIVE FACE + IDENTITY VERIFIED ✓ ({best:.1f})')
                        self.voice('Live identity verified. Access granted.')
                        time.sleep(1.2); self.root.after(0,self.root.destroy); return
                    failures+=1
                    audit('FACE_AUTH_FAILURE', str(failures))
                self.status('LIVE PERSON / IDENTITY VERIFICATION FAILED — LOOK AT CAMERA AND TRY AGAIN')
                if failures==1: self.voice('Verification failed. Please look at the camera and try again.',alert=True)
                elif failures>=3: self.voice('Security alert. Multiple live verification failures detected.',alert=True)
                if failures>=self.MAX_FACE_FAILURES:
                    if self.master_password(): self.root.after(0,self.root.destroy); return
                    failures=0
                time.sleep(.8)
        except Exception as e:
            self.overlay(True); self.status('LIVE AUTH ERROR — MASTER RECOVERY AVAILABLE'); time.sleep(.5)
            if has_master_password() and self.master_password(): self.root.after(0,self.root.destroy); return
            self.status('SECURITY ERROR — PLEASE RUN ZYNTRASEC_FACE_SETUP.exe')
    def run(self): self.root.mainloop()
if __name__=='__main__': Lock().run()
