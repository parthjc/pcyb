import os, subprocess, tkinter as tk, json, time
from pathlib import Path
from tkinter import messagebox, filedialog

APP = Path(os.environ.get('ProgramData', r'C:\ProgramData')) / 'PCYBI'
ROOT = APP / 'System'
DATA = APP / 'SecurityData'

EXES = {
    'Face Setup': 'PCYBI_FACE_SETUP.exe',
    'Security Console': 'PCYBI_SECURITY_CONSOLE.exe',
    'Advanced Control Center': 'PCYBI_ADVANCED_CONTROL_CENTER.exe',
    'Health Check': 'PCYBI_HEALTH_CHECK.exe',
    'Diagnostics': 'PCYBI_DIAGNOSTICS.exe',
    'Integrity Check': 'PCYBI_INTEGRITY_CHECK.exe',
    'Backup': 'PCYBI_BACKUP.exe',
}


def run_file(name, *args):
    p = ROOT / name
    if not p.exists():
        messagebox.showerror('PCYBI', f'Missing component:\n{p}')
        return
    try:
        subprocess.Popen([str(p), *args], cwd=str(ROOT), creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except Exception as e:
        messagebox.showerror('PCYBI', str(e))


def run_bat(name):
    p = ROOT / name
    if not p.exists():
        p = Path(__file__).resolve().parent / name
    if not p.exists():
        messagebox.showerror('PCYBI', f'Missing tool:\n{p}')
        return
    subprocess.Popen(['cmd.exe', '/c', str(p)], cwd=str(p.parent))


def service_state():
    try:
        r = subprocess.run(['sc.exe', 'query', 'PCYBIWatchdog'], capture_output=True, text=True, timeout=5)
        out = r.stdout.upper()
        if 'RUNNING' in out: return 'RUNNING'
        if 'START_PENDING' in out: return 'STARTING'
        if 'STOPPED' in out: return 'STOPPED'
        return 'NOT INSTALLED'
    except Exception:
        return 'UNKNOWN'


def process_running(name):
    try:
        r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}', '/NH'], capture_output=True, text=True, timeout=5)
        return name.lower() in r.stdout.lower()
    except Exception:
        return False


def exists(name, where=ROOT):
    return (where / name).is_file()


def status_text():
    svc = service_state()
    face = exists('face_model.yml', DATA)
    password = exists('master_password.json', DATA)
    integrity = exists('integrity.json')
    audit = exists('security_audit.log', DATA)
    monitor = process_running('PCYBI_EVENT_MONITOR.exe')
    lock = process_running('PCYBI_LOCKSCREEN.exe')
    return (
        f'PCYBI V36 // ALL-IN-ONE\n'
        f'\nSERVICE        : {svc}'
        f'\nEVENT MONITOR  : {"RUNNING" if monitor else "STOPPED"}'
        f'\nLOCKSCREEN     : {"RUNNING" if lock else "IDLE"}'
        f'\nOWNER FACE     : {"REGISTERED" if face else "NOT REGISTERED"}'
        f'\nMASTER PASSWORD: {"REGISTERED" if password else "NOT REGISTERED"}'
        f'\nINTEGRITY      : {"BASELINE READY" if integrity else "NOT READY"}'
        f'\nAUDIT LOG      : {"ACTIVE" if audit else "NOT STARTED"}'
    )


def refresh():
    status.set(status_text())
    root.after(3000, refresh)


def start_service():
    r = subprocess.run(['sc.exe', 'start', 'PCYBIWatchdog'], capture_output=True, text=True)
    if r.returncode != 0:
        messagebox.showerror('PCYBI', r.stdout + r.stderr)
    refresh()


def stop_service():
    if messagebox.askyesno('PCYBI', 'Stop the PCYBI watchdog service? Protected startup will be inactive until it is started again.'):
        subprocess.run(['sc.exe', 'stop', 'PCYBIWatchdog'], capture_output=True, text=True)
        refresh()


def restart_service():
    subprocess.run(['sc.exe', 'stop', 'PCYBIWatchdog'], capture_output=True, text=True)
    time.sleep(2)
    r = subprocess.run(['sc.exe', 'start', 'PCYBIWatchdog'], capture_output=True, text=True)
    if r.returncode != 0:
        messagebox.showerror('PCYBI', r.stdout + r.stderr)
    refresh()


def restore_backup():
    p = filedialog.askopenfilename(title='Select PCYBI encrypted backup', filetypes=[('PCYBI backup', '*.pcybi'), ('All files', '*.*')])
    if p:
        run_file('PCYBI_BACKUP.exe', 'restore', p)


def open_log(name):
    p = ROOT / name
    if not p.exists():
        p = DATA / name
    if p.exists():
        subprocess.Popen(['notepad.exe', str(p)])
    else:
        messagebox.showinfo('PCYBI', f'Log not found:\n{p}')


def build_button(parent, label, fn, row, col):
    tk.Button(parent, text=label, width=26, height=2, command=fn,
              bg='#07140b', fg='#00ff66', activebackground='#0d2817',
              activeforeground='white', relief='groove', bd=1).grid(row=row, column=col, padx=7, pady=7)


root = tk.Tk()
root.title('PCYBI // FINAL ALL-IN-ONE SECURITY CENTER')
root.geometry('900x820')
root.configure(bg='black')
root.minsize(820, 720)

tk.Label(root, text='PCYBI // FINAL ALL-IN-ONE', fg='#00ff66', bg='black',
         font=('Segoe UI', 25, 'bold')).pack(pady=(20, 5))
tk.Label(root, text='V36 HARDENED SECURITY CONTROL CENTER', fg='#75ffad', bg='black',
         font=('Consolas', 11)).pack(pady=(0, 12))

status = tk.StringVar()
tk.Label(root, textvariable=status, fg='#b8ffcf', bg='black', font=('Consolas', 12),
         justify='left', anchor='w').pack(fill='x', padx=55, pady=10)

panel = tk.Frame(root, bg='black')
panel.pack(pady=8)

build_button(panel, 'OWNER FACE SETUP', lambda: run_file(EXES['Face Setup']), 0, 0)
build_button(panel, 'SECURITY CONSOLE', lambda: run_file(EXES['Security Console']), 0, 1)
build_button(panel, 'ADVANCED CONTROL', lambda: run_file(EXES['Advanced Control Center']), 1, 0)
build_button(panel, 'HEALTH CHECK', lambda: run_file(EXES['Health Check']), 1, 1)
build_button(panel, 'DIAGNOSTICS', lambda: run_file(EXES['Diagnostics']), 2, 0)
build_button(panel, 'INTEGRITY CHECK', lambda: run_file(EXES['Integrity Check']), 2, 1)
build_button(panel, 'ENCRYPTED BACKUP', lambda: run_file(EXES['Backup']), 3, 0)
build_button(panel, 'RESTORE BACKUP', restore_backup, 3, 1)
build_button(panel, 'SERVICE REPAIR', lambda: run_bat('PCYBI_SERVICE_REPAIR_ADVANCED.bat'), 4, 0)
build_button(panel, 'FULL DIAGNOSTIC TEST', lambda: run_bat('PCYBI_FINAL_TEST.bat'), 4, 1)
build_button(panel, 'START WATCHDOG', start_service, 5, 0)
build_button(panel, 'RESTART WATCHDOG', restart_service, 5, 1)
build_button(panel, 'STOP WATCHDOG', stop_service, 6, 0)
build_button(panel, 'OPEN SECURITY AUDIT', lambda: open_log('security_audit.log'), 6, 1)

tk.Button(root, text='REFRESH STATUS', width=30, command=lambda: status.set(status_text())).pack(pady=8)
tk.Button(root, text='EXIT', width=30, command=root.destroy).pack(pady=6)

refresh()
root.mainloop()
