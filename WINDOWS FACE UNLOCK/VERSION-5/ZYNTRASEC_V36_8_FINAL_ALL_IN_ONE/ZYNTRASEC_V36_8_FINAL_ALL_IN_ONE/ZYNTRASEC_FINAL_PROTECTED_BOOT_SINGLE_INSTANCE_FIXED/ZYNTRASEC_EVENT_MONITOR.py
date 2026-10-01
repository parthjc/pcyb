import ctypes
from ctypes import wintypes
import os, subprocess, time, threading, xml.etree.ElementTree as ET

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
wtsapi32 = ctypes.windll.wtsapi32

WM_DESTROY = 0x0002
WM_POWERBROADCAST = 0x0218
WM_WTSSESSION_CHANGE = 0x02B1
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012
WTS_SESSION_UNLOCK = 0x0008
WTS_SESSION_LOGON = 0x0005
WTS_SESSION_LOCK = 0x0007
NOTIFY_FOR_THIS_SESSION = 0

root = os.path.join(os.environ.get('ProgramData', r'C:\ProgramData'), 'ZYNTRASEC', 'System')
app = os.path.join(root, 'ZYNTRASEC_LOCKSCREEN.exe')
log = os.path.join(root, 'event_monitor.log')
last_launch = 0.0
last_power_record = None

# Single-instance guard for the per-user monitor. The watchdog, logon task,
# and Run entry may all attempt to start it; only one instance is allowed.
_monitor_mutex = kernel32.CreateMutexW(None, False, r'Global\ZYNTRASEC_EVENT_MONITOR_SINGLE_INSTANCE')
if kernel32.GetLastError() == 183:
    raise SystemExit(0)


def log_line(s):
    try:
        os.makedirs(root, exist_ok=True)
        with open(log, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + s + '\n')
    except Exception:
        pass


def relaunch(reason):
    global last_launch
    if not os.path.exists(app):
        log_line('APP_MISSING ' + reason)
        return
    now = time.monotonic()
    if now - last_launch < 8:
        log_line('DEBOUNCED ' + reason)
        return
    last_launch = now
    log_line('TRIGGER ' + reason)
    try:
        subprocess.run(['taskkill', '/IM', 'ZYNTRASEC_LOCKSCREEN.exe', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=5)
    except Exception:
        pass
    time.sleep(0.7)
    try:
        subprocess.Popen([app], cwd=root,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        log_line('LAUNCHED ' + reason)
    except Exception as e:
        log_line('LAUNCH_ERROR ' + repr(e))


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ('style', wintypes.UINT),
        ('lpfnWndProc', ctypes.c_void_p),
        ('cbClsExtra', ctypes.c_int),
        ('cbWndExtra', ctypes.c_int),
        ('hInstance', wintypes.HINSTANCE),
        ('hIcon', ctypes.c_void_p),
        ('hCursor', ctypes.c_void_p),
        ('hbrBackground', ctypes.c_void_p),
        ('lpszMenuName', wintypes.LPCWSTR),
        ('lpszClassName', wintypes.LPCWSTR),
    ]

WndProcType = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

@WndProcType
def wndproc(hwnd, msg, wparam, lparam):
    if msg == WM_POWERBROADCAST:
        if wparam == PBT_APMRESUMEAUTOMATIC:
            relaunch('POWER_RESUME_AUTOMATIC')
        elif wparam == PBT_APMRESUMESUSPEND:
            relaunch('POWER_RESUME_SUSPEND')
        return 1
    if msg == WM_WTSSESSION_CHANGE:
        if wparam == WTS_SESSION_UNLOCK:
            log_line('SESSION_UNLOCK_DETECTED')
            relaunch('SESSION_UNLOCK')
        elif wparam == WTS_SESSION_LOCK:
            log_line('SESSION_LOCK_DETECTED')
        elif wparam == WTS_SESSION_LOGON:
            relaunch('SESSION_LOGON')
        return 0
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def get_latest_power_event():
    """Fallback: read the newest Power-Troubleshooter Event ID 1 via wevtutil.
    This catches wake/resume even if WM_POWERBROADCAST is missed."""
    try:
        q = '*[System[(Provider[@Name="Microsoft-Windows-Power-Troubleshooter"]) and (EventID=1)]]'
        r = subprocess.run(['wevtutil', 'qe', 'System', '/q:' + q, '/c:1', '/rd:true', '/f:xml'],
                           capture_output=True, text=True, timeout=4,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if r.returncode != 0 or not r.stdout.strip():
            return None
        txt = r.stdout.strip()
        # wevtutil may return a single Event element or an Events wrapper.
        elem = ET.fromstring(txt)
        event = elem if elem.tag.endswith('Event') else next(iter(elem), None)
        if event is None:
            return None
        rid = None
        for node in event.iter():
            if node.tag.endswith('EventRecordID'):
                rid = node.text
                break
        return rid
    except Exception:
        return None


def event_log_watcher():
    global last_power_record
    # Prime with the current latest event so an old wake event doesn't relaunch.
    last_power_record = get_latest_power_event()
    log_line('POWER_EVENT_WATCHER_READY record=' + str(last_power_record))
    while True:
        time.sleep(2.0)
        rid = get_latest_power_event()
        if rid and rid != last_power_record:
            last_power_record = rid
            log_line('POWER_EVENT_ID1_DETECTED record=' + str(rid))
            relaunch('POWER_EVENTLOG_RESUME')


def main():
    os.makedirs(root, exist_ok=True)
    log_line('MONITOR_START')
    if not os.path.exists(app):
        log_line('LOCKSCREEN_NOT_FOUND_AT_START')

    hinst = kernel32.GetModuleHandleW(None)
    cls_name = 'ZYNTRASECEventMonitorWindow'
    wc = WNDCLASSW()
    wc.style = 0
    wc.lpfnWndProc = ctypes.cast(wndproc, ctypes.c_void_p)
    wc.hInstance = hinst
    wc.lpszClassName = cls_name
    atom = user32.RegisterClassW(ctypes.byref(wc))
    if not atom:
        log_line('REGISTER_CLASS_FAILED')
        return 2

    hwnd = user32.CreateWindowExW(0, cls_name, 'ZYNTRASEC Event Monitor', 0,
                                  0, 0, 0, 0, 0, 0, hinst, None)
    if not hwnd:
        log_line('CREATE_WINDOW_FAILED')
        return 3

    if not wtsapi32.WTSRegisterSessionNotification(hwnd, NOTIFY_FOR_THIS_SESSION):
        log_line('WTS_REGISTER_FAILED')
    else:
        log_line('WTS_SESSION_NOTIFICATION_READY')
    log_line('POWER_BROADCAST_READY')

    # IMPORTANT: after a reboot/logon the service may create this monitor after
    # the WTS_SESSION_LOGON event has already occurred.  Therefore the monitor
    # must authenticate immediately on its own startup instead of waiting only
    # for a later event.
    log_line('MONITOR_READY_LOCKSCREEN_AUTOSTART')
    threading.Thread(target=lambda: (time.sleep(1.0), relaunch('MONITOR_STARTUP')), daemon=True).start()
    threading.Thread(target=event_log_watcher, daemon=True).start()

    msg = wintypes.MSG()
    while True:
        r = user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
        if r <= 0:
            break
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

    try:
        wtsapi32.WTSUnRegisterSessionNotification(hwnd)
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
