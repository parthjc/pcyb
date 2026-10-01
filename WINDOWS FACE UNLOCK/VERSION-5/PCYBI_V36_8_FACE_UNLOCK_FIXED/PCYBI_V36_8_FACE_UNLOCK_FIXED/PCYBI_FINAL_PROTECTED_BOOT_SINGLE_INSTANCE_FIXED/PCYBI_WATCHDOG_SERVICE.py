import os, time, subprocess, sys
import win32serviceutil
import win32service
import win32event
import win32ts
import win32security
import win32process
import win32profile
import win32con
import servicemanager

ROOT = os.path.join(os.environ.get('ProgramData', r'C:\ProgramData'), 'PCYBI', 'System')
MONITOR = os.path.join(ROOT, 'PCYBI_EVENT_MONITOR.exe')
LOG = os.path.join(ROOT, 'watchdog.log')
INTEGRITY = os.path.join(ROOT, 'integrity.json')
TAMPER_LOG = os.path.join(ROOT, 'tamper.log')
FILES_TO_CHECK = ['PCYBI_LOCKSCREEN.exe', 'PCYBI_EVENT_MONITOR.exe', 'PCYBI_WATCHDOG_SERVICE.exe']
SERVICE_NAME = 'PCYBIWatchdog'
DISPLAY_NAME = 'PCYBI Security Watchdog'


def log(msg):
    try:
        os.makedirs(ROOT, exist_ok=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + msg + '\n')
    except Exception:
        pass


def integrity_check():
    try:
        import hashlib, json
        if not os.path.isfile(INTEGRITY):
            return True
        with open(INTEGRITY, encoding='utf-8') as f:
            old = json.load(f)
        for name in FILES_TO_CHECK:
            path = os.path.join(ROOT, name)
            if not os.path.isfile(path):
                if name in old:
                    with open(TAMPER_LOG, 'a', encoding='utf-8') as f:
                        f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + 'MISSING_FILE ' + name + '\n')
                    try:
                        servicemanager.LogErrorMsg('PCYBI integrity failure: ' + name)
                    except Exception:
                        pass
                return False
                continue
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(chunk)
            if old.get(name) != h.hexdigest():
                with open(TAMPER_LOG, 'a', encoding='utf-8') as f:
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + 'TAMPER_DETECTED ' + name + '\n')
                try:
                    servicemanager.LogErrorMsg('PCYBI integrity failure: ' + name)
                except Exception:
                    pass
                return False
        return True
    except Exception as e:
        log('INTEGRITY_CHECK_ERROR ' + repr(e))
        return False


def active_console_session():
    try:
        sid = win32ts.WTSGetActiveConsoleSessionId()
        return None if sid == 0xFFFFFFFF else sid
    except Exception:
        return None


def process_exists_in_session(session_id):
    try:
        ps = (
            "Get-Process -Name PCYBI_EVENT_MONITOR -ErrorAction SilentlyContinue "
            "| ForEach-Object { $p=$_; try { $s=(Get-Process -Id $p.Id -IncludeUserName "
            "-ErrorAction Stop).SessionId } catch { $s=-1 }; if ($s -eq "
            f"{int(session_id)}" + ") { 'YES' } }"
        )
        r = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', ps],
            capture_output=True, text=True, timeout=6,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        return 'YES' in r.stdout
    except Exception:
        return False


def launch_as_user(session_id):
    """Trigger the per-user interactive monitor through its scheduled task.

    The watchdog runs as LocalSystem, so it does not directly create GUI
    processes in the user's desktop. The interactive scheduled task is the
    supported primary path and is automatically recreated when missing.
    """
    task_name = 'PCYBI User Event Monitor'
    try:
        q = subprocess.run(
            ['schtasks.exe', '/Query', '/TN', task_name],
            capture_output=True, text=True, timeout=8,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        if q.returncode != 0:
            log(f'MONITOR_TASK_MISSING session={session_id}')
            return False
        r = subprocess.run(
            ['schtasks.exe', '/Run', '/TN', task_name],
            capture_output=True, text=True, timeout=10,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        if r.returncode == 0:
            log(f'MONITOR_TASK_TRIGGERED session={session_id} task={task_name}')
            return True
        log(f'MONITOR_TASK_TRIGGER_FAILED session={session_id} rc={r.returncode} stderr={r.stderr.strip()}')
        return False
    except Exception as e:
        log(f'MONITOR_TASK_TRIGGER_EXCEPTION session={session_id} error={type(e).__name__}: {e}')
        return False


class PCYBIWatchdog(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = DISPLAY_NAME
    _svc_description_ = 'PCYBI boot watchdog; starts the per-user security monitor after Windows sign-in.'

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        log('WATCHDOG_START')
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        log('WATCHDOG_SERVICE_RUNNING')
        last_integrity = 0
        integrity_ok = True
        while self.running:
            now = time.monotonic()
            if now - last_integrity >= 30:
                integrity_ok = integrity_check()
                last_integrity = now
                if not integrity_ok:
                    log('FAIL_CLOSED_INTEGRITY_STATE')
            sid = active_console_session()
            if integrity_ok and sid is not None and os.path.isfile(MONITOR):
                # At boot/logon WTS may expose the console session before the
                # user token is ready. Retry on the next loop instead of
                # treating the first launch failure as a permanent failure.
                if not process_exists_in_session(sid):
                    if launch_as_user(sid):
                        log(f'MONITOR_RECOVERY_REQUESTED session={sid}')
            if win32event.WaitForSingleObject(self.stop_event, 5000) == win32event.WAIT_OBJECT_0:
                break
        log('WATCHDOG_STOP')


if __name__ == '__main__':
    # Windows SCM launches a frozen PyInstaller service with no command-line
    # arguments.  Use the pywin32 dispatcher explicitly in that case;
    # HandleCommandLine alone can leave the SCM waiting and produce error 1053.
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PCYBIWatchdog)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PCYBIWatchdog)
