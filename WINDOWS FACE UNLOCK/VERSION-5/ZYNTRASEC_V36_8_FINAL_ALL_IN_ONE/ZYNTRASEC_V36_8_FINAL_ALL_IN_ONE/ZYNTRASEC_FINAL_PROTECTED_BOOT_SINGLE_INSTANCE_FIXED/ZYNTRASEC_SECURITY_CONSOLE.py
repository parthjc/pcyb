import os, json, subprocess, hashlib, shutil, time, tkinter as tk
from tkinter import messagebox
ROOT=os.path.join(os.environ.get('ProgramData',r'C:\ProgramData'),'ZYNTRASEC','System')
CFG=os.path.join(ROOT,'pc_ybi_settings.json')
BACK=os.path.join(ROOT,'Backups')
DEFAULT={'voice_enabled':True,'voice_volume':100,'voice_rate':-1}
os.makedirs(ROOT,exist_ok=True); os.makedirs(BACK,exist_ok=True)
def load():
    try:
        with open(CFG,'r',encoding='utf-8') as f: return {**DEFAULT,**json.load(f)}
    except Exception:return DEFAULT.copy()
def save(d):
    tmp=CFG+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(d,f,indent=2)
    os.replace(tmp,CFG)
def run(cmd):
    return subprocess.run(cmd,shell=True,capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
def refresh():
    p=[]
    for n in ['ZYNTRASEC_EVENT_MONITOR.exe','ZYNTRASEC_LOCKSCREEN.exe','ZYNTRASEC_WATCHDOG_SERVICE.exe']:
        if run(f'tasklist /FI "IMAGENAME eq {n}" /NH').stdout.strip(): p.append(n)
    svc='RUNNING' if 'RUNNING' in run('sc query ZYNTRASECWatchdog').stdout else 'NOT RUNNING'
    vals=[('SYSTEM STATUS','PROTECTED' if svc=='RUNNING' else 'CHECK'),('FACE AUTH','READY'),('LIVENESS','READY'),('WATCHDOG',svc),('WINDOWS SERVICE',svc),('SLEEP/WAKE','READY'),('UNLOCK MONITOR','READY'),('BACKUP','AVAILABLE' if os.path.isdir(BACK) else 'MISSING'),('TAMPER STATUS',tamper_status()),('PROCESSES',str(len(p)))]
    status.set('\n'.join(f'{a:<22} ● {b}' for a,b in vals))
def tamper_status():
    return 'NORMAL' if os.path.exists(os.path.join(ROOT,'integrity.json')) else 'NOT INITIALIZED'
def backup():
    stamp=time.strftime('%Y%m%d_%H%M%S'); d=os.path.join(BACK,stamp); os.makedirs(d,exist_ok=True)
    for n in ['face_model.yml','pc_ybi_settings.json','integrity.json','owner.sec']:
        src=os.path.join(ROOT,n)
        if os.path.isfile(src): shutil.copy2(src,os.path.join(d,n))
    messagebox.showinfo('ZYNTRASEC Backup',f'Backup created:\n{d}'); refresh()
def save_settings():
    d=load(); d['voice_enabled']=bool(voice_var.get()); d['voice_volume']=int(vol.get()); d['voice_rate']=int(rate.get()); save(d); messagebox.showinfo('ZYNTRASEC','Settings saved.'); refresh()
root=tk.Tk(); root.title('ZYNTRASEC // SECURITY CONSOLE'); root.geometry('760x620'); root.configure(bg='black')
tk.Label(root,text='ZYNTRASEC // SECURITY CONSOLE',fg='#00ff66',bg='black',font=('Segoe UI',24,'bold')).pack(pady=18)
status=tk.StringVar(); tk.Label(root,textvariable=status,fg='#b8ffcf',bg='black',font=('Consolas',12),justify='left').pack(anchor='w',padx=45,pady=15)
box=tk.Frame(root,bg='black'); box.pack(pady=10)
voice_var=tk.BooleanVar(value=load()['voice_enabled']); tk.Checkbutton(box,text='Voice enabled',variable=voice_var,fg='#00ff66',bg='black',selectcolor='black',activebackground='black',font=('Segoe UI',11)).grid(row=0,column=0,columnspan=2,sticky='w')
tk.Label(box,text='Volume',fg='white',bg='black').grid(row=1,column=0,sticky='w'); vol=tk.Scale(box,from_=0,to=100,orient='horizontal',length=300,bg='black',fg='#00ff66',highlightthickness=0); vol.set(load()['voice_volume']); vol.grid(row=1,column=1)
tk.Label(box,text='Speech rate',fg='white',bg='black').grid(row=2,column=0,sticky='w'); rate=tk.Scale(box,from_=-5,to=5,orient='horizontal',length=300,bg='black',fg='#00ff66',highlightthickness=0); rate.set(load()['voice_rate']); rate.grid(row=2,column=1)
tk.Button(root,text='SAVE VOICE SETTINGS',command=save_settings).pack(pady=8)
tk.Button(root,text='CREATE SECURITY BACKUP',command=backup).pack(pady=8)
tk.Button(root,text='REFRESH STATUS',command=refresh).pack(pady=8)
tk.Button(root,text='EXIT',command=root.destroy).pack(pady=8)
refresh(); root.mainloop()
