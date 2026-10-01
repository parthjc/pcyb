import os, subprocess, tkinter as tk, json, time
from tkinter import messagebox
from pathlib import Path

ROOT=Path(os.environ.get('ProgramData',r'C:\ProgramData'))/'PCYBI'/'System'
DATA=ROOT.parent/'SecurityData'

def launch(name,*args):
    p=ROOT/name
    if not p.exists(): messagebox.showerror('PCYBI',f'Missing component:\n{p}'); return
    try: subprocess.Popen([str(p),*args],cwd=str(ROOT),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except Exception as e: messagebox.showerror('PCYBI',str(e))

def read_health():
    p=ROOT/'health_report.json'
    if not p.exists(): launch('PCYBI_HEALTH_CHECK.exe'); return None
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None

def service_query():
    try:
        r=subprocess.run(['sc.exe','query','PCYBIWatchdog'],capture_output=True,text=True,timeout=5)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e: return repr(e)

def refresh():
    launch('PCYBI_HEALTH_CHECK.exe')
    root.after(1800, update_status)

def update_status():
    h=read_health()
    if not h:
        status.set('HEALTH CHECK: unavailable')
    else:
        svc=h.get('service',{}).get('state','UNKNOWN')
        overall=h.get('overall','UNKNOWN')
        face=h.get('registration',{}).get('face_model')
        pwd=h.get('registration',{}).get('master_password')
        integ=h.get('integrity',{}).get('status') or {}
        status.set(f'OVERALL     : {overall}\nWATCHDOG    : {svc}\nFACE MODEL  : {"READY" if face else "MISSING"}\nPASSWORD    : {"READY" if pwd else "MISSING"}\nINTEGRITY   : {"OK" if integ.get("ok") is True else "CHECK"}\nAUDIT       : {"READY" if h.get("audit",{}).get("log") else "MISSING"}')
    root.after(5000,update_status)

def open_text(name):
    p=ROOT/name
    if not p.exists(): messagebox.showinfo('PCYBI',f'Not found:\n{p}'); return
    subprocess.Popen(['notepad.exe',str(p)])

def repair():
    p=Path(__file__).with_name('PCYBI_SERVICE_REPAIR_ADVANCED.bat')
    if p.exists(): subprocess.Popen(['cmd.exe','/c',str(p)],creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
    else: messagebox.showerror('PCYBI','Repair script not found in package.')

root=tk.Tk(); root.title('PCYBI // ADVANCED SECURITY CENTER V35'); root.geometry('900x760'); root.configure(bg='black')
tk.Label(root,text='PCYBI // ADVANCED SECURITY CENTER',fg='#00ff66',bg='black',font=('Segoe UI',25,'bold')).pack(pady=18)
tk.Label(root,text='V35 // HEALTH • INTEGRITY • WATCHDOG • RECOVERY',fg='#70ff9a',bg='black',font=('Consolas',11)).pack()
status=tk.StringVar(value='Loading health status...')
tk.Label(root,textvariable=status,fg='#d0ffe0',bg='black',font=('Consolas',13),justify='left',anchor='w').pack(fill='x',padx=55,pady=22)
frame=tk.Frame(root,bg='black'); frame.pack(pady=5)
buttons=[
('RUN HEALTH CHECK',lambda: refresh()),('RUN DIAGNOSTICS',lambda: launch('PCYBI_DIAGNOSTICS.exe')),
('VERIFY INTEGRITY',lambda: launch('PCYBI_INTEGRITY_CHECK.exe')),('SERVICE REPAIR',repair),
('FACE SETUP',lambda: launch('PCYBI_FACE_SETUP.exe')),('SECURITY CONSOLE',lambda: launch('PCYBI_SECURITY_CONSOLE.exe')),
('ENCRYPTED BACKUP',lambda: launch('PCYBI_BACKUP.exe')),('OPEN HEALTH REPORT',lambda: open_text('health_report.json')),
('OPEN WATCHDOG LOG',lambda: open_text('watchdog.log')),('OPEN TAMPER LOG',lambda: open_text('tamper.log')),
('OPEN AUDIT LOG',lambda: open_text('security_audit.log')),('SERVICE QUERY',lambda: messagebox.showinfo('PCYBIWatchdog',service_query()))]
for i,(label,cmd) in enumerate(buttons):
    tk.Button(frame,text=label,width=29,height=2,command=cmd).grid(row=i//2,column=i%2,padx=8,pady=7)
tk.Button(root,text='EXIT',width=30,command=root.destroy).pack(pady=18)
update_status(); root.mainloop()
