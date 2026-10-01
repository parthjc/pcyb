import os,subprocess,tkinter as tk,json,time,hashlib
from tkinter import messagebox
ROOT=os.path.join(os.environ.get('ProgramData',r'C:\ProgramData'),'ZYNTRASEC','System'); DATA=os.path.join(os.environ.get('ProgramData',r'C:\ProgramData'),'ZYNTRASEC','SecurityData')
def run(exe,*args):
 p=os.path.join(ROOT,exe)
 if not os.path.isfile(p): messagebox.showerror('ZYNTRASEC',f'Missing component: {p}'); return
 try: subprocess.Popen([p,*args],cwd=ROOT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 except Exception as e: messagebox.showerror('ZYNTRASEC',str(e))
def check_service():
 try:
  r=subprocess.run(['sc.exe','query','ZYNTRASECWatchdog'],capture_output=True,text=True,timeout=5); return 'RUNNING' if 'RUNNING' in r.stdout else 'STOPPED'
 except: return 'UNKNOWN'
def status():
 svc=check_service(); vals=[]
 for n in ['ZYNTRASEC_EVENT_MONITOR.exe','ZYNTRASEC_LOCKSCREEN.exe','ZYNTRASEC_WATCHDOG_SERVICE.exe']:
  try: out=subprocess.run(['tasklist','/FI',f'IMAGENAME eq {n}','/NH'],capture_output=True,text=True).stdout; vals.append(f'{n}: '+('RUNNING' if n.lower() in out.lower() else 'STOPPED'))
  except: pass
 return 'SERVICE: '+svc+'\n'+'\n'.join(vals)+'\nFACE MODEL: '+('READY' if os.path.isfile(os.path.join(DATA,'face_model.yml')) else 'MISSING')+'\nMASTER PASSWORD: '+('READY' if os.path.isfile(os.path.join(DATA,'master_password.json')) else 'MISSING')+'\nAUDIT LOG: '+('READY' if os.path.isfile(os.path.join(DATA,'security_audit.log')) else 'NOT STARTED')+'\nINTEGRITY BASELINE: '+('READY' if os.path.isfile(os.path.join(ROOT,'integrity.json')) else 'MISSING')
def refresh(): s.set(status()); root.after(4000,refresh)
def open_log(name):
 p=os.path.join(ROOT,name)
 if os.path.isfile(p): subprocess.Popen(['notepad.exe',p])
 else: messagebox.showinfo('ZYNTRASEC',f'Not found: {p}')
root=tk.Tk(); root.title('ZYNTRASEC // ALL-IN-ONE SECURITY CENTER'); root.geometry('820x700'); root.configure(bg='black')
tk.Label(root,text='ZYNTRASEC // ALL-IN-ONE SECURITY CENTER',fg='#00ff66',bg='black',font=('Segoe UI',24,'bold')).pack(pady=20)
s=tk.StringVar(); tk.Label(root,textvariable=s,fg='#b8ffcf',bg='black',font=('Consolas',12),justify='left').pack(anchor='w',padx=45,pady=10)
frame=tk.Frame(root,bg='black'); frame.pack(pady=18)
buttons=[('FACE SETUP','ZYNTRASEC_FACE_SETUP.exe'),('RUN INTEGRITY CHECK','ZYNTRASEC_INTEGRITY_CHECK.exe'),('RUN DIAGNOSTICS','ZYNTRASEC_DIAGNOSTICS.exe'),('REPAIR INSTALLATION','ZYNTRASEC_REPAIR.bat'),('ENCRYPTED BACKUP','ZYNTRASEC_BACKUP.exe'),('OPEN SECURITY CONSOLE','ZYNTRASEC_SECURITY_CONSOLE.exe')]
for i,(label,exe) in enumerate(buttons): tk.Button(frame,text=label,width=28,command=(lambda e=exe: run(e) if e.endswith('.exe') else subprocess.Popen([os.path.join(os.path.dirname(__file__),e)]))).grid(row=i//2,column=i%2,padx=8,pady=8)
tk.Button(root,text='OPEN AUDIT LOG',width=28,command=lambda:open_log('security_audit.log')).pack(pady=6)
tk.Button(root,text='OPEN EVENT MONITOR LOG',width=28,command=lambda:open_log('event_monitor.log')).pack(pady=6)
tk.Button(root,text='REFRESH STATUS',width=28,command=lambda:s.set(status())).pack(pady=6)
tk.Button(root,text='EXIT',width=28,command=root.destroy).pack(pady=6)
refresh(); root.mainloop()
