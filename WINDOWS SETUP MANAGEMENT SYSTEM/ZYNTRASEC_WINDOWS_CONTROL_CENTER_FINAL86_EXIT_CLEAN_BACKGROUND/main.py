import re

import os, sys, ctypes, subprocess, platform, shutil, tempfile, json, time, threading, hashlib
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import math
APP="ZYNTRASEC // WINDOWS CONTROL CENTER"
BG="#040705"; PANEL="#08130c"; GREEN="#00ff66"; TEXT="#baffd0"; MUTED="#63a877"
WARN="#ffd166"; RED="#ff5577"; CYAN="#4de8ff"





class CyberScrollbar(tk.Canvas):
    """Small native Tk cyber scrollbar used instead of platform-themed ttk scrollbars."""
    def __init__(self, master, orient="vertical", command=None, **kwargs):
        self.orient=orient
        self.command=command
        self._first=0.0; self._last=1.0
        self._drag_offset=0.0
        width=14 if orient=="vertical" else None
        height=14 if orient=="horizontal" else None
        super().__init__(master, bg="#010604", highlightthickness=1,
                         highlightbackground="#0b6b36", highlightcolor="#00ff66",
                         borderwidth=0, width=width, height=height,
                         cursor="sb_v_double_arrow" if orient=="vertical" else "sb_h_double_arrow", **kwargs)
        self._thumb=self.create_rectangle(0,0,0,0,fill="#0b8f45",outline="#00ff66",width=1)
        self._track=self.create_rectangle(0,0,0,0,fill="#010604",outline="")
        self.tag_raise(self._thumb)
        self.bind("<Configure>", lambda e:self._redraw())
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<MouseWheel>", self._wheel)
        self.bind("<Button-4>", lambda e:self._scroll(-3))
        self.bind("<Button-5>", lambda e:self._scroll(3))

    def set(self, first, last):
        try:self._first=float(first); self._last=float(last)
        except Exception:self._first=0.0; self._last=1.0
        self._redraw()

    def _redraw(self):
        try:
            w=max(1,self.winfo_width()); h=max(1,self.winfo_height())
            if self.orient=="vertical":
                track=max(1,h-2); a=max(0,min(1,self._first)); b=max(a,min(1,self._last))
                thumb=max(28,track*(b-a)); y=1+(track-thumb)*a
                self.coords(self._track,1,1,w-1,h-1)
                self.coords(self._thumb,2,y,w-2,y+thumb)
            else:
                track=max(1,w-2); a=max(0,min(1,self._first)); b=max(a,min(1,self._last))
                thumb=max(28,track*(b-a)); x=1+(track-thumb)*a
                self.coords(self._track,1,1,w-1,h-1)
                self.coords(self._thumb,x,2,x+thumb,h-2)
        except Exception: pass

    def _fraction(self, x, y):
        w=max(1,self.winfo_width()); h=max(1,self.winfo_height())
        if self.orient=="vertical":
            track=max(1,h-2); thumb=max(28,track*(self._last-self._first));
            return max(0,min(1,(y-1-self._drag_offset)/(track-thumb))) if track>thumb else 0
        track=max(1,w-2); thumb=max(28,track*(self._last-self._first));
        return max(0,min(1,(x-1-self._drag_offset)/(track-thumb))) if track>thumb else 0

    def _press(self,event):
        try:
            x,y=event.x,event.y
            bb=self.bbox(self._thumb)
            if bb and bb[0]<=x<=bb[2] and bb[1]<=y<=bb[3]:
                self._drag_offset=(y-bb[1]) if self.orient=="vertical" else (x-bb[0])
            else:
                f=self._fraction(x,y)
                if self.command:self.command("moveto", f)
        except Exception: pass

    def _drag(self,event):
        try:
            f=self._fraction(event.x,event.y)
            if self.command:self.command("moveto", f)
        except Exception: pass

    def _release(self,event):
        self._drag_offset=0.0

    def _wheel(self,event):
        try:
            step=-3 if event.delta>0 else 3
            self._scroll(step)
        except Exception: pass

    def _scroll(self,step):
        try:
            if self.command:self.command("scroll",step,"units")
        except Exception: pass


class ButtonTooltip:
    """Small bilingual Gujarati + English hover help for every button."""
    def __init__(self, widget, text):
        self.widget=widget
        self.text=text
        self.tip=None
        self.after_id=None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<ButtonPress>", self._leave, add="+")

    def _enter(self, event=None):
        self._cancel()
        try:
            self.after_id=self.widget.after(450, self._show)
        except Exception:
            pass

    def _leave(self, event=None):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self.after_id:
            try:self.widget.after_cancel(self.after_id)
            except Exception:pass
            self.after_id=None

    def _show(self):
        self.after_id=None
        if self.tip or not self.widget.winfo_exists(): return
        try:
            self.tip=tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.attributes("-topmost", True)
            self.tip.configure(bg="#07150c")
            frame=tk.Frame(self.tip,bg="#07150c",highlightbackground="#00ff66",highlightthickness=1)
            frame.pack()
            tk.Label(frame,text=self.text,bg="#07150c",fg="#baffd0",justify="left",
                     anchor="w",wraplength=520,font=("Consolas",9),padx=11,pady=9).pack()
            self.tip.update_idletasks()
            x=self.widget.winfo_rootx()+12
            y=self.widget.winfo_rooty()+self.widget.winfo_height()+6
            sw=self.widget.winfo_screenwidth(); sh=self.widget.winfo_screenheight()
            tw=self.tip.winfo_width(); th=self.tip.winfo_height()
            if x+tw>sw-8: x=max(8,sw-tw-8)
            if y+th>sh-8: y=self.widget.winfo_rooty()-th-6
            if y<8: y=8
            self.tip.geometry(f"+{x}+{y}")
        except Exception:
            self._hide()

    def _hide(self):
        if self.tip:
            try:self.tip.destroy()
            except Exception:pass
            self.tip=None

TOOLTIP_TEXT={'REFRESH': 'English: Re-scan the current data and refresh the screen.\nGujarati: હાલની માહિતી ફરી તપાસી ને screen refresh કરે છે.', 'OPEN STARTUP SETTINGS': 'English: Opens Windows Startup Apps settings.\nGujarati: Windows ની Startup Apps settings ખોલે છે.', 'SCAN DRIVERS': 'English: Lists installed drivers and their versions.\nGujarati: PC ના installed drivers અને તેમની versions બતાવે છે.', 'AUTO UPDATE DRIVERS': 'English: Checks Microsoft-supported Windows Update sources for applicable driver updates.\nGujarati: Microsoft-supported Windows Update sourcesમાંથી available driver updates તપાસે છે.\nIf none are available: nothing is installed.', 'OPEN DEVICE MANAGER': 'English: Opens Device Manager to inspect hardware and driver status.\nGujarati: hardware અને driver status જોવા Device Manager ખોલે છે.', 'OPEN WINDOWS UPDATE': 'English: Opens Windows Update settings.\nGujarati: Windows Update settings ખોલે છે.', 'OPEN OPTIONAL FEATURES': 'English: Opens Windows Optional Features to review optional components.\nGujarati: Windows Optional Features ખોલે છે જેથી optional components review કરી શકો.', 'OPEN WINDOWS FEATURES': 'English: Opens Windows Features settings.\nGujarati: Windows Features settings ખોલે છે.', 'OPEN INSTALLED APPS': 'English: Opens Windows Installed Apps settings.\nGujarati: Windows Installed Apps settings ખોલે છે.', 'CREATE CONFIG BACKUP': 'English: Saves ZYNTRASEC configuration before major changes.\nGujarati: મોટા ફેરફાર પહેલાં ZYNTRASEC configuration નો backup બનાવે છે.', 'VERIFY LAST BACKUP': 'English: Checks whether the latest backup exists and can be read.\nGujarati: છેલ્લો backup હાજર અને વાંચી શકાય છે કે નહીં તે તપાસે છે.', 'BACKUP HISTORY': 'English: Shows previous ZYNTRASEC backups.\nGujarati: અગાઉના ZYNTRASEC backups બતાવે છે.', 'BACKUP REPORT': 'English: Shows a backup status report.\nGujarati: Backup નો status report બતાવે છે.', 'DETECT USB DRIVES': 'English: Detects connected USB/removable drives.\nGujarati: જોડાયેલા USB/removable drives શોધે છે.', 'CREATE RECOVERY USB': 'English: Starts the Windows Recovery USB workflow. Choose the correct USB carefully.\nGujarati: Windows Recovery USB બનાવવાની પ્રક્રિયા શરૂ કરે છે. સાચી USB ધ્યાનથી પસંદ કરો.\nWarning: The Windows creation process may erase/reformat the selected USB.', 'SAVE PC BASELINE': 'English: Saves a read-only snapshot of the current PC for later comparison.\nGujarati: પછી compare કરવા current PC નો read-only baseline save કરે છે.', 'COMPARE WITH BASELINE': 'English: Compares current PC information with the saved baseline and shows changes.\nGujarati: current PC ને saved baseline સાથે compare કરીને changes બતાવે છે.', 'GENERATE REPORT': 'English: Creates a system/security report and saves a copy.\nGujarati: system/security report બનાવે અને copy save કરે છે.', 'IPCONFIG': 'English: Shows network adapters, IP addresses, gateway and related Windows network configuration.\nGujarati: network adapters, IP, gateway અને Windows network configuration બતાવે છે.', 'DNS CACHE': 'English: Shows the current DNS resolver cache. Useful for DNS troubleshooting.\nGujarati: હાલનું DNS cache બતાવે છે. DNS troubleshooting માટે ઉપયોગી છે.', 'OPEN NETWORK SETTINGS': 'English: Opens Windows network settings.\nGujarati: Windows Network settings ખોલે છે.', 'RUN SFC': 'English: Checks protected Windows system files with System File Checker.\nGujarati: protected Windows system files તપાસવા SFC ચલાવે છે.\nMay take time.', 'RUN DISM CHECK': 'English: Checks the Windows component store using DISM.\nGujarati: Windows component store તપાસવા DISM ચલાવે છે.\nMay take time and may need Administrator rights.', 'OPEN WINDOWS RECOVERY': 'English: Opens Windows recovery options for troubleshooting.\nGujarati: troubleshooting માટે Windows Recovery options ખોલે છે.', 'CLEAN USER TEMP': 'English: Cleans safe temporary files from the current user profile.\nGujarati: હાલના user profile ના safe temporary files clean કરે છે.', 'HIGH PERFORMANCE': 'English: Opens/applies the available High Performance power plan.\nGujarati: available High Performance power plan ખોલે/લાગુ કરે છે.\nMay use more power.', 'RESTART EXPLORER': 'English: Restarts Windows Explorer to refresh desktop/taskbar.\nGujarati: desktop/taskbar refresh કરવા Windows Explorer restart કરે છે.', 'OPEN ABOUT': 'English: Opens Windows About/System information.\nGujarati: Windows About/System information ખોલે છે.', 'OPEN ACTIVATION': 'English: Opens official Windows Activation settings.\nGujarati: official Windows Activation settings ખોલે છે.', 'ONE-CLICK COMPLETE CHECK': 'English: Runs the available read-only setup checks together.\nGujarati: ઉપલબ્ધ read-only setup checks એક સાથે ચલાવે છે.', 'PRE-SETUP BACKUP + RESTORE POINT': 'English: Creates a ZYNTRASEC configuration backup plus a Windows restore point before setup changes.\nGujarati: setup changes પહેલાં ZYNTRASEC backup અને Windows restore point બનાવે છે.', 'APPLY SAFE BASELINE': "English: Applies the project's documented safe baseline settings.\nGujarati: Project ની documented safe baseline settings લાગુ કરે છે.", 'OPEN': 'English: Opens the selected Windows page/module.\nGujarati: પસંદ કરેલી Windows page/module ખોલે છે.', 'EXIT': 'English: Closes ZYNTRASEC Windows Control Center.\nGujarati: ZYNTRASEC Windows Control Center બંધ કરે છે.', 'REFRESH STARTUP': 'English: Re-scan Windows startup entries and refresh the table. No startup item is changed.\nGujarati: Windows startup entries ફરી scan કરીને table refresh કરે છે. કોઈ startup item બદલાતું નથી.', 'OPEN LOCATION': 'English: Opens the file/folder location for the selected startup entry when a valid path is available.\nGujarati: selected startup entry નું valid file/folder location હોય તો ખોલે છે.', 'DISABLE': 'English: Stops the selected user-manageable startup entry from starting with Windows.\nGujarati: selected user-manageable startup entry ને Windows સાથે start થતી અટકાવે છે.\nWarning: Do not disable critical Windows entries.', 'ENABLE': 'English: Re-enables a previously disabled startup entry.\nGujarati: અગાઉ disabled કરેલી startup entry ફરી enable કરે છે.', 'REMOVE': 'English: Permanently removes the selected user-manageable startup entry after confirmation.\nGujarati: confirmation પછી selected user-manageable startup entry દૂર કરે છે.\nWarning: More permanent than Disable.', 'CREATE WINDOWS RESTORE POINT': 'English: Creates a Windows restore point before major system changes.\nGujarati: મોટા system changes પહેલાં Windows restore point બનાવે છે.\nNote: It is not a personal-file backup.', 'TRIM C:': 'English: Optimizes C: only when Windows reports SSD/flash storage that supports TRIM.\nGujarati: Windows C: ને SSD/flash storage તરીકે ઓળખે અને TRIM support હોય ત્યારે જ optimize કરે છે.\nHDD: Skip.', 'TRIM D:': 'English: Optimizes D: only when Windows reports SSD/flash storage that supports TRIM.\nGujarati: Windows D: ને SSD/flash storage તરીકે ઓળખે અને TRIM support હોય ત્યારે જ optimize કરે છે.\nHDD: Skip.', 'SCAN DISKS / PARTITIONS': 'English: Scans disks and partitions and refreshes the storage layout.\nGujarati: disks અને partitions scan કરીને storage layout refresh કરે છે.', 'OPEN DISK MANAGEMENT': 'English: Opens Windows Disk Management for detailed partition management.\nGujarati: detailed partition management માટે Windows Disk Management ખોલે છે.', 'AUTO PARTITION': 'English: Analyzes eligible unallocated space for the automatic partition workflow.\nGujarati: eligible unallocated space analyze કરીને automatic partition workflow ચલાવવા તૈયાર કરે છે.\nWarning: Partition changes can affect data.', 'AUTO EQUAL CREATE': 'English: Creates equal-size partitions from eligible unallocated space.\nGujarati: eligible unallocated spaceમાંથી equal-size partitions બનાવે છે.\nWarning: Partition changes can affect data.', 'CHOOSE FOLDER + ADD EXCLUSION': 'English: Adds only the selected trusted project folder to Microsoft Defender exclusions.\nGujarati: માત્ર selected trusted project folder માટે Microsoft Defender exclusion ઉમેરે છે.\nWarning: Protection is reduced for that folder.', 'REMOVE EXCLUSION': 'English: Removes the selected project folder from the configured Defender exclusion.\nGujarati: selected project folder નું Defender exclusion દૂર કરે છે.', 'GENERATE COMPLETE REPORT': 'English: Collects available system/security information into one complete report.\nGujarati: available system/security information એક complete report માં ભેગી કરે છે.', 'OPEN REPORT FOLDER': 'English: Opens the folder containing generated ZYNTRASEC reports.\nGujarati: generated ZYNTRASEC reports વાળો folder ખોલે છે.', 'REFRESH SECURITY STATUS': 'English: Re-checks Defender, Firewall and related Windows security status.\nGujarati: Defender, Firewall અને related Windows security status ફરી check કરે છે.', 'AUTO CHECK + OPEN WINDOWS SECURITY': 'English: Checks available security status and opens Windows Security for details.\nGujarati: security status check કરીને details માટે Windows Security ખોલે છે.', 'OPEN SYSTEM RESTORE': 'English: Opens Windows System Restore.\nGujarati: Windows System Restore ખોલે છે.', 'VIEW RESTORE POINTS': 'English: Shows available Windows restore points.\nGujarati: available Windows restore points બતાવે છે.', 'OPEN ZYNTRASEC DATA': 'English: Opens ZYNTRASEC local data/backups/logs folder.\nGujarati: ZYNTRASEC ના local data/backups/logs વાળો folder ખોલે છે.', 'LIVE SYSTEM MONITOR': 'English: Shows current system resource information.\nGujarati: current system resource information બતાવે છે.', 'RUN FULL SCAN': 'English: Runs the module’s full available diagnostic scan and reports results.\nGujarati: module નો full available diagnostic scan ચલાવીને result બતાવે છે.', 'SEARCH': 'English: Searches the current list using your entered text.\nGujarati: તમે લખેલા text પ્રમાણે current list search કરે છે.', 'BROWSE': 'English: Opens a picker to choose a file or folder.\nGujarati: file અથવા folder પસંદ કરવા picker ખોલે છે.', 'CHECK': 'English: Checks the selected target without applying a change.\nGujarati: selected target check કરે છે; change apply કરતું નથી.', 'CHECK USER ACCESS': 'English: Checks whether the selected Windows user has access to the target folder.\nGujarati: selected Windows user ને target folder પર access છે કે નહીં તે check કરે છે.', 'DRY RUN': 'English: Simulates the planned change without applying it.\nGujarati: planned change simulate કરે છે, actual change apply કરતું નથી.', 'BACKUP BEFORE CHANGES': 'English: Saves the current state before a policy/permission change.\nGujarati: policy/permission change પહેલાં current state નો backup બનાવે છે.', 'APPLY': 'English: Applies the reviewed change to the selected target.\nGujarati: review કરેલો change selected target પર apply કરે છે.', 'VERIFY': 'English: Checks the target again after a change to confirm the final state.\nGujarati: change પછી target ફરી check કરીને final state verify કરે છે.', 'RESTORE LAST SAFE STATE': 'English: Restores the last saved ZYNTRASEC safe policy state when available.\nGujarati: available હોય ત્યારે છેલ્લી saved ZYNTRASEC safe policy state restore કરે છે.'}
def tooltip_for_button_text(text):
    clean=" ".join(str(text).replace("🆕 ","").replace("🛠 ","").replace("🔐 ","").replace("💾 ","").replace("▤ ","").replace("👤 ","").replace("▣ ","").strip().split())
    if clean in TOOLTIP_TEXT: return TOOLTIP_TEXT[clean]
    # Match labels that contain a known action, e.g. icons or extended labels.
    for key,val in TOOLTIP_TEXT.items():
        if key in clean.upper(): return val
    return f"English: Opens or runs '{clean}' and shows the result in the ZYNTRASEC console when applicable.\nGujarati: '{clean}' ખોલે અથવા ચલાવે છે અને જરૂરી હોય ત્યારે result ZYNTRASEC console માં બતાવે છે."

def is_admin():
    try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except: return False

def _hidden_process_kwargs():
    """Hide helper console windows while ZYNTRASEC GUI remains visible."""
    if os.name != "nt":
        return {}
    kwargs={"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    try:
        si=subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs["startupinfo"] = si
    except Exception:
        pass
    return kwargs

# Processes started by ZYNTRASEC are tracked so EXIT can clean up only
# ZYNTRASEC-owned helper processes. Windows services are never stopped.
_ACTIVE_PROCS=set()
_ACTIVE_PROCS_LOCK=threading.Lock()

def _track_process(p):
    with _ACTIVE_PROCS_LOCK:
        _ACTIVE_PROCS.add(p)

def _untrack_process(p):
    with _ACTIVE_PROCS_LOCK:
        _ACTIVE_PROCS.discard(p)

def _stop_owned_processes():
    """Stop only helper processes currently launched by this app.
    Do NOT stop Windows services or unrelated user processes.
    """
    with _ACTIVE_PROCS_LOCK:
        procs=list(_ACTIVE_PROCS)
    if os.name != "nt":
        for p in procs:
            try:p.terminate()
            except Exception:pass
        return
    for p in procs:
        try:
            if p.poll() is None:
                # /T also closes children created by this exact helper.
                subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],
                               capture_output=True,text=True,timeout=8,**_hidden_process_kwargs())
        except Exception:
            try:p.terminate()
            except Exception:pass
    with _ACTIVE_PROCS_LOCK:
        _ACTIVE_PROCS.clear()

def _run_tracked(args, *, shell=False, timeout=180):
    p=None
    try:
        p=subprocess.Popen(args,shell=shell,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           text=True,**_hidden_process_kwargs())
        _track_process(p)
        try:
            out,err=p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                if os.name=="nt":
                    subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],
                                   capture_output=True,text=True,timeout=8,**_hidden_process_kwargs())
                else:p.terminate()
            except Exception:pass
            out,err=p.communicate()
            return 1,(out or "")+(err or "")+"\n[TIMEOUT]"
        return p.returncode,(out or "")+(err or "")
    except Exception as e:
        return 1,str(e)
    finally:
        if p is not None:_untrack_process(p)

def run(cmd, timeout=180):
    return _run_tracked(cmd,shell=True,timeout=timeout)

def ps(script,timeout=180):
    # Execute PowerShell directly so nested quotes are not corrupted by cmd.exe.
    return _run_tracked(
        ["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-Command",script],
        shell=False,timeout=timeout
    )

def human(n):
    for u in ("B","KB","MB","GB","TB"):
        if n<1024 or u=="TB":return f"{n:.1f} {u}"
        n/=1024


def discover_local_users():
    """Fast local-user discovery using one PowerShell query."""
    import csv, io
    users=[]
    try:
        script = '$admins=@(Get-LocalGroupMember -Group "Administrators" -ErrorAction SilentlyContinue | ForEach-Object { $_.Name.ToLower() }); Get-CimInstance Win32_UserAccount -Filter "LocalAccount=True" | ForEach-Object { $name=$_.Name; $full=$_.Domain+"\\"+$name; [pscustomobject]@{Name=$name;SID=$_.SID;Disabled=[bool]$_.Disabled;Admin=($admins -contains $full.ToLower() -or $admins -contains $name.ToLower())} } | ConvertTo-Csv -NoTypeInformation'
        out=subprocess.check_output(["powershell.exe","-NoProfile","-Command",script],text=True,stderr=subprocess.DEVNULL,timeout=12,**_hidden_process_kwargs())
        for row in csv.DictReader(io.StringIO(out)):
            name=(row.get('Name') or '').strip(); sid=(row.get('SID') or '').strip()
            if not name or not sid: continue
            users.append({'name':name,'sid':sid,'admin':str(row.get('Admin','False')).lower()=='true','disabled':str(row.get('Disabled','False')).lower()=='true'})
    except Exception:
        pass
    return users

def user_inventory_text():
    users = discover_local_users()
    lines = [f"LOCAL WINDOWS USERS: {len(users)}", ""]
    for u in users:
        role = "ADMINISTRATOR" if u["admin"] else "STANDARD USER"
        state = "DISABLED" if u["disabled"] else "ENABLED"
        lines.append(f'{u["name"]} | {role} | {state} | {u["sid"]}')
    return "\n".join(lines)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP); self.geometry("1360x820"); self.minsize(900,620); self.configure(bg=BG)
        self.option_add("*Font",("Consolas",10))
        self._output_settings_path=Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))/"ZYNTRASEC"/"output_console_settings.json"
        self._output_font_size=10
        self._output_auto_scroll=True
        self._output_saved_height=145
        self._closing=False
        self._load_output_settings()
        self.style(); self.build()
        self._tooltip_refs=[]
        self.after_idle(self._bind_all_tooltips)
        self.recovery_root=Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))/"ZYNTRASEC"/"Recovery"
        self.recovery_root.mkdir(parents=True,exist_ok=True)
        self.recovery_file=self.recovery_root/"LAST_POLICY_SAFE_STATE.json"
        self.data_root=Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))/"ZYNTRASEC"
        self.backup_root=self.data_root/"Backup"
        self.log_root=self.data_root/"Logs"
        for _p in (self.backup_root,self.log_root): _p.mkdir(parents=True,exist_ok=True)
        self.custom_apps_file=self.data_root/"custom_apps.json"
        self.policy_apps_file=self.data_root/"policy_custom_apps.json"
        self.custom_apps=self._load_custom_apps()
        self.policy_custom_apps=self._load_policy_apps()
        # Legacy cleanup: previous builds pinned PowerShell/PowerShell ISE into
        # the Policy Apps list. They must appear only after explicit ADD APP.
        legacy_names={"powershell", "powershell_ise", "powershell ise"}
        cleaned=[]
        for item in self.policy_custom_apps:
            name=str(item.get("name", "")).strip().lower()
            exe=str(item.get("exe", "")).strip().lower().replace("/", "\\")
            if name in legacy_names or exe.endswith("\\windowspowershell\\v1.0\\powershell.exe") or exe.endswith("\\windowspowershell\\v1.0\\powershell_ise.exe"):
                continue
            cleaned.append(item)
        if len(cleaned) != len(self.policy_custom_apps):
            self.policy_custom_apps=cleaned
            self._save_policy_apps()
        self.protocol("WM_DELETE_WINDOW", self._safe_close)
        self.home()

    def _style_cyber_combobox_popup(self, event=None):
        """Apply ZYNTRASEC cyber colors to every ttk Combobox popup/list.
        Tk/ttk styles do not fully theme the native popdown list, so style it
        after the popup is posted as well.
        """
        try:
            widget = event.widget if event is not None else None
            if widget is None or str(widget.winfo_class()) != "TCombobox":
                return
            def apply():
                try:
                    pop = self.tk.call("ttk::combobox::PopdownWindow", widget._w)
                    # Standard ttk combobox popdown structure: .f.l + .f.sb
                    for name in (pop + ".f.l", pop + ".f.sb"):
                        try:
                            self.tk.call(name, "configure",
                                "-background", "#06100a",
                                "-foreground", GREEN,
                                "-selectbackground", "#18a957",
                                "-selectforeground", "#000000",
                                "-highlightbackground", "#18a957",
                                "-highlightcolor", GREEN,
                                "-borderwidth", 1,
                                "-relief", "flat")
                        except Exception:
                            pass
                    # Popdown frame itself
                    try:
                        self.tk.call(pop, "configure", "-background", "#06100a", "-borderwidth", 1, "-relief", "solid")
                    except Exception:
                        pass
                except Exception:
                    pass
            self.after(35, apply)
        except Exception:
            pass

    def style(self):
        s=ttk.Style(self); s.theme_use("clam")
        s.configure("TButton",background="#0b2114",foreground=GREEN,bordercolor="#146b38",
                    lightcolor="#146b38",darkcolor="#146b38",padding=9,font=("Consolas",10,"bold"))
        s.map("TButton",background=[("active","#123c21")],foreground=[("active","white")])
        s.configure("Nav.TButton",background="#06130b",foreground=GREEN,bordercolor="#0b6b36",
                    lightcolor="#0b6b36",darkcolor="#0b6b36",padding=(8,7),font=("Consolas",9,"bold"))
        s.map("Nav.TButton",background=[("active","#0d3b20"),("pressed","#082613")],
              foreground=[("active","#ffffff"),("pressed",GREEN)])
        # Unified cyber-terminal scrollbar theme: no default white Windows rails.
        s.configure("Cyber.Vertical.TScrollbar",background="#0b2a17",troughcolor="#010604",
                    bordercolor="#0b6b36",arrowcolor=GREEN,gripcount=0,arrowsize=12)
        s.configure("Cyber.Horizontal.TScrollbar",background="#0b2a17",troughcolor="#010604",
                    bordercolor="#0b6b36",arrowcolor=GREEN,gripcount=0,arrowsize=12)
        s.map("Cyber.Vertical.TScrollbar",background=[("active","#18a957"),("pressed","#0f7d3f")])
        s.map("Cyber.Horizontal.TScrollbar",background=[("active","#18a957"),("pressed","#0f7d3f")])
        s.configure("Nav.Vertical.TScrollbar",background="#0b2a17",troughcolor="#010604",
                    bordercolor="#0b6b36",arrowcolor=GREEN,gripcount=0,arrowsize=12)
        s.map("Nav.Vertical.TScrollbar",background=[("active","#18a957"),("pressed","#0f7d3f")])
        s.configure("Treeview",background="#06100a",foreground=TEXT,fieldbackground="#06100a",
                    rowheight=26)
        s.configure("Treeview.Heading",background="#102719",foreground=GREEN,
                    font=("Consolas",10,"bold"))
        s.configure("Partition.TCombobox",fieldbackground="#06100a",background="#06100a",
                    foreground=GREEN,arrowcolor=GREEN,bordercolor="#18a957",
                    lightcolor="#18a957",darkcolor="#0b6b36",padding=2)
        s.map("Partition.TCombobox",fieldbackground=[("readonly","#06100a"),("active","#0b2114")],
              foreground=[("readonly",GREEN),("active",GREEN)],
              background=[("readonly","#06100a"),("active","#0b2114")],
              arrowcolor=[("readonly",GREEN),("active","#39ff88")])
        # Theme every dropdown popup, not only the closed combobox field.
        self.bind_class("TCombobox", "<ButtonPress-1>", self._style_cyber_combobox_popup, add="+")

    def _async_job(self, work, done=None, label="WORKING..."):
        if getattr(self, "_closing", False):
            return
        if getattr(self, "_job_running", False):
            messagebox.showinfo("ZYNTRASEC", "Another operation is still running. Please wait.")
            return
        self._job_running=True
        try:self.badge.config(text="● "+label,fg=WARN)
        except Exception:pass
        def worker():
            try:
                result=work()
                if not getattr(self, "_closing", False):
                    self.after(0, lambda r=result: self._async_done(done,r))
            except Exception as e:
                if not getattr(self, "_closing", False):
                    self.after(0, lambda e=e: self._async_done(None,e))
        threading.Thread(target=worker,daemon=True).start()

    def _async_done(self, done, result):
        self._job_running=False
        try:self.badge.config(text="● ADMINISTRATOR" if is_admin() else "● ADMIN REQUIRED",fg=GREEN if is_admin() else WARN)
        except Exception:pass
        if done:
            try: done(result)
            except Exception as e: messagebox.showerror("ZYNTRASEC",str(e))
        elif isinstance(result,Exception):
            messagebox.showerror("ZYNTRASEC",str(result))

    def build(self):
        self.head=tk.Frame(self,bg=BG,height=66); self.head.pack(fill="x")
        self.title_label=tk.Label(self.head,text="ZYNTRASEC",bg=BG,fg=GREEN,font=("Consolas",25,"bold"))
        self.title_label.pack(side="left",padx=20,pady=11)
        self.subtitle_label=tk.Label(self.head,text="// WINDOWS CONTROL CENTER",bg=BG,fg=TEXT,font=("Consolas",13,"bold"))
        self.subtitle_label.pack(side="left")
        self.badge=tk.Label(self.head,text="",bg=BG,fg=GREEN,font=("Consolas",10,"bold"));self.badge.pack(side="right",padx=18)

        body=tk.Frame(self,bg=BG);body.pack(fill="both",expand=True)

        # Hacker-style scrollable navigation: every setup module is reachable from the left rail.
        nav_host=tk.Frame(body,bg="#020b06",width=235,highlightbackground="#0b6b36",highlightthickness=1)
        nav_host.pack(side="left",fill="y");nav_host.pack_propagate(False)
        nav_top=tk.Frame(nav_host,bg="#020b06",height=42)
        nav_top.pack(side="top",fill="x");nav_top.pack_propagate(False)
        tk.Label(nav_top,text=">> ZYNTRASEC NAV // MODULES",bg="#020b06",fg=GREEN,
                 font=("Consolas",8,"bold"),anchor="w").pack(fill="x",padx=9,pady=(8,1))
        tk.Label(nav_top,text="[ SCROLL ENABLED ]",bg="#020b06",fg=MUTED,
                 font=("Consolas",7,"bold"),anchor="w").pack(fill="x",padx=9)
        nav_body=tk.Frame(nav_host,bg="#020b06");nav_body.pack(side="top",fill="both",expand=True)
        self.nav_canvas=tk.Canvas(nav_body,bg="#020b06",highlightthickness=0,borderwidth=0)
        self.nav_scroll=CyberScrollbar(nav_body,orient="vertical",command=self.nav_canvas.yview)
        self.nav_canvas.configure(yscrollcommand=self.nav_scroll.set)
        self.nav_canvas.pack(side="left",fill="both",expand=True)
        self.nav_scroll.pack(side="right",fill="y")
        self.nav=tk.Frame(self.nav_canvas,bg="#020b06")
        self._nav_window=self.nav_canvas.create_window((0,0),window=self.nav,anchor="nw")
        self.nav.bind("<Configure>",lambda e:self.nav_canvas.configure(scrollregion=self.nav_canvas.bbox("all")))
        self.nav_canvas.bind("<Configure>",self._resize_nav)
        self.nav_canvas.bind("<MouseWheel>",self._nav_wheel)
        self.nav.bind("<MouseWheel>",self._nav_wheel)
        self.nav_canvas.bind("<Button-4>",lambda e:self.nav_canvas.yview_scroll(-3,"units"))
        self.nav_canvas.bind("<Button-5>",lambda e:self.nav_canvas.yview_scroll(3,"units"))
        self.nav.bind("<Button-4>",lambda e:self.nav_canvas.yview_scroll(-3,"units"))
        self.nav.bind("<Button-5>",lambda e:self.nav_canvas.yview_scroll(3,"units"))

        # Main work area: scrollable module content + fixed output console.
        page_host=tk.Frame(body,bg=BG);page_host.pack(side="right",fill="both",expand=True,padx=8,pady=6)
        content_host=tk.Frame(page_host,bg=BG);content_host.pack(side="top",fill="both",expand=True)
        self.page_canvas=tk.Canvas(content_host,bg=BG,highlightthickness=0,borderwidth=0)
        self.page_scroll=CyberScrollbar(content_host,orient="vertical",command=self.page_canvas.yview)
        self.page_canvas.configure(yscrollcommand=self.page_scroll.set)
        self.page_canvas.pack(side="left",fill="both",expand=True)
        self.page_scroll.pack(side="right",fill="y")
        self.page=tk.Frame(self.page_canvas,bg=BG)
        self._page_window=self.page_canvas.create_window((0,0),window=self.page,anchor="nw")
        self.page.bind("<Configure>",lambda e:self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all")))
        self.page_canvas.bind("<Configure>",lambda e:self.page_canvas.itemconfigure(self._page_window,width=e.width))
        self.page_canvas.bind("<MouseWheel>",self._page_wheel)
        self.page.bind("<MouseWheel>",self._page_wheel)

        # One unified, compact output console for every module.
        self.output_host=tk.Frame(page_host,bg="#010201",highlightbackground="#146b38",highlightthickness=1)
        self.output_host.pack(side="bottom",fill="x",expand=False,padx=4,pady=(5,4))
        # Keep the unified console compact so module action buttons remain visible.
        # The console stays compact so the active module screen remains visible.
        self.output_host.configure(height=int(self._output_saved_height))
        self.output_host.pack_propagate(False)

        # Manual output-console splitter: drag the cyber handle up/down to resize
        # the console.  It lives in page_host so it is always directly under the console.
        self.output_splitter=tk.Frame(page_host,bg="#063d20",height=11,cursor="sb_v_double_arrow",
                                      highlightbackground="#18a957",highlightthickness=1)
        self.output_splitter.pack(side="bottom",fill="x",padx=4,pady=(0,0))
        self.output_splitter.pack_propagate(False)
        self.output_grip=tk.Label(self.output_splitter,text="═══  DRAG TO RESIZE  ═══   •   DOUBLE-CLICK = RESET",
                                  bg="#010604",fg=GREEN,font=("Consolas",8,"bold"),cursor="sb_v_double_arrow")
        self.output_grip.pack(fill="both",expand=True)
        for _w in (self.output_splitter,self.output_grip):
            _w.bind("<ButtonPress-1>",self._output_split_start)
            _w.bind("<B1-Motion>",self._output_split_drag)
            _w.bind("<Double-Button-1>",self._output_split_reset)

        self.output_title=tk.Label(self.output_host,text="OUTPUT // ZYNTRASEC CONSOLE",bg="#010201",fg=GREEN,font=("Consolas",10,"bold"),anchor="w")
        self.output_title.grid(row=0,column=0,sticky="ew",padx=(8,2),pady=(4,2))
        self.output_title.configure(cursor="sb_v_double_arrow")
        self.output_title.bind("<ButtonPress-1>",self._output_split_start)
        self.output_title.bind("<B1-Motion>",self._output_split_drag)
        self.output_title.bind("<Double-Button-1>",self._output_split_reset)
        self.output_toolbar=tk.Frame(self.output_host,bg="#010201")
        self.output_toolbar.grid(row=0,column=1,sticky="e",padx=(2,6),pady=(3,2))
        self._console_btn("−",self._output_font_down,"FONT −")
        self._console_btn("10",self._output_font_reset,"FONT RESET",name="font_size_btn")
        self._console_btn("+",self._output_font_up,"FONT +")
        self._console_btn("AUTO",self._toggle_output_autoscroll,"AUTO-SCROLL",name="auto_btn")
        self._console_btn("COPY",self._copy_output,"COPY OUTPUT")
        self._console_btn("SAVE",self._save_output,"SAVE OUTPUT")
        self._console_btn("FIND",self._find_output,"SEARCH OUTPUT")
        self._console_btn("CLEAR",lambda:self.output_clear("OUTPUT // ZYNTRASEC CONSOLE"),"CLEAR CONSOLE")
        self.log=tk.Text(self.output_host,bg="#010201",fg=GREEN,insertbackground=GREEN,font=("Consolas",self._output_font_size),relief="flat",wrap="none",undo=False)
        self.output_ybar=CyberScrollbar(self.output_host,orient="vertical",command=self.log.yview)
        self.output_xbar=CyberScrollbar(self.output_host,orient="horizontal",command=self.log.xview)
        self.log.configure(yscrollcommand=self.output_ybar.set,xscrollcommand=self.output_xbar.set)
        self.log.grid(row=1,column=0,sticky="nsew",padx=(6,0))
        self.output_ybar.grid(row=1,column=1,sticky="ns",padx=(0,6))
        self.output_xbar.grid(row=2,column=0,sticky="ew",padx=6,pady=(0,6))
        self.output_host.grid_rowconfigure(1,weight=1);self.output_host.grid_columnconfigure(0,weight=1)
        self.output_host.grid_columnconfigure(1,weight=0)
        self._update_console_toolbar()
        self._output_height_user_set=False
        self.log.insert("end","[BOOT] ZYNTRASEC ONLINE\n")
        self.bind("<Configure>",self._responsive_layout)
        self.bind_all("<MouseWheel>", self._global_wheel, add="+")
        self.bind_all("<Button-4>", self._global_wheel, add="+")
        self.bind_all("<Button-5>", self._global_wheel, add="+")
        self.navbar()

    def _bind_all_tooltips(self):
        """Attach bilingual hover help to every Tk/ttk button currently visible."""
        try:
            for ref in getattr(self,"_tooltip_refs",[]):
                try: ref.widget.unbind("<Enter>", ref._enter_id)
                except Exception: pass
            self._tooltip_refs=[]
            def walk(w):
                yield w
                for c in w.winfo_children():
                    yield from walk(c)
            for w in walk(self):
                try:
                    cls=w.winfo_class()
                    if cls not in ("Button","TButton"):
                        continue
                    text=w.cget("text")
                    if not text: continue
                    ref=ButtonTooltip(w,tooltip_for_button_text(text))
                    self._tooltip_refs.append(ref)
                except Exception:
                    pass
        except Exception:
            pass

    def _page_wheel(self,event):
        try:
            self.page_canvas.yview_scroll(int(-1*(event.delta/120)),"units")
        except Exception: pass

    def _resize_nav(self,event):
        try:self.nav_canvas.itemconfigure(self._nav_window,width=event.width)
        except Exception:pass

    def _global_wheel(self,event):
        try:
            x0=self.page_canvas.winfo_rootx(); y0=self.page_canvas.winfo_rooty()
            x1=x0+self.page_canvas.winfo_width(); y1=y0+self.page_canvas.winfo_height()
            if x0 <= event.x_root <= x1 and y0 <= event.y_root <= y1:
                step=int(-1*(event.delta/120)) if event.delta else 0
                if step==0: step=-1 if event.delta>0 else 1
                self.page_canvas.yview_scroll(step,"units")
                return "break"
            self._nav_wheel(event)
        except Exception: pass

    def _nav_wheel(self,event):
        try:
            # Scroll whenever the pointer is anywhere inside the left navigation rail,
            # including over buttons/labels.
            x0=self.nav_canvas.winfo_rootx(); y0=self.nav_canvas.winfo_rooty()
            x1=x0+self.nav_canvas.winfo_width(); y1=y0+self.nav_canvas.winfo_height()
            if x0 <= event.x_root <= x1 and y0 <= event.y_root <= y1:
                delta=event.delta
                step=int(-1*(delta/120)) if delta else 0
                if step==0: step=-1 if delta>0 else 1
                self.nav_canvas.yview_scroll(step,"units")
        except Exception:pass

    def _nav_wheel_global(self,event):
        self._nav_wheel(event)


    def _load_output_settings(self):
        try:
            if self._output_settings_path.exists():
                d=json.loads(self._output_settings_path.read_text(encoding="utf-8"))
                self._output_font_size=max(8,min(18,int(d.get("font_size",10))))
                self._output_auto_scroll=bool(d.get("auto_scroll",True))
                self._output_saved_height=max(95,min(520,int(d.get("height",145))))
        except Exception:
            pass

    def _save_output_settings(self):
        try:
            self._output_settings_path.parent.mkdir(parents=True,exist_ok=True)
            d={"font_size":int(self._output_font_size),"auto_scroll":bool(self._output_auto_scroll),
               "height":int(self.output_host.winfo_height()) if hasattr(self,"output_host") else int(self._output_saved_height)}
            self._output_settings_path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        except Exception:
            pass

    def _console_btn(self,text,command,tip,name=None):
        b=tk.Button(self.output_toolbar,text=text,command=command,bg="#06100a",fg=GREEN,
                    activebackground="#123c21",activeforeground=GREEN,relief="flat",
                    bd=1,highlightthickness=1,highlightbackground="#146b38",
                    font=("Consolas",8,"bold"),padx=5,pady=1,cursor="hand2")
        b.pack(side="left",padx=1)
        if name: setattr(self,name,b)
        return b

    def _update_console_toolbar(self):
        try:
            self.font_size_btn.config(text=str(self._output_font_size))
            self.auto_btn.config(text="AUTO ON" if self._output_auto_scroll else "AUTO OFF")
            self.log.config(font=("Consolas",self._output_font_size))
        except Exception:
            pass

    def _output_font_up(self):
        self._output_font_size=min(18,self._output_font_size+1); self._update_console_toolbar(); self._save_output_settings()

    def _output_font_down(self):
        self._output_font_size=max(8,self._output_font_size-1); self._update_console_toolbar(); self._save_output_settings()

    def _output_font_reset(self):
        self._output_font_size=10; self._update_console_toolbar(); self._save_output_settings()

    def _toggle_output_autoscroll(self):
        self._output_auto_scroll=not self._output_auto_scroll; self._update_console_toolbar(); self._save_output_settings()

    def _copy_output(self):
        try:
            data=self.log.get("1.0","end-1c")
            self.clipboard_clear(); self.clipboard_append(data); self.update()
            self.output_append("[✓] Console output copied to clipboard.")
        except Exception as e:
            self.output_append(f"[X] Copy failed: {e}")

    def _save_output(self):
        try:
            path=filedialog.asksaveasfilename(title="SAVE ZYNTRASEC CONSOLE OUTPUT",defaultextension=".txt",
                                              filetypes=[("Text files","*.txt"),("All files","*.*")],
                                              initialfile=f"ZYNTRASEC_CONSOLE_{datetime.now():%Y%m%d_%H%M%S}.txt")
            if not path:return
            Path(path).write_text(self.log.get("1.0","end-1c"),encoding="utf-8")
            self.output_append(f"[✓] Console saved: {path}")
        except Exception as e:
            self.output_append(f"[X] Save failed: {e}")

    def _find_output(self):
        win=tk.Toplevel(self); win.title("ZYNTRASEC // SEARCH OUTPUT"); win.configure(bg=BG); win.resizable(False,False)
        tk.Label(win,text="SEARCH CONSOLE OUTPUT",bg=BG,fg=GREEN,font=("Consolas",10,"bold")).pack(anchor="w",padx=12,pady=(10,4))
        entry=tk.Entry(win,bg="#06100a",fg=GREEN,insertbackground=GREEN,relief="flat",highlightthickness=1,highlightbackground="#146b38",width=42)
        entry.pack(padx=12,pady=4); entry.focus_set()
        def run_find():
            q=entry.get().strip()
            self.log.tag_remove("console_find","1.0","end")
            if not q:return
            start="1.0"; count=0
            while True:
                pos=self.log.search(q,start,stopindex="end",nocase=True)
                if not pos:break
                end=f"{pos}+{len(q)}c"; self.log.tag_add("console_find",pos,end); count+=1; start=end
            self.log.tag_config("console_find",background="#18a957",foreground="#000000")
            if count:
                self.log.see("console_find.first")
            self.output_append(f"[✓] Search: '{q}' -> {count} match(es)")
        tk.Button(win,text="SEARCH",command=run_find,bg="#06100a",fg=GREEN,activebackground="#123c21",activeforeground=GREEN,relief="flat",bd=1,highlightthickness=1,highlightbackground="#146b38",font=("Consolas",9,"bold")).pack(pady=(4,10))
        entry.bind("<Return>",lambda e:run_find())

    def _output_auto_see(self,index="end"):
        try:
            if self._output_auto_scroll:self.log.see(index)
        except Exception:pass

    def _resize_output(self,event=None):
        try:
            # Keep the user's manually selected height during window resize.
            # Only establish a default if no height has been selected yet.
            if not getattr(self, "_output_height_user_set", False):
                self.output_host.configure(height=145)
        except Exception:
            pass

    def _output_split_start(self,event):
        try:
            self._output_drag_y=event.y_root
            self._output_drag_height=int(self.output_host.winfo_height())
        except Exception:
            self._output_drag_y=event.y_root
            self._output_drag_height=145

    def _output_split_drag(self,event):
        try:
            delta=self._output_drag_y-event.y_root
            host_h=max(520,int(self.winfo_height()))
            min_h=95
            max_h=max(260,min(520,host_h-230))
            new_h=max(min_h,min(max_h,self._output_drag_height+delta))
            self.output_host.configure(height=int(new_h))
            self._output_height_user_set=True
            self._output_saved_height=int(new_h)
            self._save_output_settings()
        except Exception:
            pass

    def _output_split_reset(self,event=None):
        try:
            self.output_host.configure(height=145)
            self._output_height_user_set=False
            self._output_saved_height=145
            self._save_output_settings()
        except Exception:
            pass

    def _responsive_layout(self,event=None):
        try:
            w=max(900,self.winfo_width())
            nav_w=210 if w<1100 else 235
            # The host is the first child of body; resize it without changing page geometry.
            body=self.nav_canvas.master.master
            children=body.winfo_children()
            if children: children[0].configure(width=nav_w)
            self._resize_output()
            if w<1050:
                self.title_label.configure(font=("Consolas",20,"bold"),padx=12)
                self.subtitle_label.configure(font=("Consolas",10,"bold"))
            else:
                self.title_label.configure(font=("Consolas",25,"bold"),padx=20)
                self.subtitle_label.configure(font=("Consolas",13,"bold"))
        except Exception:pass

    def navbar(self):
        for w in self.nav.winfo_children():w.destroy()
        tk.Label(self.nav,text="// MODES",bg="#020b06",fg="#5aa979",font=("Consolas",8,"bold"),anchor="w").pack(fill="x",padx=9,pady=(8,3))
        mode_items=[
            (">> NEW WINDOWS SETUP",self.new_setup),
            (">> MANAGE EXISTING PC",self.manage),
        ]
        for txt,fn in mode_items:
            ttk.Button(self.nav,text=txt,command=fn,style="Nav.TButton").pack(fill="x",padx=7,pady=2)
        tk.Frame(self.nav,bg="#0b6b36",height=1).pack(fill="x",padx=7,pady=7)

        tk.Label(self.nav,text="// CORE",bg="#020b06",fg="#5aa979",font=("Consolas",8,"bold"),anchor="w").pack(fill="x",padx=9,pady=(1,3))
        core=[
            (">> USERS",self.users),(">> POLICIES",self.policies),(">> ACL / FOLDERS",self.acl),
            (">> BACKUP / ROLLBACK",self.backup),(">> REPORT",self.report),
        ]
        for txt,fn in core:
            ttk.Button(self.nav,text=txt,command=fn,style="Nav.TButton").pack(fill="x",padx=7,pady=2)
        tk.Frame(self.nav,bg="#0b6b36",height=1).pack(fill="x",padx=7,pady=7)

        tk.Label(self.nav,text="// SYSTEM MODULES",bg="#020b06",fg="#5aa979",font=("Consolas",8,"bold"),anchor="w").pack(fill="x",padx=9,pady=(1,3))
        modules=[
            ("01  WINDOWS",self.windows_setup_info),
            ("02  WINDOWS UPDATE",lambda:run("start ms-settings:windowsupdate")),
            ("03  DRIVERS",self.driver_center),
            ("04  SECURITY",self.security),
            ("05  STARTUP",self.startup),
            ("06  WINDOWS HEALTH",self.windows_health),
            ("07  STORAGE",self.storage),
            ("08  PARTITIONS",self.partition_manager),
            ("09  PERFORMANCE",self.performance_setup),
            ("10  NETWORK",self.network),
            ("11  WINDOWS COMPONENTS",self.windows_components),
            ("12  SOFTWARE",self.software_setup),
            ("13  HARDWARE",self.hardware_diagnostic),
            ("14  BACKUP & RECOVERY",self.backup_recovery_center),
            ("15  BASELINE",self.baseline_center),
            ("16  FINAL REPORT",self.report),
        ]
        for txt,fn in modules:
            ttk.Button(self.nav,text=">> "+txt,command=fn,style="Nav.TButton").pack(fill="x",padx=7,pady=2)

        tk.Frame(self.nav,bg="#0b6b36",height=1).pack(fill="x",padx=7,pady=7)
        tk.Label(self.nav,text="// SYSTEM",bg="#020b06",fg="#5aa979",font=("Consolas",8,"bold"),anchor="w").pack(fill="x",padx=9,pady=(1,3))
        ttk.Button(self.nav,text=">> EXIT CONTROL CENTER",command=self.destroy,style="Nav.TButton").pack(fill="x",padx=7,pady=(2,10))
        self.nav_canvas.yview_moveto(0)
        # Wheel over any sidebar child scrolls the navigation.
        self.bind_all("<MouseWheel>",self._nav_wheel_global,add="+")
        self.after_idle(self._bind_all_tooltips)

    def _load_custom_apps(self):
        try:
            if self.custom_apps_file.exists():
                data=json.loads(self.custom_apps_file.read_text(encoding="utf-8"))
                return data if isinstance(data,list) else []
        except Exception:
            pass
        return []

    def _save_custom_apps(self):
        tmp=self.custom_apps_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.custom_apps,indent=2),encoding="utf-8")
        os.replace(tmp,self.custom_apps_file)

    def _load_policy_apps(self):
        try:
            if self.policy_apps_file.exists():
                data=json.loads(self.policy_apps_file.read_text(encoding="utf-8"))
                return data if isinstance(data,list) else []
        except Exception:
            pass
        return []

    def _save_policy_apps(self):
        tmp=self.policy_apps_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.policy_custom_apps,indent=2),encoding="utf-8")
        os.replace(tmp,self.policy_apps_file)

    def _policy_app_is_pinned(self, exe):
        return any(os.path.normcase(x.get("exe",""))==os.path.normcase(exe) for x in self.policy_custom_apps)

    def _add_custom_to_policies(self, exe):
        exe=os.path.abspath(exe)
        if self._policy_app_is_pinned(exe):
            return
        name=Path(exe).stem
        self.policy_custom_apps.append({"name":name,"exe":exe})
        self._save_policy_apps()

    def _remove_policy_app(self, exe):
        self.policy_custom_apps=[x for x in self.policy_custom_apps if os.path.normcase(x.get("exe",""))!=os.path.normcase(exe)]
        self._save_policy_apps()

    def _custom_app_policy_state(self, username, exe):
        """Read the target user's DisallowRun application policy.
        Custom EXEs use the same user-hive policy mechanism as the built-in rows.
        """
        try:
            if not os.path.isfile(exe):
                return "MISSING"
            hive,loaded,orig_sid=self._user_hive(username)
            try:
                base=fr"HKU\{hive}\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
                key=base + r"\DisallowRun"
                q=subprocess.run(["reg.exe","query",key],capture_output=True,text=True,timeout=30)
                if q.returncode!=0:
                    return "ALLOWED"
                wanted=Path(exe).name.lower()
                for line in (q.stdout or "").splitlines():
                    parts=line.strip().split(None,2)
                    if len(parts)>=3 and parts[1].upper() in ("REG_SZ","REG_EXPAND_SZ") and parts[2].strip().lower()==wanted:
                        # DisallowRun values are active only when the Explorer flag is enabled.
                        flag=subprocess.run(["reg.exe","query",base,"/v","DisallowRun"],capture_output=True,text=True,timeout=30)
                        if flag.returncode==0 and "REG_DWORD" in (flag.stdout or "") and "0x1" in (flag.stdout or "").lower():
                            return "BLOCKED"
                        return "ALLOWED"
                return "ALLOWED"
            finally:
                self._close_user_hive(hive,loaded,orig_sid)
        except Exception:
            return "CHECK ERROR"

    def _custom_app_policy_change(self, username, exe, block):
        """Apply/remove a per-user DisallowRun policy for one EXE.
        Uses the same target-user registry hive and the same confirmation/verification
        workflow as the four built-in Policies rows. No NTFS ACL changes are made.
        """
        if not is_admin():
            raise RuntimeError("Run ZYNTRASEC as Administrator to change application access.")
        if not os.path.isfile(exe):
            raise RuntimeError("Selected executable does not exist.")
        action="BLOCK" if block else "ALLOW"
        before=self._custom_app_policy_state(username,exe)
        before_effective=before if before in ("BLOCKED","ALLOWED") else "ALLOWED"
        detail=(f"\\n\\nBefore: USER={before_effective} | MACHINE=NOT SET | EFFECTIVE={before_effective}"
                f"\\n\\nThis action changes ONLY the selected user's policy hive.\
Machine policy is read-only.")
        if not self._admin_target_warning(username, f"{action} application"):
            return False
        if not messagebox.askyesno("Confirm policy change",
            f"{action}\\n\\nUser: {username}\\nPolicy: {Path(exe).stem}" + detail):
            return False

        self.make_backup()
        hive,loaded,orig_sid=self._user_hive(username)
        try:
            base=fr"HKU\{hive}\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            key=base + r"\DisallowRun"
            wanted=Path(exe).name

            # Read existing entries.
            q=subprocess.run(["reg.exe","query",key],capture_output=True,text=True,timeout=30)
            entries=[]
            if q.returncode==0:
                for line in (q.stdout or "").splitlines():
                    parts=line.strip().split(None,2)
                    if len(parts)>=3 and parts[1].upper() in ("REG_SZ","REG_EXPAND_SZ"):
                        entries.append((parts[0],parts[2].strip()))

            matching=[n for n,v in entries if v.lower()==wanted.lower()]
            if block:
                # Enable the Windows DisallowRun policy flag.
                p=subprocess.run(["reg.exe","add",base,"/v","DisallowRun","/t","REG_DWORD","/d","1","/f"],capture_output=True,text=True,timeout=30)
                if p.returncode!=0:
                    raise RuntimeError((p.stdout or p.stderr or "Failed to enable DisallowRun policy.").strip())
                if not matching:
                    numeric=[]
                    for n,v in entries:
                        try: numeric.append(int(n))
                        except ValueError: pass
                    value_name=str(max(numeric,default=0)+1)
                    p=subprocess.run(["reg.exe","add",key,"/v",value_name,"/t","REG_SZ","/d",wanted,"/f"],capture_output=True,text=True,timeout=30)
                    if p.returncode!=0:
                        raise RuntimeError((p.stdout or p.stderr or "Failed to add application policy.").strip())
            else:
                for value_name in matching:
                    p=subprocess.run(["reg.exe","delete",key,"/v",value_name,"/f"],capture_output=True,text=True,timeout=30)
                    if p.returncode!=0:
                        raise RuntimeError((p.stdout or p.stderr or "Failed to remove application policy.").strip())
                # Only turn the flag off when this policy has no remaining entries.
                q2=subprocess.run(["reg.exe","query",key],capture_output=True,text=True,timeout=30)
                remaining=[]
                if q2.returncode==0:
                    for line in (q2.stdout or "").splitlines():
                        parts=line.strip().split(None,2)
                        if len(parts)>=3 and parts[1].upper() in ("REG_SZ","REG_EXPAND_SZ"):
                            remaining.append(parts)
                if not remaining:
                    subprocess.run(["reg.exe","delete",base,"/v","DisallowRun","/f"],capture_output=True,text=True,timeout=30)

            # Verify using the same target hive before unloading it.
            flag=subprocess.run(["reg.exe","query",base,"/v","DisallowRun"],capture_output=True,text=True,timeout=30)
            verify=subprocess.run(["reg.exe","query",key],capture_output=True,text=True,timeout=30)
            active_flag=(flag.returncode==0 and "REG_DWORD" in (flag.stdout or "") and "0x1" in (flag.stdout or "").lower())
            found=False
            if verify.returncode==0:
                for line in (verify.stdout or "").splitlines():
                    parts=line.strip().split(None,2)
                    if len(parts)>=3 and parts[1].upper() in ("REG_SZ","REG_EXPAND_SZ") and parts[2].strip().lower()==wanted.lower():
                        found=True; break
            state="BLOCKED" if (active_flag and found) else "ALLOWED"
            expected="BLOCKED" if block else "ALLOWED"
            if state!=expected:
                raise RuntimeError(f"Verification failed. Expected {expected}, got {state}.")
            self._audit_temp("CUSTOM_APP_BLOCK" if block else "CUSTOM_APP_ALLOW",username,
                             f"exe={exe}; mechanism=USER_DISALLOWRUN; verified={state}")
            self.logit(f"Policy app changed: {Path(exe).stem}; user={username}; state={state}")
        finally:
            self._close_user_hive(hive,loaded,orig_sid)

        after_state="BLOCKED" if block else "ALLOWED"
        self.policies()
        messagebox.showinfo("Policy changed",
            f"{Path(exe).stem}\nUser: {username}\nRequested: {after_state}\n\n"
            f"Verified: USER={after_state} | MACHINE=NOT SET | EFFECTIVE={after_state}\n\n"
            "If the target user is currently signed in, Windows may require sign-out/sign-in for the restriction to refresh.")
        return True

    # Compatibility alias used by the existing UI callbacks.
    def _custom_app_change(self, username, exe, block):
        return self._custom_app_policy_change(username, exe, block)

    def custom_apps_page(self):
        self.header("🧩 CUSTOM APPLICATION CONTROL","Add any EXE and control access for the selected local user. Changes are per-file and reversible.")

        # Always-visible action bar: create it before any user discovery so ADD EXE
        # cannot disappear if user enumeration has a problem.
        action_bar=tk.Frame(self.page,bg=PANEL,highlightbackground="#146b38",highlightthickness=1)
        action_bar.pack(fill="x",padx=8,pady=(4,7))
        tk.Label(action_bar,text="ACTIONS",bg=PANEL,fg=MUTED,font=("Consolas",9,"bold")).pack(side="left",padx=(10,6),pady=8)
        tk.Button(action_bar,text="➕ ADD EXE",command=self.add_custom_app,bg="#063d20",fg=GREEN,activebackground="#0b5b30",activeforeground="white",relief="flat",font=("Consolas",10,"bold"),padx=12,pady=7).pack(side="left",padx=4,pady=5)
        tk.Button(action_bar,text="↻ REFRESH",command=self.refresh_custom_apps,bg="#063d20",fg=GREEN,activebackground="#0b5b30",activeforeground="white",relief="flat",font=("Consolas",10,"bold"),padx=12,pady=7).pack(side="left",padx=4,pady=5)
        tk.Button(action_bar,text="🗑 REMOVE",command=self.remove_custom_app,bg="#063d20",fg=GREEN,activebackground="#0b5b30",activeforeground="white",relief="flat",font=("Consolas",10,"bold"),padx=12,pady=7).pack(side="left",padx=4,pady=5)
        tk.Button(action_bar,text="🔴 BLOCK",command=lambda:self.custom_action(True),bg="#063d20",fg=GREEN,activebackground="#0b5b30",activeforeground="white",relief="flat",font=("Consolas",10,"bold"),padx=12,pady=7).pack(side="left",padx=4,pady=5)
        tk.Button(action_bar,text="🟢 ALLOW",command=lambda:self.custom_action(False),bg="#063d20",fg=GREEN,activebackground="#0b5b30",activeforeground="white",relief="flat",font=("Consolas",10,"bold"),padx=12,pady=7).pack(side="left",padx=4,pady=5)
        tk.Button(action_bar,text="➜ ADD TO POLICIES",command=self.add_selected_custom_to_policies,bg="#063d20",fg=GREEN,activebackground="#0b5b30",activeforeground="white",relief="flat",font=("Consolas",10,"bold"),padx=12,pady=7).pack(side="left",padx=4,pady=5)

        top=tk.Frame(self.page,bg=BG); top.pack(fill="x",padx=8,pady=3)
        self.custom_user=tk.StringVar(value="pcuser")
        tk.Label(top,text="Target local user:",bg=BG,fg=TEXT,font=("Consolas",10,"bold")).pack(side="left")
        self.custom_user_combo=ttk.Combobox(top,textvariable=self.custom_user,state="readonly",width=22)
        self.custom_user_combo.pack(side="left",padx=6)
        try:
            rows=self._discover_user_rows()
            names=[r["name"] for r in rows if str(r.get("enabled","false")).lower()=="true"]
            self.custom_user_combo["values"]=names
            preferred=self._preferred_local_user(rows)
            if preferred in names:self.custom_user.set(preferred)
            elif "pcuser" in names:self.custom_user.set("pcuser")
            elif names:self.custom_user.set(names[0])
        except Exception as e:
            self.custom_user_combo["values"]=("pcuser",)
            self.custom_user.set("pcuser")
            self.logit(f"Custom Apps user discovery warning: {e}")

        cols=("app","exe","status")
        self.custom_tree=ttk.Treeview(self.page,columns=cols,show="headings",height=12)
        self.custom_tree.heading("app",text="APP")
        self.custom_tree.heading("exe",text="EXECUTABLE")
        self.custom_tree.heading("status",text="STATUS")
        self.custom_tree.column("app",width=180,minwidth=120,anchor="w",stretch=False)
        self.custom_tree.column("exe",width=520,minwidth=250,anchor="w",stretch=True)
        self.custom_tree.column("status",width=150,minwidth=120,anchor="center",stretch=False)
        self.custom_tree.pack(fill="both",expand=True,padx=10,pady=6)
        self.custom_tree.bind("<Configure>",self._resize_custom_tree)
        tk.Label(self.page,text="Per-user application policy for the selected local user. HKLM policy and NTFS permissions are not modified.",bg=BG,fg=MUTED,wraplength=900,justify="left").pack(anchor="w",padx=12,pady=4)
        self.refresh_custom_apps()

    def _resize_custom_tree(self,event=None):
        if not hasattr(self,"custom_tree"): return
        try:
            total=max(500,self.custom_tree.winfo_width())
            self.custom_tree.column("app",width=max(120,min(220,int(total*0.22))))
            self.custom_tree.column("status",width=max(120,min(180,int(total*0.18))))
            self.custom_tree.column("exe",width=max(250,total-int(self.custom_tree.column("app","width"))-int(self.custom_tree.column("status","width"))-8))
        except Exception: pass

    def add_custom_app(self):
        exe=filedialog.askopenfilename(title="Select application EXE",filetypes=[("Executable","*.exe"),("All files","*.*")])
        if not exe:return
        exe=os.path.abspath(exe)
        if any(os.path.normcase(x.get("exe",""))==os.path.normcase(exe) for x in self.custom_apps):
            messagebox.showinfo("Custom Apps","This EXE is already added.");return
        self.custom_apps.append({"name":Path(exe).stem,"exe":exe})
        self._save_custom_apps(); self.refresh_custom_apps()
        self.logit(f"Custom application added: {exe}")

    def refresh_custom_apps(self):
        if not hasattr(self,"custom_tree"):return
        # Reload the persistent list so Refresh reflects changes made by another
        # ZYNTRASEC instance/process as well.
        self.custom_apps=self._load_custom_apps()
        for i in self.custom_tree.get_children():self.custom_tree.delete(i)
        user=self.custom_user.get().strip()
        for item in self.custom_apps:
            exe=item.get("exe","")
            status=self._custom_app_policy_state(user,exe) if os.path.isfile(exe) else "MISSING"
            self.custom_tree.insert("","end",values=(item.get("name",Path(exe).stem),exe,status))

    def _selected_custom(self):
        if not hasattr(self,"custom_tree"):return None
        sel=self.custom_tree.selection()
        if not sel:return None
        vals=self.custom_tree.item(sel[0],"values")
        return vals[0],vals[1]

    def custom_action(self,block):
        selected=self._selected_custom()
        if not selected:
            messagebox.showwarning("Custom Apps","Select an application first.");return
        name,exe=selected; user=self.custom_user.get().strip()
        try:
            if self._custom_app_change(user,exe,block):
                self.refresh_custom_apps()
                messagebox.showinfo("Custom Apps",f"{name}: {'BLOCKED' if block else 'ALLOWED'}")
        except Exception as e:
            messagebox.showerror("Custom Apps",str(e))

    def add_selected_custom_to_policies(self):
        selected=self._selected_custom()
        if not selected:
            messagebox.showwarning("Custom Apps","Select an application first.")
            return
        name,exe=selected
        if not os.path.isfile(exe):
            messagebox.showwarning("Custom Apps","The selected EXE does not exist.")
            return
        if self._policy_app_is_pinned(exe):
            messagebox.showinfo("Policies",f"{name} is already in Policies.")
            return
        if not messagebox.askyesno("Add to Policies",f"Add {name} to the Policies tab?\n\nIt will remain in Custom Apps too.\nThe the same user-policy BLOCK/ALLOW control will be used."):
            return
        self._add_custom_to_policies(exe)
        self.logit(f"Custom application added to Policies: {exe}")
        messagebox.showinfo("Policies",f"{name} added to Policies.\n\nIt remains available in Custom Apps.")

    def remove_custom_app(self):
        selected=self._selected_custom()
        if not selected:return
        name,exe=selected
        if not messagebox.askyesno("Remove Custom App",f"Remove {name} from ZYNTRASEC's custom list?\n\nThis removes only the app from ZYNTRASEC's list; its current user policy is left unchanged."):
            return
        self.custom_apps=[x for x in self.custom_apps if os.path.normcase(x.get("exe",""))!=os.path.normcase(exe)]
        self._save_custom_apps();self.refresh_custom_apps()

    def clear(self):
        try:
            self._perf_monitor_running=False
            if hasattr(self,"_perf_after"):
                self.after_cancel(self._perf_after)
                del self._perf_after
        except Exception:
            pass
        # Clear only module content. Keep the output splitter alive so the
        # console remains resizable after every navigation.
        for w in self.page.winfo_children():
            if w is not getattr(self, "output_splitter", None):
                w.destroy()
        try:
            self.page_canvas.update_idletasks()
            self.page_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def header(self,t,sub=""):
        self.clear()
        self.output_clear("OUTPUT // ZYNTRASEC CONSOLE")
        tk.Label(self.page,text=t,bg=BG,fg=GREEN,font=("Consolas",19,"bold")).pack(anchor="w",padx=8,pady=(5,1))
        if sub:tk.Label(self.page,text=sub,bg=BG,fg=MUTED,font=("Consolas",9)).pack(anchor="w",padx=8,pady=(0,9))
        self.badge.config(text="● ADMINISTRATOR" if is_admin() else "● ADMIN REQUIRED",
                          fg=GREEN if is_admin() else WARN)
        # Every module opens at the top instead of inheriting the previous
        # module's scroll position.
        try:
            self.after_idle(lambda: self.page_canvas.yview_moveto(0.0))
        except Exception:
            pass
        self.after_idle(self._bind_all_tooltips)

    def output_clear(self,title="OUTPUT // ZYNTRASEC CONSOLE"):
        try:
            self.output_title.config(text=title)
            self.log.delete("1.0","end")
        except Exception:
            pass

    def output_show(self,module,action,text,status="SUCCESS"):
        try:
            self.output_title.config(text="OUTPUT // ZYNTRASEC CONSOLE")
            self.log.delete("1.0","end")
            stamp=datetime.now().strftime("%H:%M:%S")
            status_icon={"SUCCESS":"[✓]","READY":"[✓]","ONLINE":"[✓]","REVIEW":"[!]","ATTENTION":"[!]","BLOCKED":"[!]","ERROR":"[X]"}.get(str(status).upper(),"[•]")
            line="═"*96
            top="╔"+line+"╗\n"
            title=f"║ ZYNTRASEC // SYSTEM INTELLIGENCE CONSOLE".ljust(97)+"║\n"
            mid="╠"+line+"╣\n"
            meta=(f"║ [{stamp}] MODULE : {str(module).upper()}".ljust(97)+"║\n"
                  f"║ [{stamp}] ACTION : {str(action).upper()}".ljust(97)+"║\n"
                  f"║ {status_icon} STATUS : {str(status).upper()}".ljust(97)+"║\n")
            body="╠"+line+"╣\n"
            raw=(text or "(no output)").rstrip().splitlines()
            rendered=[]
            for ln in raw:
                # Keep long diagnostic lines readable inside the terminal frame.
                if len(ln)>92:
                    rendered.append(ln[:92])
                    rendered.append("... "+ln[92:])
                else:
                    rendered.append(ln)
            content="".join((f"║ >> {ln}".ljust(97)+"║\n") for ln in rendered)
            bottom="╚"+line+"╝\n"
            self.log.insert("end",top+title+mid+meta+body+content+bottom)
            self._output_auto_see("end")
        except Exception:
            pass

    def output_append(self,text):
        try:
            self.log.insert("end",text.rstrip()+"\n")
            self._output_auto_see("end")
        except Exception:
            pass

    def logit(self,s):
        self.output_append(f"[{datetime.now():%H:%M:%S}] {s}")

    def home(self):
        self.header("ZYNTRASEC // WINDOWS CONTROL CENTER","All-in-one setup, management and rollback console.")
        f=tk.Frame(self.page,bg=BG);f.pack(fill="x",padx=10,pady=15)
        cards=[("MODE","AUTO-DETECT"),("USER",os.environ.get("USERNAME","")),("PRIVILEGE","ADMIN" if is_admin() else "STANDARD"),("OS",platform.release())]
        for a,b in cards:self.card(f,a,b)
        box=tk.Frame(self.page,bg=PANEL,highlightbackground="#146b38",highlightthickness=1);box.pack(fill="x",padx=10,pady=8)
        tk.Label(box,text="CHOOSE OPERATION",bg=PANEL,fg=TEXT,font=("Consolas",15,"bold")).pack(pady=13)
        ttk.Button(box,text="🆕 NEW WINDOWS SETUP",command=self.new_setup).pack(pady=5)
        ttk.Button(box,text="🛠 MANAGE EXISTING PC",command=self.manage).pack(pady=5)
        tk.Label(box,text="Workflow: SCAN → REVIEW → BACKUP → CHANGE → VERIFY → REPORT",
                 bg=PANEL,fg=MUTED).pack(pady=13)

    def card(self,p,a,b):
        q=tk.Frame(p,bg=PANEL,highlightbackground="#0d4d28",highlightthickness=1);q.pack(side="left",fill="both",expand=True,padx=4)
        tk.Label(q,text=a,bg=PANEL,fg=MUTED).pack(pady=(10,2));tk.Label(q,text=b,bg=PANEL,fg=GREEN,font=("Consolas",13,"bold")).pack(pady=(0,10))

    def new_setup(self):
        self.header("🆕 NEW WINDOWS SETUP — ALL IN ONE",
                    "Fresh Windows checklist: scan → review → backup → configure → verify. Destructive storage actions require explicit confirmation.")
        # One-click read-only overview first; individual modules remain available below.
        ttk.Button(self.page,text="🔍 ONE-CLICK COMPLETE CHECK",command=self.new_setup_complete_check).pack(anchor="w",padx=10,pady=(4,8))
        ttk.Button(self.page,text="💾 PRE-SETUP BACKUP + RESTORE POINT",command=self.new_setup_backup).pack(anchor="w",padx=10,pady=4)
        steps=[
            ("01","WINDOWS","Version / build / edition / activation",self.windows_setup_info),
            ("02","WINDOWS UPDATE","Update status and pending restart",lambda:run("start ms-settings:windowsupdate")),
            ("03","DRIVERS","Device Manager + optional/OEM update paths",self.driver_center),
            ("04","USERS","Local users, admin/standard roles",self.users),
            ("05","SECURITY","Defender / Firewall / UAC / TPM / Secure Boot / Memory Integrity",self.security),
            ("06","POLICIES","User restrictions and policy controls",self.policies),
            ("07","ACL / PERMISSIONS","Protect selected folders",self.acl),
            ("08","STARTUP","Startup applications and locations",self.startup),
            ("09","WINDOWS HEALTH","SFC / DISM health checks",self.windows_health),
            ("10","STORAGE","C:/D: usage and large folders/files",self.storage),
            ("11","PARTITIONS","GB size / equal split / preview / apply from unallocated space",self.partition_manager),
            ("12","PERFORMANCE","CPU / RAM / GPU / SSD / power",self.performance_setup),
            ("13","NETWORK","Adapter / IP / DNS / internet status",self.network),
            ("14","WINDOWS COMPONENTS",".NET / WSL / Hyper-V / VMP / Sandbox / OpenSSH",self.windows_components),
            ("15","SOFTWARE","Installed apps and setup checklist",self.software_setup),
            ("16","HARDWARE","CPU / RAM / GPU / disks / battery / device errors",self.hardware_diagnostic),
            ("17","BACKUP & RECOVERY","Restore Point / registry / config / ACL / startup backup",self.backup_recovery_center),
            ("18","BASELINE","Save current PC baseline and compare later",self.baseline_center),
            ("19","FINAL REPORT","Generate final Windows setup report",self.report),
        ]
        for n,t,d,fn in steps:self.step(n,t,d,fn)
        ttk.Button(self.page,text="⚙ APPLY SAFE BASELINE",command=self.safe_baseline).pack(anchor="w",padx=10,pady=10)
        tk.Label(self.page,text="↓ Scroll this section to access all 19 setup modules ↓",bg=BG,fg=MUTED,font=("Consolas",9,"bold")).pack(pady=(0,12))
        self.output_show("NEW WINDOWS SETUP", "READY", "Recommended order: COMPLETE CHECK → BACKUP → WINDOWS UPDATE/DRIVERS → SECURITY → STORAGE/PARTITIONS → PERFORMANCE → FINAL REPORT.\n\nPartition operations are limited to unallocated space in this module; preview is shown before apply.")

    def step(self,n,title,desc,fn):
        box=tk.Frame(self.page,bg="#06130b",highlightbackground="#146b38",highlightthickness=1)
        box.pack(fill="x",padx=10,pady=4)
        left=tk.Frame(box,bg="#06130b"); left.pack(side="left",fill="x",expand=True,padx=10,pady=7)
        tk.Label(left,text=n,bg="#06130b",fg=MUTED,font=("Consolas",9,"bold"),width=3,anchor="w").pack(side="left")
        mid=tk.Frame(left,bg="#06130b"); mid.pack(side="left",fill="x",expand=True)
        tk.Label(mid,text=title,bg="#06130b",fg=GREEN,font=("Consolas",11,"bold"),anchor="w").pack(fill="x")
        tk.Label(mid,text=desc,bg="#06130b",fg=TEXT,font=("Consolas",9),anchor="w",wraplength=850,justify="left").pack(fill="x",pady=(2,0))
        ttk.Button(box,text="OPEN",command=fn).pack(side="right",padx=10,pady=9)

    def _new_setup_ps(self, script, label):
        def done(r):
            rc,out=r
            self.output_show("NEW WINDOWS SETUP",label,out or "(no output)","SUCCESS" if rc==0 else "REVIEW")
        self._async_job(lambda:ps(script,60),done,label+"...")

    def new_setup_complete_check(self):
        def work():
            rows=[]
            checks=[
                ("Windows", "(Get-CimInstance Win32_OperatingSystem | Select-Object -First 1 | ForEach-Object { $_.Caption+' | Build '+$_.BuildNumber })"),
                ("Activation", "(Get-CimInstance SoftwareLicensingProduct | Where-Object {$_.PartialProductKey -and $_.LicenseStatus -eq 1} | Select-Object -First 1 Name,LicenseStatus | Out-String).Trim()"),
                ("TPM", "(Get-Tpm | Select-Object TpmPresent,TpmReady | Format-List | Out-String).Trim()"),
                ("Secure Boot", "try {[string](Confirm-SecureBootUEFI -ErrorAction Stop)} catch {'Unavailable/Legacy BIOS'}"),
                ("Defender RTP", "[string](Get-MpComputerStatus).RealTimeProtectionEnabled"),
                ("Firewall", "[string]((Get-NetFirewallProfile | Where-Object Enabled -eq $false).Count -eq 0)"),
                ("UAC", r"[string]((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System').EnableLUA -eq 1)"),
                ("Memory Integrity", r"[string]((Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' -ErrorAction SilentlyContinue).Enabled -eq 1)"),
                ("C: Free", "[string]([math]::Round((Get-PSDrive C).Free/1GB,1))+' GB'"),
                ("D: Free", "if(Test-Path D:\\){[string]([math]::Round((Get-PSDrive D).Free/1GB,1))+' GB'}else{'NOT PRESENT'}"),
                ("Users", "[string]((Get-LocalUser).Count)"),
                ("Startup", "[string]((Get-CimInstance Win32_StartupCommand).Count)"),
            ]
            for name,script in checks:
                rc,out=ps(script,30); val=(out or '').strip().replace('\r','').replace('\n',' | ')
                ok=True if name in ('Windows','C: Free','D: Free','Users','Startup') else ('True' in val or 'LicenseStatus' in val or 'TPM' in val)
                rows.append((name,'OK' if ok else 'REVIEW',val))
            return rows
        def done(rows):
            txt="NEW WINDOWS SETUP — COMPLETE CHECK\n\n"+"\n".join(f"{a:<20} {b:<8} {c}" for a,b,c in rows)
            ok=sum(b=='OK' for _,b,_ in rows); self.output_show("NEW WINDOWS SETUP","COMPLETE CHECK",txt,f"{ok}/{len(rows)} OK")
        self._async_job(work,done,"COMPLETE CHECKING")

    def new_setup_backup(self):
        self.make_backup()
        if is_admin():
            rc,out=run('powershell.exe -NoProfile -Command "Checkpoint-Computer -Description \'ZYNTRASEC_NEW_WINDOWS_SETUP\' -RestorePointType \'MODIFY_SETTINGS\'"',120)
            self.logit(("Restore Point: CREATED" if rc==0 else "Restore Point: REVIEW")+"\n"+out[-1800:])
        else:
            self.logit("Restore Point: ADMINISTRATOR REQUIRED")

    def windows_setup_info(self):
        self.header("🪟 WINDOWS SETUP", "Complete PC / Windows information — live read-only inventory.")
        wrap = tk.Frame(self.page, bg=BG)
        wrap.pack(fill="both", expand=True, padx=8, pady=(0,8))
        tk.Label(wrap, text="PC SYSTEM INFORMATION", bg=BG, fg=GREEN,
                 font=("Consolas",11,"bold")).pack(anchor="w", pady=(0,4))
        tree_frame = tk.Frame(wrap, bg="#06130b", highlightbackground="#146b38", highlightthickness=1)
        tree_frame.pack(fill="both", expand=True)
        cols=("section","item","value")
        self._windows_tree=ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        self._windows_tree.heading("section", text="SECTION")
        self._windows_tree.heading("item", text="INFORMATION")
        self._windows_tree.heading("value", text="VALUE")
        self._windows_tree.column("section", width=150, anchor="w")
        self._windows_tree.column("item", width=230, anchor="w")
        self._windows_tree.column("value", width=760, anchor="w")
        vs=CyberScrollbar(tree_frame, orient="vertical", command=self._windows_tree.yview)
        hs=CyberScrollbar(tree_frame, orient="horizontal", command=self._windows_tree.xview)
        self._windows_tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self._windows_tree.grid(row=0,column=0,sticky="nsew")
        vs.grid(row=0,column=1,sticky="ns")
        hs.grid(row=1,column=0,sticky="ew")
        tree_frame.grid_rowconfigure(0,weight=1); tree_frame.grid_columnconfigure(0,weight=1)
        buttons=tk.Frame(self.page,bg=BG)
        buttons.pack(fill="x",padx=8,pady=(0,7))
        ttk.Button(buttons,text="CHECK / REFRESH PC INFO",command=self.windows_setup_info_refresh).pack(side="left",padx=(0,6))
        ttk.Button(buttons,text="OPEN ABOUT",command=lambda:run("start ms-settings:about")).pack(side="left",padx=(0,6))
        ttk.Button(buttons,text="OPEN ACTIVATION",command=lambda:run("start ms-settings:activation")).pack(side="left")
        self.windows_setup_info_refresh()

    def windows_setup_info_refresh(self):
        script = r'''
$ErrorActionPreference='SilentlyContinue'
$os=Get-CimInstance Win32_OperatingSystem
$cs=Get-CimInstance Win32_ComputerSystem
$cpu=@(Get-CimInstance Win32_Processor)
$bios=Get-CimInstance Win32_BIOS
$board=Get-CimInstance Win32_BaseBoard
$gpu=@(Get-CimInstance Win32_VideoController)
$ram=@(Get-CimInstance Win32_PhysicalMemory)
$disks=@(Get-CimInstance Win32_DiskDrive)
$vols=@(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3")
$net=@(Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True")
$hot=@(Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10)
$active=@(Get-CimInstance SoftwareLicensingProduct | Where-Object {$_.PartialProductKey -and $_.ApplicationID -eq '55c92734-d682-4d71-983e-d6ec3f16059f' -and $_.LicenseStatus -eq 1} | Select-Object -First 1)
$activation=if($active){'ACTIVATED'}else{'NOT ACTIVATED'}
$channel=if($active){[string]$active.Description}else{'Not activated / no active license found'}
$install=try{[Management.ManagementDateTimeConverter]::ToDateTime($os.InstallDate).ToString('yyyy-MM-dd HH:mm:ss')}catch{'N/A'}
$boot=try{[string]$os.BootDevice}catch{'N/A'}
$tz=(Get-TimeZone).DisplayName
$items=@()
function AddItem($s,$i,$v){$script:items += [pscustomobject]@{Section=$s;Item=$i;Value=[string]$v}}
AddItem 'WINDOWS' 'Host Name' $cs.Name
AddItem 'WINDOWS' 'OS Name' $os.Caption
AddItem 'WINDOWS' 'Version' $os.Version
AddItem 'WINDOWS' 'OS Build' $os.BuildNumber
AddItem 'WINDOWS' 'Architecture' $os.OSArchitecture
AddItem 'WINDOWS' 'Install Date' $install
AddItem 'WINDOWS' 'Boot Device' $boot
AddItem 'WINDOWS' 'System Directory' $os.SystemDirectory
AddItem 'WINDOWS' 'Windows Directory' $os.WindowsDirectory
AddItem 'WINDOWS' 'Registered User' $os.RegisteredUser
AddItem 'WINDOWS' 'Organization' $os.Organization
AddItem 'WINDOWS' 'Product Type' $os.ProductType
AddItem 'WINDOWS' 'Activation' $activation
AddItem 'WINDOWS' 'License Channel' $channel
AddItem 'COMPUTER' 'Manufacturer' $cs.Manufacturer
AddItem 'COMPUTER' 'Model' $cs.Model
AddItem 'COMPUTER' 'System Type' $cs.SystemType
AddItem 'COMPUTER' 'Domain / Workgroup' $cs.Domain
AddItem 'COMPUTER' 'User Name' $cs.UserName
AddItem 'COMPUTER' 'Total RAM' (([math]::Round($cs.TotalPhysicalMemory/1GB,2)).ToString()+' GB')
AddItem 'CPU' 'Processor(s)' $cpu.Count
foreach($c in $cpu){AddItem 'CPU' 'Name' $c.Name; AddItem 'CPU' 'Cores / Logical' ($c.NumberOfCores.ToString()+' / '+$c.NumberOfLogicalProcessors.ToString()); AddItem 'CPU' 'Max Clock' (($c.MaxClockSpeed).ToString()+' MHz'); AddItem 'CPU' 'Manufacturer' $c.Manufacturer}
AddItem 'MOTHERBOARD' 'Manufacturer' $board.Manufacturer
AddItem 'MOTHERBOARD' 'Product' $board.Product
AddItem 'MOTHERBOARD' 'Serial' $board.SerialNumber
AddItem 'BIOS' 'Manufacturer' $bios.Manufacturer
AddItem 'BIOS' 'Version' $bios.SMBIOSBIOSVersion
AddItem 'BIOS' 'Release Date' ([Management.ManagementDateTimeConverter]::ToDateTime($bios.ReleaseDate).ToString('yyyy-MM-dd'))
foreach($r in $ram){AddItem 'MEMORY' 'Module' (($r.Manufacturer+' '+$r.PartNumber).Trim()+' | '+([math]::Round($r.Capacity/1GB,2)).ToString()+' GB | '+$r.Speed+' MHz')}
foreach($d in $disks){AddItem 'DISK' 'Physical Disk' (($d.Model)+' | '+([math]::Round($d.Size/1GB,2)).ToString()+' GB | '+$d.InterfaceType)}
foreach($v in $vols){AddItem 'VOLUME' 'Drive' (($v.DeviceID)+' | '+([math]::Round($v.Size/1GB,2)).ToString()+' GB total | '+([math]::Round($v.FreeSpace/1GB,2)).ToString()+' GB free | '+$v.FileSystem)}
foreach($g in $gpu){AddItem 'GPU' 'Adapter' (($g.Name)+' | '+$g.DriverVersion)}
foreach($n in $net){AddItem 'NETWORK' 'Adapter' $n.Description; AddItem 'NETWORK' 'MAC' $n.MACAddress; AddItem 'NETWORK' 'IP' (($n.IPAddress -join ', ')); AddItem 'NETWORK' 'Gateway' (($n.DefaultIPGateway -join ', ')); AddItem 'NETWORK' 'DNS' (($n.DNSServerSearchOrder -join ', '))}
AddItem 'SYSTEM' 'Time Zone' $tz
AddItem 'SYSTEM' 'Boot Time' ([Management.ManagementDateTimeConverter]::ToDateTime($os.LastBootUpTime).ToString('yyyy-MM-dd HH:mm:ss'))
AddItem 'SYSTEM' 'Page File' (($os.TotalVirtualMemorySize/1MB).ToString('0.00')+' GB total | '+(($os.FreeVirtualMemory)/1MB).ToString('0.00')+' GB free')
foreach($h in $hot){AddItem 'UPDATES' 'HotFix' (($h.HotFixID)+' | '+$h.InstalledOn)}
$items | ConvertTo-Json -Compress
'''
        def done(result):
            rc,out=result
            if rc!=0:
                self.output_show("WINDOWS SETUP","PC INFORMATION",out or "PC information check failed.","REVIEW")
                return
            try:
                data=json.loads(out.strip())
                if isinstance(data,dict): data=[data]
                for iid in self._windows_tree.get_children(): self._windows_tree.delete(iid)
                for row in data:
                    self._windows_tree.insert("","end",values=(row.get("Section",""),row.get("Item",""),row.get("Value","")))
                summary="Complete PC information refreshed.\n\n"+"\n".join(f"{r.get('Section',''):12} {r.get('Item',''):24} {r.get('Value','')}" for r in data[:80])
                self.output_show("WINDOWS SETUP","PC INFORMATION",summary,"SUCCESS")
            except Exception as e:
                self.output_show("WINDOWS SETUP","PC INFORMATION",f"Could not parse PC information: {e}\n\nRaw output:\n{out}","REVIEW")
        self._async_job(lambda:ps(script,90),done,"PC INFO...")

    def driver_center(self):
        self.header("🔧 DRIVER CENTER","Driver inventory, Windows Update driver installation and Device Manager review.")
        ttk.Button(self.page,text="SCAN DRIVERS",command=lambda:self._new_setup_ps("Get-CimInstance Win32_PnPSignedDriver | Select DeviceName,DriverVersion,DriverDate,Manufacturer,IsSigned | Sort DeviceName | Format-Table -AutoSize", "DRIVER SCAN")).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="⚡ AUTO UPDATE DRIVERS",command=self.driver_auto_update).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="OPEN DEVICE MANAGER",command=lambda:run("devmgmt.msc")).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="OPEN WINDOWS UPDATE",command=lambda:run("start ms-settings:windowsupdate-optionalupdates")).pack(anchor="w",padx=8,pady=4)
        tk.Label(self.page,text="AUTO UPDATE uses Windows Update's signed driver catalog; no third-party driver sites are used.",bg=BG,fg=MUTED,font=("Consolas",9)).pack(anchor="w",padx=8,pady=(2,6))

    def driver_auto_update(self):
        if not is_admin():
            messagebox.showwarning("ZYNTRASEC", "Administrator permission is required for automatic driver installation.")
            return
        script = r'''
$ErrorActionPreference = 'Stop'
function CodeName([int]$code) {
    switch ($code) {
        0 { 'NOT_STARTED' }; 1 { 'IN_PROGRESS' }; 2 { 'SUCCEEDED' }
        3 { 'SUCCEEDED_WITH_ERRORS' }; 4 { 'FAILED' }; 5 { 'ABORTED' }
        default { 'UNKNOWN' }
    }
}
function IsSuccessCode([int]$code) { return ($code -eq 2) }
Write-Output '>> DRIVER AUTO UPDATE INITIALIZED'
Write-Output '>> SOURCE       : WINDOWS UPDATE DRIVER CATALOG'
Write-Output '>> THIRD-PARTY  : NOT USED'
try {
    $session = New-Object -ComObject Microsoft.Update.Session
    $session.ClientApplicationID = 'ZYNTRASEC Driver Center'
    $searcher = $session.CreateUpdateSearcher()
    Write-Output '>> SEARCHING    : AVAILABLE DRIVER UPDATES...'
    $result = $searcher.Search("IsInstalled=0 and IsHidden=0 and Type='Driver'")
    $updates = New-Object -ComObject Microsoft.Update.UpdateColl
    foreach ($u in $result.Updates) {
        if (-not $u.EulaAccepted) { try { $u.AcceptEula() } catch {} }
        [void]$updates.Add($u)
    }
    Write-Output (">> FOUND        : {0} DRIVER UPDATE(S)" -f $updates.Count)
    if ($updates.Count -eq 0) {
        Write-Output '>> RESULT       : NO DRIVER UPDATES AVAILABLE'
        Write-Output '>> STATUS       : SUCCESS'
        exit 0
    }
    for ($i=0; $i -lt $updates.Count; $i++) { Write-Output (">> QUEUED       : {0}" -f $updates.Item($i).Title) }
    $downloader = $session.CreateUpdateDownloader(); $downloader.Updates = $updates
    Write-Output '>> DOWNLOAD     : STARTING...'
    $downloadResult = $downloader.Download(); $downloadCode=[int]$downloadResult.ResultCode
    Write-Output (">> DOWNLOAD     : {0} (CODE {1})" -f (CodeName $downloadCode),$downloadCode)
    if (-not (IsSuccessCode $downloadCode)) {
        Write-Output '>> DOWNLOAD     : REVIEW REQUIRED; INSTALL SKIPPED'
        Write-Output '>> STATUS       : REVIEW'; exit 2
    }
    $installer = $session.CreateUpdateInstaller(); $installer.Updates = $updates
    Write-Output '>> INSTALL      : STARTING...'
    $installResult = $installer.Install(); $installCode=[int]$installResult.ResultCode
    Write-Output (">> INSTALL      : {0} (CODE {1})" -f (CodeName $installCode),$installCode)
    Write-Output (">> REBOOT NEEDED : {0}" -f $installResult.RebootRequired)
    $ok=0; $review=0; $failed=0
    for ($i=0; $i -lt $updates.Count; $i++) {
        $r=$installResult.GetUpdateResult($i); $u=$updates.Item($i); $rc=[int]$r.ResultCode
        if ($rc -eq 2) { $ok++; $tag='UPDATED' }
        elseif ($rc -eq 3) { $review++; $tag='UPDATED_WITH_WARNINGS' }
        else { $failed++; $tag='REVIEW' }
        Write-Output (">> RESULT       : [{0}] {1} :: {2}" -f (CodeName $rc),$u.Title,$tag)
    }
    if ($failed -gt 0 -or $review -gt 0 -or -not (IsSuccessCode $installCode)) {
        Write-Output (">> COMPLETE     : {0} SUCCESS / {1} REVIEW / {2} FAILED" -f $ok,$review,$failed)
        Write-Output '>> STATUS       : REVIEW'; exit 2
    }
    Write-Output '>> VERIFY       : RESCANNING DRIVER UPDATES...'
    Start-Sleep -Seconds 2
    $verify = $searcher.Search("IsInstalled=0 and IsHidden=0 and Type='Driver'")
    $titles=@($updates | ForEach-Object { $_.Title })
    $remaining=@($verify.Updates | Where-Object { $titles -contains $_.Title })
    if ($remaining.Count -gt 0 -and -not $installResult.RebootRequired) {
        Write-Output (">> VERIFY       : {0} MATCHING UPDATE(S) STILL OFFERED" -f $remaining.Count)
        Write-Output '>> STATUS       : REVIEW'; exit 2
    }
    if ($installResult.RebootRequired) { Write-Output '>> VERIFY       : INSTALLATION ACCEPTED; REBOOT REQUIRED TO FINALIZE' }
    else { Write-Output '>> VERIFY       : INSTALLATION ACCEPTED; NO MATCHING UPDATE REMAINS' }
    Write-Output (">> COMPLETE     : {0} SUCCESS / {1} REVIEW / {2} FAILED" -f $ok,$review,$failed)
    Write-Output '>> STATUS       : SUCCESS'
    exit 0
}
catch {
    Write-Output (">> ERROR        : {0}" -f $_.Exception.Message)
    Write-Output '>> STATUS       : REVIEW'; exit 1
}
'''
        def work():
            return ps(script,900)
        def done(result):
            rc,out=result
            status='SUCCESS' if rc==0 else 'REVIEW'
            self.output_show('DRIVER CENTER','AUTO UPDATE DRIVERS',out or '(no output)',status)
        self._async_job(work,done,'DRIVER UPDATE...')

    def performance_setup(self):
        self.performance()

    def windows_components(self):
        self.header("🧩 WINDOWS COMPONENTS","Read-only component inventory and safe Windows feature access.")
        buttons = ttk.Frame(self.page)
        buttons.pack(anchor="w", padx=8, pady=4)
        ttk.Button(buttons, text="REFRESH COMPONENT STATUS", command=lambda: self._new_setup_ps(
            "Get-WindowsOptionalFeature -Online | Where-Object {$_.FeatureName -match 'Microsoft-Windows-Subsystem-Linux|VirtualMachinePlatform|Microsoft-Hyper-V|Containers-DisposableClientVM|OpenSSH|NetFx3'} | Select FeatureName,State | Sort FeatureName | Format-Table -AutoSize",
            "COMPONENT STATUS"
        )).pack(side="left", padx=(0,6))
        ttk.Button(buttons, text="ALL OPTIONAL FEATURES", command=lambda: self._new_setup_ps(
            "Get-WindowsOptionalFeature -Online | Select FeatureName,State | Sort FeatureName | Format-Table -AutoSize",
            "ALL OPTIONAL FEATURES"
        )).pack(side="left", padx=(0,6))
        ttk.Button(buttons, text="COMPONENT REPORT", command=lambda: self._new_setup_ps(
            "Get-WindowsOptionalFeature -Online | Group-Object State | Select Name,Count | Sort Name | Format-Table -AutoSize; Write-Output ''; Get-WindowsOptionalFeature -Online | Where-Object State -eq 'Enabled' | Select FeatureName,State | Sort FeatureName | Format-Table -AutoSize",
            "COMPONENT REPORT"
        )).pack(side="left", padx=(0,6))
        ttk.Button(buttons, text="OPEN OPTIONAL FEATURES", command=lambda: run("optionalfeatures.exe")).pack(side="left", padx=(0,6))
        ttk.Button(buttons, text="OPEN WINDOWS FEATURES", command=lambda: run("start ms-settings:optionalfeatures")).pack(side="left")
        self._new_setup_ps(
            "Get-WindowsOptionalFeature -Online | Where-Object {$_.FeatureName -match 'Microsoft-Windows-Subsystem-Linux|VirtualMachinePlatform|Microsoft-Hyper-V|Containers-DisposableClientVM|OpenSSH|NetFx3'} | Select FeatureName,State | Sort FeatureName | Format-Table -AutoSize",
            "COMPONENT CHECK"
        )

    def software_setup(self):
        self.header("📦 SOFTWARE SETUP","Installed software inventory, search and reporting; no automatic mass uninstall.")
        toolbar=tk.Frame(self.page,bg=BG); toolbar.pack(fill="x",padx=8,pady=(2,4))
        ttk.Button(toolbar,text="🔄 REFRESH SOFTWARE",command=lambda:self._software_inventory()).pack(side="left",padx=(0,5))
        ttk.Button(toolbar,text="📊 SOFTWARE REPORT",command=self._software_report).pack(side="left",padx=5)
        ttk.Button(toolbar,text="⚙ OPEN INSTALLED APPS",command=lambda:run("start ms-settings:appsfeatures")).pack(side="left",padx=5)
        search=tk.Frame(self.page,bg=BG); search.pack(fill="x",padx=8,pady=4)
        tk.Label(search,text="SEARCH SOFTWARE:",bg=BG,fg=MUTED).pack(side="left",padx=(0,6))
        self._software_search_var=tk.StringVar()
        ent=ttk.Entry(search,textvariable=self._software_search_var,width=45)
        ent.pack(side="left",padx=4)
        ttk.Button(search,text="🔍 SEARCH",command=self._software_search).pack(side="left",padx=5)
        ent.bind("<Return>",lambda e:self._software_search())
        self._software_inventory()

    def _software_registry_query(self):
        return r"Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object {$_.DisplayName} | Select-Object DisplayName,DisplayVersion,Publisher,InstallDate,EstimatedSize | Sort-Object DisplayName"

    def _software_inventory(self):
        script=self._software_registry_query()+r" | Format-Table -AutoSize"
        self._new_setup_ps(script,"SOFTWARE INVENTORY")

    def _software_search(self):
        term=self._software_search_var.get().strip() if hasattr(self,'_software_search_var') else ''
        if not term:
            self._software_inventory(); return
        safe=term.replace("'","''")
        script=self._software_registry_query()+f" | Where-Object {{$_.DisplayName -like '*{safe}*' -or $_.Publisher -like '*{safe}*'}} | Format-Table -AutoSize"
        self._new_setup_ps(script,"SOFTWARE SEARCH")

    def _software_report(self):
        script=self._software_registry_query()+r" | ForEach-Object {[pscustomobject]@{DisplayName=$_.DisplayName;Publisher=if($_.Publisher){$_.Publisher}else{'Unknown'}}}; $apps=@(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object {$_.DisplayName}); Write-Output ('TOTAL INSTALLED APPS : '+$apps.Count); Write-Output ''; Write-Output 'TOP PUBLISHERS:'; $apps | Group-Object Publisher | Sort-Object Count -Descending | Select-Object -First 15 Name,Count | Format-Table -AutoSize"
        self._new_setup_ps(script,"SOFTWARE REPORT")

    def hardware_diagnostic(self):
        self.header("🖥 HARDWARE DIAGNOSTIC","Read-only hardware inventory, device status and driver problem checks.")
        btns=tk.Frame(self.page,bg=BG);btns.pack(fill="x",padx=8,pady=5)
        ttk.Button(btns,text="🔄 REFRESH HARDWARE",command=self._hardware_inventory).pack(side="left",padx=(0,6))
        ttk.Button(btns,text="⚠ DRIVER PROBLEMS",command=self._hardware_driver_problems).pack(side="left",padx=6)
        ttk.Button(btns,text="📋 HARDWARE REPORT",command=self._hardware_report).pack(side="left",padx=6)
        self._hardware_inventory()

    def _hardware_inventory(self):
        script=r'''$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed
$cs=Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory
$mb=Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer,Product,SerialNumber
$bios=Get-CimInstance Win32_BIOS | Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate
$ram=Get-CimInstance Win32_PhysicalMemory | Select-Object BankLabel,Capacity,Speed,Manufacturer,PartNumber
$gpu=Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,AdapterRAM
$disk=Get-PhysicalDisk | Select-Object FriendlyName,MediaType,BusType,HealthStatus,@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}}
$net=Get-CimInstance Win32_NetworkAdapter | Where-Object {$_.PhysicalAdapter -eq $true -and $_.NetEnabled -eq $true} | Select-Object Name,Speed,MACAddress
$bad=@(Get-PnpDevice -PresentOnly | Where-Object {$_.Status -ne 'OK'})
Write-Output '=== CPU ==='; $cpu | Format-List
Write-Output '=== SYSTEM ==='; $cs | ForEach-Object { [pscustomobject]@{Manufacturer=$_.Manufacturer;Model=$_.Model;RAM_GB=[math]::Round($_.TotalPhysicalMemory/1GB,1)} } | Format-List
Write-Output '=== MOTHERBOARD ==='; $mb | Format-List
Write-Output '=== BIOS ==='; $bios | Format-List
Write-Output '=== RAM MODULES ==='; $ram | ForEach-Object {[pscustomobject]@{Bank=$_.BankLabel;CapacityGB=[math]::Round($_.Capacity/1GB,1);SpeedMHz=$_.Speed;Manufacturer=$_.Manufacturer;PartNumber=$_.PartNumber}} | Format-Table -AutoSize
Write-Output '=== GPU ==='; $gpu | ForEach-Object {[pscustomobject]@{Name=$_.Name;Driver=$_.DriverVersion;VRAM_GB=if($_.AdapterRAM){[math]::Round($_.AdapterRAM/1GB,1)}else{'N/A'}}} | Format-Table -AutoSize
Write-Output '=== STORAGE ==='; $disk | Format-Table -AutoSize
Write-Output '=== NETWORK ADAPTERS ==='; $net | Format-Table -AutoSize
Write-Output ('=== DEVICE PROBLEMS : '+$bad.Count+' ==='); if($bad.Count){$bad | Select-Object Class,FriendlyName,Status,ProblemCode | Format-Table -AutoSize}else{Write-Output 'No present devices reporting a non-OK status.'}'''
        self._new_setup_ps(script,"HARDWARE INVENTORY")

    def _hardware_driver_problems(self):
        script=r'''$bad=@(Get-PnpDevice -PresentOnly | Where-Object {$_.Status -ne 'OK'})
Write-Output ('DEVICE PROBLEMS : '+$bad.Count)
if($bad.Count){$bad | Select-Object Class,FriendlyName,Status,ProblemCode,InstanceId | Format-Table -AutoSize}else{Write-Output 'DRIVER PROBLEMS : 0'}'''
        self._new_setup_ps(script,"DRIVER PROBLEMS")

    def _hardware_report(self):
        script=r'''$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors
$cs=Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,@{N='RAM_GB';E={[math]::Round($_.TotalPhysicalMemory/1GB,1)}}
$gpu=(Get-CimInstance Win32_VideoController | Select-Object -First 1 Name,DriverVersion)
$disks=@(Get-PhysicalDisk)
$bad=@(Get-PnpDevice -PresentOnly | Where-Object {$_.Status -ne 'OK'})
Write-Output 'ZYNTRASEC // HARDWARE REPORT'
$cpu | Format-List
$cs | Format-List
$gpu | Format-List
Write-Output ('PHYSICAL DISKS : '+$disks.Count)
$disks | Select-Object FriendlyName,MediaType,BusType,HealthStatus,@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}} | Format-Table -AutoSize
Write-Output ('DEVICE PROBLEMS : '+$bad.Count)'''
        self._new_setup_ps(script,"HARDWARE REPORT")

    def backup_recovery_center(self):
        self.header("💾 BACKUP / ROLLBACK","Create configuration backups before major changes.")
        ttk.Button(self.page,text="CREATE CONFIG BACKUP",command=self.make_backup).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="VERIFY LAST BACKUP",command=self.verify_last_backup).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="BACKUP HISTORY",command=self.backup_history).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="BACKUP REPORT",command=self.backup_report).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="DETECT USB DRIVES",command=self.detect_recovery_usb).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="CREATE RECOVERY USB",command=self.create_recovery_usb).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="OPEN ZYNTRASEC DATA",command=lambda:run(f'explorer "{self.data_root}"')).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="CREATE WINDOWS RESTORE POINT",command=self.new_setup_backup).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="VIEW RESTORE POINTS",command=lambda:self._new_setup_ps("Get-ComputerRestorePoint | Select CreationTime,Description,RestorePointType,SequenceNumber | Format-Table -AutoSize", "RESTORE POINTS")).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="OPEN SYSTEM RESTORE",command=lambda:run("rstrui.exe")).pack(anchor="w",padx=8,pady=5)

    def detect_recovery_usb(self):
        script = r"""
Get-CimInstance Win32_DiskDrive | Where-Object { $_.MediaType -match 'Removable|External' -or $_.InterfaceType -eq 'USB' } |
    Select-Object Index,Model,InterfaceType,MediaType,@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}} |
    Format-Table -AutoSize
"""
        def done(r):
            text = r[1].strip() if r[1] else "No removable/USB disk detected."
            status = "SUCCESS" if r[0] == 0 and "No removable/USB disk detected." not in text else "REVIEW"
            self.output_show("BACKUP / ROLLBACK", "DETECT RECOVERY USB", text, status)
        self._async_job(lambda: ps(script,30), done, "DETECTING USB DRIVES...")

    def create_recovery_usb(self):
        if not messagebox.askyesno(
            "CREATE RECOVERY USB",
            "Windows Recovery Drive will open.\n\n"
            "Select the correct USB drive carefully. Creating a recovery drive can erase the USB drive.\n\n"
            "Continue?"
        ):
            return
        self.output_show(
            "BACKUP / ROLLBACK", "CREATE RECOVERY USB",
            "Launching the Windows Recovery Drive wizard.\n\n"
            "WARNING: Follow the wizard carefully; the selected USB may be erased.",
            "SUCCESS"
        )
        run("RecoveryDrive.exe")

    def _backup_dirs(self):
        try:
            return sorted([p for p in self.backup_root.iterdir() if p.is_dir() and p.name.startswith("ZYNTRASEC_Backup_")], key=lambda x:x.stat().st_mtime, reverse=True)
        except Exception:
            return []

    def verify_last_backup(self):
        dirs=self._backup_dirs()
        if not dirs:
            self.output_show("BACKUP / ROLLBACK","VERIFY LAST BACKUP","NO BACKUP FOUND", "REVIEW")
            return
        d=dirs[0]
        required=["README.txt","HKCU_Policies.reg","HKLM_Policies.reg","gpresult.html"]
        missing=[x for x in required if not (d/x).exists()]
        files=[x for x in d.iterdir() if x.is_file()]
        size=sum(x.stat().st_size for x in files)
        status="PASS" if not missing else "REVIEW"
        text=(f"LAST BACKUP : {d}\n"
              f"CREATED     : {datetime.fromtimestamp(d.stat().st_mtime):%Y-%m-%d %H:%M:%S}\n"
              f"FILES       : {len(files)}\n"
              f"SIZE        : {size/1024:.1f} KB\n"
              f"REQUIRED    : {len(required)-len(missing)}/{len(required)}\n"
              f"MISSING     : {', '.join(missing) if missing else 'NONE'}\n"
              f"VERIFY      : {status}")
        self.output_show("BACKUP / ROLLBACK","VERIFY LAST BACKUP",text,status)

    def backup_history(self):
        dirs=self._backup_dirs()
        if not dirs:
            text="NO ZYNTRASEC CONFIG BACKUPS FOUND."
        else:
            lines=[f"BACKUP COUNT : {len(dirs)}","", "NAME | CREATED | SIZE"]
            for d in dirs[:20]:
                try:
                    size=sum(x.stat().st_size for x in d.rglob('*') if x.is_file())
                    lines.append(f"{d.name} | {datetime.fromtimestamp(d.stat().st_mtime):%Y-%m-%d %H:%M:%S} | {size/1024:.1f} KB")
                except Exception as e:
                    lines.append(f"{d.name} | ERROR: {e}")
            text="\n".join(lines)
        self.output_show("BACKUP / ROLLBACK","BACKUP HISTORY",text,"SUCCESS")

    def backup_report(self):
        dirs=self._backup_dirs()
        latest=dirs[0] if dirs else None
        if latest:
            files=[x for x in latest.rglob('*') if x.is_file()]
            size=sum(x.stat().st_size for x in files)
            verify="PASS" if all((latest/x).exists() for x in ["README.txt","HKCU_Policies.reg","HKLM_Policies.reg","gpresult.html"]) else "REVIEW"
            text=(f"ZYNTRASEC // BACKUP REPORT\n\n"
                  f"TOTAL BACKUPS : {len(dirs)}\n"
                  f"LATEST        : {latest.name}\n"
                  f"FILES         : {len(files)}\n"
                  f"SIZE          : {size/1024:.1f} KB\n"
                  f"VERIFY STATUS  : {verify}\n"
                  f"LOCATION      : {latest}")
        else:
            text="ZYNTRASEC // BACKUP REPORT\n\nTOTAL BACKUPS : 0\nSTATUS        : NO BACKUP FOUND"
        self.output_show("BACKUP / ROLLBACK","BACKUP REPORT",text,"SUCCESS" if latest else "REVIEW")

    def baseline_center(self):
        self.header("📊 PC BASELINE","Save a read-only PC snapshot and compare future changes.")
        top=tk.Frame(self.page,bg=BG); top.pack(fill="x",padx=8,pady=5)
        ttk.Button(top,text="💾 SAVE PC BASELINE",command=self.save_pc_baseline).pack(side="left",padx=3)
        ttk.Button(top,text="🔄 REFRESH BASELINE",command=self.refresh_pc_baseline).pack(side="left",padx=3)
        ttk.Button(top,text="🔍 COMPARE WITH BASELINE",command=self.compare_pc_baseline).pack(side="left",padx=3)
        ttk.Button(top,text="📊 BASELINE REPORT",command=self.baseline_report).pack(side="left",padx=3)
        self.output_show("BASELINE","READY","Save a baseline first, then compare later to detect added, removed, or changed system items.","SUCCESS")

    def _collect_pc_baseline(self):
        """Collect a compact read-only snapshot for later comparison."""
        snap={"schema":2,"created":datetime.now().isoformat(),"computer":platform.node(),
              "user":os.environ.get("USERNAME"),"os":platform.platform()}
        for cmd,key in [("whoami","identity"),("hostname","hostname")]:
            rc,out=run(cmd,20); snap[key]=out.strip() if rc==0 else ""
        rc,out=ps(r'''$o=Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture,LastBootUpTime,InstallDate; $o | ConvertTo-Json -Compress''',30)
        try:snap["windows"]=json.loads(out.strip())
        except:snap["windows"]={"raw":out.strip()}
        scripts={
            "cpu":r'''Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | ConvertTo-Json -Compress''',
            "ram":r'''$m=Get-CimInstance Win32_PhysicalMemory; [pscustomobject]@{TotalGB=[math]::Round((($m|Measure-Object Capacity -Sum).Sum/1GB),2); Modules=@($m|ForEach-Object {[pscustomobject]@{Manufacturer=$_.Manufacturer;PartNumber=$_.PartNumber;CapacityGB=[math]::Round($_.Capacity/1GB,2);Speed=$_.Speed}})} | ConvertTo-Json -Compress -Depth 4''',
            "gpu":r'''Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,AdapterRAM | ConvertTo-Json -Compress''',
            "motherboard":r'''Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer,Product,SerialNumber | ConvertTo-Json -Compress''',
            "bios":r'''Get-CimInstance Win32_BIOS | Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate | ConvertTo-Json -Compress''',
            "network":r'''Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" | Select-Object Description,MACAddress,IPAddress,DefaultIPGateway,DNSServerSearchOrder | ConvertTo-Json -Compress''',
            "disks":r'''Get-CimInstance Win32_DiskDrive | Select-Object Model,SerialNumber,InterfaceType,MediaType,@{N="SizeGB";E={[math]::Round($_.Size/1GB,2)}} | ConvertTo-Json -Compress''',
        }
        for section,script in scripts.items():
            rc,out=ps(script,45)
            try:snap[section]=json.loads(out.strip()) if out.strip() else []
            except:snap[section]={"raw":out.strip()}
        rc,out=ps(r'''$roots=@("HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*","HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*","HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"); $a=@(); foreach($r in $roots){$a+=Get-ItemProperty $r -ErrorAction SilentlyContinue | Where-Object {$_.DisplayName} | ForEach-Object {[pscustomobject]@{Name=$_.DisplayName;Version=$_.DisplayVersion;Publisher=$_.Publisher}}}; $a | Sort-Object Name,Version -Unique | ConvertTo-Json -Compress -Depth 3''',60)
        try:snap["software"]=json.loads(out.strip()) if out.strip() else []
        except:snap["software"]=[]
        rc,out=ps(r'''Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue | Select-Object Name,Command,Location,User | Sort-Object Name,Command | ConvertTo-Json -Compress -Depth 4''',45)
        try:snap["startup"]=json.loads(out.strip()) if out.strip() else []
        except:snap["startup"]=[]
        return snap

    def save_pc_baseline(self):
        f=self.data_root/"PC_BASELINE.json"
        def work():
            snap=self._collect_pc_baseline(); f.write_text(json.dumps(snap,indent=2,default=str),encoding="utf-8"); return snap
        def done(snap):
            self.logit(f"PC BASELINE SAVED: {f}")
            self.output_show("BASELINE","SAVE",self._baseline_summary(snap),"SUCCESS")
        self._async_job(work,done,"SAVING PC BASELINE...")

    def refresh_pc_baseline(self):
        def work(): return self._collect_pc_baseline()
        def done(snap): self.output_show("BASELINE","REFRESH",self._baseline_summary(snap),"SUCCESS")
        self._async_job(work,done,"REFRESHING BASELINE SNAPSHOT...")

    def _baseline_summary(self,s):
        cpu=s.get("cpu",{})
        if isinstance(cpu,list): cpu=cpu[0] if cpu else {}
        ram=s.get("ram",{}) if isinstance(s.get("ram"),dict) else {}
        software=s.get("software",[]); startup=s.get("startup",[])
        w=s.get("windows",{}) if isinstance(s.get("windows"),dict) else {}
        return (f"PC BASELINE SNAPSHOT\n\n"
                f">> COMPUTER   : {s.get('computer','')}\n"
                f">> WINDOWS    : {w.get('Caption','')} | {w.get('Version','')} | Build {w.get('BuildNumber','')}\n"
                f">> CPU        : {cpu.get('Name','')}\n"
                f">> CORES/THR  : {cpu.get('NumberOfCores','?')} / {cpu.get('NumberOfLogicalProcessors','?')}\n"
                f">> RAM        : {ram.get('TotalGB','?')} GB\n"
                f">> SOFTWARE   : {len(software) if isinstance(software,list) else 0}\n"
                f">> STARTUP    : {len(startup) if isinstance(startup,list) else 0}\n"
                f">> CREATED    : {s.get('created','')}\n"
                f">> STATUS     : SNAPSHOT READY")

    def _baseline_keys(self,v):
        if not isinstance(v,list): return set()
        out=set()
        for x in v:
            if isinstance(x,dict):
                name=str(x.get('Name') or x.get('name') or '').strip().lower()
                ver=str(x.get('Version') or x.get('version') or '').strip().lower()
                cmd=str(x.get('Command') or x.get('command') or '').strip().lower()
                out.add((name,ver,cmd))
            else: out.add((str(x).strip().lower(),"",""))
        return out

    def compare_pc_baseline(self):
        f=self.data_root/"PC_BASELINE.json"
        if not f.exists():
            self.output_show("BASELINE","COMPARE","No baseline found. Use SAVE PC BASELINE first.","REVIEW"); return
        try: old=json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            self.output_show("BASELINE","COMPARE",str(e),"REVIEW"); return
        def work(): return self._collect_pc_baseline()
        def done(now):
            sections=[("software","SOFTWARE"),("startup","STARTUP"),("network","NETWORK"),("disks","DISKS")]
            lines=[f"BASELINE CREATED : {old.get('created','')}",f"CURRENT SNAPSHOT : {now.get('created','')}",""]
            total=0
            for key,label in sections:
                a=self._baseline_keys(old.get(key,[])); b=self._baseline_keys(now.get(key,[]))
                added=sorted(b-a); removed=sorted(a-b); changed=0
                if key=="software":
                    old_by={x[0]:x[1] for x in a}; new_by={x[0]:x[1] for x in b}
                    changed=sum(1 for n in (old_by.keys()&new_by.keys()) if old_by[n]!=new_by[n])
                total += len(added)+len(removed)+changed
                lines.append(f"[{label}] ADDED={len(added)} | REMOVED={len(removed)} | CHANGED={changed}")
                for item in added[:8]: lines.append(f"  + {item[0] or item[2]}")
                for item in removed[:8]: lines.append(f"  - {item[0] or item[2]}")
            ow=old.get('windows',{}); nw=now.get('windows',{})
            if ow.get('BuildNumber')!=nw.get('BuildNumber') or ow.get('Version')!=nw.get('Version'):
                lines.append(f"[WINDOWS] CHANGED : {ow.get('Version','')} Build {ow.get('BuildNumber','')} -> {nw.get('Version','')} Build {nw.get('BuildNumber','')}"); total+=1
            lines += ["",f">> TOTAL CHANGES : {total}",f">> STATUS        : {'CHANGES DETECTED' if total else 'NO CHANGES'}"]
            self.output_show("BASELINE","COMPARE","\n".join(lines),"SUCCESS")
        self._async_job(work,done,"COMPARING PC BASELINE...")

    def baseline_report(self):
        f=self.data_root/"PC_BASELINE.json"
        if not f.exists():
            self.output_show("BASELINE","REPORT","No baseline found. Use SAVE PC BASELINE first.","REVIEW"); return
        try:s=json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            self.output_show("BASELINE","REPORT",str(e),"REVIEW"); return
        self.output_show("BASELINE","REPORT",self._baseline_summary(s),"SUCCESS")

    def partition_manager(self):
        self.header("💽 STORAGE & PARTITION MANAGER","Custom GB / equal split. Equal Split can safely shrink the existing data volume after confirmation; EFI/System/Recovery are protected.")
        self.output_show("PARTITION MANAGER","READY","1) SCAN DISKS. 2) Set Equal parts. 3) AUTO EQUAL CREATE. Existing data and EFI/System/Recovery partitions are protected.")
        top=tk.Frame(self.page,bg=BG);top.pack(fill='x',padx=8,pady=5)
        ttk.Button(top,text="🔎 SCAN DISKS / PARTITIONS",command=self.partition_scan).pack(side='left',padx=3)
        ttk.Button(top,text="⚙ OPEN DISK MANAGEMENT",command=lambda:run("diskmgmt.msc")).pack(side='left',padx=3)
        form=tk.Frame(self.page,bg=PANEL);form.pack(fill='x',padx=8,pady=5)
        tk.Label(form,text="Disk",bg=PANEL,fg=TEXT).grid(row=0,column=0,padx=5,pady=5)
        self.part_disk=tk.StringVar(value="")
        self.part_disk_combo=ttk.Combobox(form,textvariable=self.part_disk,width=34,state="readonly",style="Partition.TCombobox")
        self.part_disk_combo.grid(row=0,column=1,padx=2)
        self.part_disk_combo.bind("<<ComboboxSelected>>", lambda e:self.partition_check_unallocated(silent=True))
        self.partitions_status=tk.Label(form,text="Partitions: scanning...",bg=PANEL,fg=TEXT,anchor="w")
        self.partitions_status.grid(row=1,column=0,columnspan=8,sticky="w",padx=5,pady=(0,4))
        tk.Label(form,text="Custom GB",bg=PANEL,fg=TEXT).grid(row=0,column=2,padx=5);self.part_gb=tk.Entry(form,width=10);self.part_gb.insert(0,'5');self.part_gb.grid(row=0,column=3)
        tk.Label(form,text="Equal parts",bg=PANEL,fg=TEXT).grid(row=0,column=4,padx=5);self.part_count=tk.Entry(form,width=8);self.part_count.insert(0,'2');self.part_count.grid(row=0,column=5)
        # Dedicated APPLY row: this button performs the confirmed resize/create operation.
        action=tk.Frame(self.page,bg=BG);action.pack(fill='x',padx=8,pady=(2,6))
        tk.Label(action,text="APPLY (CHANGES DISK)",bg=BG,fg='#ffcc00').pack(side='left',padx=6)
        ttk.Button(action,text="⚡ AUTO PARTITION",command=self.partition_auto).pack(side='left',padx=4)
        ttk.Button(action,text="🚀 AUTO EQUAL CREATE",command=self.partition_create_equal).pack(side='left',padx=4)
        # Automatically load the current disk/partition state when this page opens.
        # A lightweight background refresh keeps the dropdown and partition summary
        # synchronized after external changes (Disk Management, delete/create, etc.).
        self._partition_refresh_active = True
        self.partition_refresh_disks()
        self.after(2500, self._partition_dynamic_refresh)

    def _partition_dynamic_refresh(self):
        if not getattr(self, "_partition_refresh_active", False):
            return
        try:
            if not self.part_disk_combo.winfo_exists():
                return
        except Exception:
            return
        # This is a read-only background refresh. It does not use _job_running, so
        # users can start/perform other tasks while disk detection is running.
        # partition_refresh_disks has its own small lock to prevent overlapping reads.
        self.partition_refresh_disks()
        self.after(2500, self._partition_dynamic_refresh)

    def _selected_partition_disk(self):
        raw=self.part_disk.get().strip()
        if not raw:
            raise ValueError("No disk detected/selected. Click SCAN DISKS / PARTITIONS.")
        try:
            return int(raw.split("|")[0].strip())
        except Exception:
            raise ValueError("Invalid disk selection. Please choose a detected disk.")

    def partition_refresh_disks(self):
        # Background partition refresh is intentionally separate from _job_running.
        # It must never lock the whole application while PowerShell is reading disk
        # state; only real disk-changing actions should reserve _job_running.
        if getattr(self, "_partition_refresh_running", False):
            return
        self._partition_refresh_running = True
        def work():
            script="""
Update-HostStorageCache -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 150
$rows=@()
Get-Disk | ForEach-Object {
  $d=$_
  $parts=@(Get-Partition -DiskNumber $d.Number -ErrorAction SilentlyContinue | Where-Object { $_.Size -gt 0 } | Sort-Object Offset)
  $alloc=[uint64](($parts | Measure-Object -Property Size -Sum).Sum); if($null -eq $alloc){$alloc=0}
  $cursor=[uint64]0; $free=[uint64]0
  foreach($p in $parts){ $st=[uint64]$p.Offset; $en=$st+[uint64]$p.Size; if($st -gt $cursor){$free += $st-$cursor}; if($en -gt $cursor){$cursor=$en} }
  if([uint64]$d.Size -gt $cursor){$free += [uint64]$d.Size-$cursor}
  $plist=@()
  foreach($p in $parts){ $letter=if($p.DriveLetter){[string]$p.DriveLetter}else{"-"}; $ptype=if($p.Type){[string]$p.Type}else{"Basic"}; $plist += [pscustomobject]@{Number=[int]$p.PartitionNumber;DriveLetter=$letter;Size=[uint64]$p.Size;Type=$ptype} }
  $rows += [pscustomobject]@{Number=$d.Number;FriendlyName=$d.FriendlyName;OperationalStatus=$d.OperationalStatus;PartitionStyle=$d.PartitionStyle;Size=$d.Size;Allocated=$alloc;Unallocated=$free;IsBoot=$d.IsBoot;IsSystem=$d.IsSystem;Partitions=$plist}
}
$rows | ConvertTo-Json -Compress
"""
            return ps(script,30)
        def done(res):
            rc,out=res
            try:
                # PowerShell can return a non-zero code for harmless warnings while
                # still emitting a complete JSON disk inventory. Valid JSON inventory
                # is authoritative for this read-only scan.
                data=json.loads(out.strip()) if out.strip() else []
                if isinstance(data,dict): data=[data]
                vals=[]
                for d in data:
                    size=float(d.get("Size") or 0)/1024**3
                    alloc=float(d.get("Allocated") or 0)/1024**3
                    free=float(d.get("Unallocated") or 0)/1024**3
                    boot=" BOOT" if d.get("IsBoot") else ""
                    system=" SYSTEM" if d.get("IsSystem") else ""
                    plist=d.get('Partitions') or []
                    data_parts=[]
                    for p in plist:
                        letter=str(p.get('DriveLetter') or '-').strip()
                        ptype=str(p.get('Type') or '')
                        if letter != '-' and not any(x in ptype.lower() for x in ('reserved','recovery','system','efi')):
                            data_parts.append(p)
                    vals.append(f"{int(d.get('Number'))} | {d.get('FriendlyName') or 'Disk'} | {size:.2f} GB | {len(data_parts)} data partition(s) | Unallocated {free:.2f} GB{boot}{system}")
                    plist=d.get('Partitions') or []
                    visible=[]
                    for p in plist:
                        letter=str(p.get('DriveLetter') or '-').strip()
                        if letter != '-': visible.append(f"{letter}: {float(p.get('Size') or 0)/1024**3:.2f} GB")
                    # Show only normal drive-letter data partitions in the compact status.
                    # EFI/System/Recovery remain visible in the detailed scan output but are
                    # not counted as user/data partitions.
                    if visible:
                        self.partitions_status.config(text=f"Disk {int(d.get('Number'))}: {len(visible)} data partition(s)  |  " + "  |  ".join(visible))
                    else:
                        self.partitions_status.config(text=f"Disk {int(d.get('Number'))}: 0 data partitions")
                self.part_disk_combo["values"]=vals
                # Preserve the current selection during background refresh. Do not call
                # CHECK UNALLOCATED here: that used to overwrite the output console every
                # 3 seconds and made the live state look stale/wrong.
                current=self.part_disk.get().strip()
                if current in vals:
                    self.part_disk.set(current)
                elif vals:
                    self.part_disk.set(vals[0])
                else:
                    self.part_disk.set("")
                    self.output_show("PARTITION MANAGER","NO DISKS","No physical disks detected.","ATTENTION")
            except Exception as e:
                # A background refresh is read-only and must not overwrite a valid
                # partition screen with a transient PowerShell parsing/warning error.
                # Keep the existing disk list if one is already visible.
                try:
                    if not self.part_disk_combo["values"]:
                        self.output_show("PARTITION MANAGER","DISK DETECTION",
                                         "Unable to refresh disk inventory. Click SCAN DISKS / PARTITIONS to retry.\n\n"+str(e),"REVIEW")
                except Exception:
                    pass
        def worker():
            try:
                result=work()
                self.after(0, lambda r=result: finish(r))
            except Exception as e:
                self.after(0, lambda e=e: finish((1,str(e))))
        def finish(result):
            self._partition_refresh_running = False
            try:
                done(result)
            except Exception as e:
                try:
                    if not self.part_disk_combo["values"]:
                        self.output_show("PARTITION MANAGER","DISK DETECTION",
                                         "Unable to refresh disk inventory.\n\n"+str(e),"REVIEW")
                except Exception:
                    pass
        threading.Thread(target=worker,daemon=True).start()

    def partition_check_unallocated(self,silent=False):
        try: disk=self._selected_partition_disk()
        except Exception as e:
            if not silent: messagebox.showerror('Partition',str(e))
            return
        try:
            info=self._get_disk_unallocated(disk); total=info['Size']/1024**3; alloc=info['Allocated']/1024**3; free=info['Unallocated']/1024**3
            if free < 1.0:
                msg=f"DISK {disk}\nTotal: {total:.2f} GB\nAllocated: {alloc:.2f} GB\nUNALLOCATED: {free:.2f} GB\n\nNO USABLE UNALLOCATED SPACE.\nUse Disk Management to shrink an existing partition first, then scan again."
                self.output_show('PARTITION MANAGER','NO UNALLOCATED SPACE',msg,'ATTENTION')
                return
            msg=f"DISK {disk}\nTotal: {total:.2f} GB\nAllocated: {alloc:.2f} GB\nUNALLOCATED: {free:.2f} GB\n\nCustom partitions can be created only from this unallocated space."
            self.output_show('PARTITION MANAGER','UNALLOCATED SPACE',msg,'READY')
        except Exception as e:
            if not silent: messagebox.showerror('Partition',str(e))
            else: self.output_show('PARTITION MANAGER','DISK CHECK ERROR',str(e),'ERROR')

    def _partition_unallocated(self):
        rc,out=ps("Get-Disk | Select Number,PartitionStyle,OperationalStatus,Size,AllocatedSize,IsBoot,IsSystem | Format-Table -AutoSize; Get-Partition | Select DiskNumber,PartitionNumber,DriveLetter,Size,Type | Sort DiskNumber,PartitionNumber | Format-Table -AutoSize",60)
        return rc,out

    def partition_scan(self):
        # One scan operation updates BOTH the output console and the Disk dropdown.
        # This avoids the old race where the scan output finished but the dropdown
        # remained empty because its background refresh was still queued.
        def work():
            scan_script=("Get-Disk | Select Number,FriendlyName,PartitionStyle,OperationalStatus,Size,AllocatedSize,IsBoot,IsSystem | "
                         "Format-Table -AutoSize; Get-Partition | Select DiskNumber,PartitionNumber,DriveLetter,Size,Type | "
                         "Sort DiskNumber,PartitionNumber | Format-Table -AutoSize")
            rc_scan,out_scan=ps(scan_script,60)
            json_script="""
$rows=@()
Get-Disk | ForEach-Object {
  $d=$_
  $parts=@(Get-Partition -DiskNumber $d.Number -ErrorAction SilentlyContinue | Where-Object { $_.Size -gt 0 } | Sort-Object Offset)
  $alloc=[uint64](($parts | Measure-Object -Property Size -Sum).Sum); if($null -eq $alloc){$alloc=0}
  $cursor=[uint64]0; $free=[uint64]0
  foreach($p in $parts){ $st=[uint64]$p.Offset; $en=$st+[uint64]$p.Size; if($st -gt $cursor){$free += $st-$cursor}; if($en -gt $cursor){$cursor=$en} }
  if([uint64]$d.Size -gt $cursor){$free += [uint64]$d.Size-$cursor}
  $plist=@()
  foreach($p in $parts){ $letter=if($p.DriveLetter){[string]$p.DriveLetter}else{"-"}; $ptype=if($p.Type){[string]$p.Type}else{"Basic"}; $plist += [pscustomobject]@{Number=[int]$p.PartitionNumber;DriveLetter=$letter;Size=[uint64]$p.Size;Type=$ptype} }
  $rows += [pscustomobject]@{Number=$d.Number;FriendlyName=$d.FriendlyName;OperationalStatus=$d.OperationalStatus;PartitionStyle=$d.PartitionStyle;Size=$d.Size;Allocated=$alloc;Unallocated=$free;IsBoot=$d.IsBoot;IsSystem=$d.IsSystem;Partitions=$plist}
}
$rows | ConvertTo-Json -Compress
"""
            rc_json,out_json=ps(json_script,30)
            return rc_scan,out_scan,rc_json,out_json
        def done(res):
            rc_scan,out_scan,rc_json,out_json=res
            try:
                # Treat a valid disk JSON inventory as a successful detection even
                # when PowerShell also returned a non-fatal warning/diagnostic code.
                data=json.loads(out_json.strip()) if out_json.strip() else []
                if isinstance(data,dict): data=[data]
                vals=[]
                for d in data:
                    try: num=int(d.get("Number"))
                    except Exception: continue
                    size=float(d.get("Size") or 0)/1024**3
                    alloc=float(d.get("Allocated") or 0)/1024**3
                    free=float(d.get("Unallocated") or 0)/1024**3
                    boot=" BOOT" if d.get("IsBoot") else ""
                    system=" SYSTEM" if d.get("IsSystem") else ""
                    vals.append(f"{num} | {d.get('FriendlyName') or 'Disk'} | {size:.1f} GB | Unallocated {free:.1f} GB{boot}{system}")
                self.part_disk_combo["values"]=vals
                if vals:
                    self.part_disk.set(vals[0])
                else:
                    self.part_disk.set("")
                status="SUCCESS" if vals else ("REVIEW" if rc_scan!=0 else "SUCCESS")
                self.output_show("PARTITION MANAGER","DISK/PARTITION SCAN",
                                 (out_scan.strip() or "No disk scan output.")+"\n\nDROPDOWN DISKS: "+str(len(vals)),status)
                if vals:
                    self.partition_check_unallocated(silent=True)
            except Exception as e:
                self.part_disk_combo["values"]=()
                self.part_disk.set("")
                self.output_show("PARTITION MANAGER","DISK DETECTION ERROR",str(e),"ERROR")
        self._async_job(work,done,"SCANNING DISKS + REFRESHING DROPDOWN...")

    def _get_disk_unallocated(self,disk):
        # Do not rely only on Get-Disk.AllocatedSize. Calculate the real
        # unallocated bytes from the partition extents. This avoids stale or
        # misleading values after a shrink/rescan and correctly reports the
        # space actually available for New-Partition/DiskPart.
        script=f"""
$d=Get-Disk -Number {int(disk)} -ErrorAction Stop
$parts=@(Get-Partition -DiskNumber {int(disk)} -ErrorAction SilentlyContinue |
    Where-Object {{ $_.Size -gt 0 }} |
    Sort-Object Offset |
    Select-Object Offset,Size,PartitionNumber,DriveLetter,Type)
$allocated=[uint64](($parts | Measure-Object -Property Size -Sum).Sum)
if($null -eq $allocated){{$allocated=[uint64]0}}
$free=[uint64]0
$cursor=[uint64]0
foreach($p in $parts){{
    $start=[uint64]$p.Offset
    $end=$start+[uint64]$p.Size
    if($start -gt $cursor){{$free += ($start-$cursor)}}
    if($end -gt $cursor){{$cursor=$end}}
}}
if([uint64]$d.Size -gt $cursor){{$free += ([uint64]$d.Size-$cursor)}}
[pscustomobject]@{{Disk={int(disk)};Size=[uint64]$d.Size;Allocated=$allocated;Unallocated=$free;PartitionCount=$parts.Count}} | ConvertTo-Json -Compress
"""
        rc,out=ps(script,30)
        if rc!=0: raise RuntimeError(out.strip() or 'Cannot read disk.')
        return json.loads(out.strip().splitlines()[-1])

    def _parse_gb_value(self, raw):
        import re
        m=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(?:GB|GIB)?\s*', str(raw), re.I)
        if not m: raise ValueError('GB must be a number, e.g. 5 or 5 GB.')
        v=float(m.group(1))
        if v <= 0: raise ValueError('GB must be greater than 0.')
        return v

    def _partition_preview(self, sizes):
        try:
            disk=self._selected_partition_disk()
            sizes=[float(x) for x in sizes]
        except Exception as e:
            messagebox.showerror('Partition',str(e));return None
        if not sizes or any(x<=0 for x in sizes):
            messagebox.showerror('Partition','Partition size must be greater than 0 GB.');return None
        info=self._get_disk_unallocated(disk)
        free=max(0.0, float(info.get('Unallocated') or 0)/1024**3)
        total=sum(sizes)
        # Always show the actual requested size, even when creation is impossible.
        text=(f"DISK {disk}\n"
              f"Total: {float(info.get('Size') or 0)/1024**3:.2f} GB\n"
              f"Allocated: {float(info.get('Allocated') or 0)/1024**3:.2f} GB\n"
              f"Unallocated: {free:.2f} GB\n"
              f"Requested: {total:.2f} GB\n\n"
              "New partitions:\n"+"\n".join(f"  {i+1}. {x:.2f} GB" for i,x in enumerate(sizes)))
        if total>free+0.01:
            text += ("\n\nRESULT: CANNOT CREATE\n"
                     f"Requested {total:.2f} GB but only {free:.2f} GB is unallocated.\n\n"
                     "Existing partitions will NOT be shrunk automatically. "
                     "Use SHRINK / Disk Management to create unallocated space, then scan again.")
            self.output_show('PARTITION MANAGER','INSUFFICIENT UNALLOCATED SPACE',text,'ATTENTION')
            messagebox.showerror('Partition',f'Not enough UNALLOCATED space.\nRequested: {total:.2f} GB\nAvailable: {free:.2f} GB\n\nExisting partitions will NOT be shrunk automatically.')
            return None
        text += "\n\nRESULT: READY TO CREATE\nOnly unallocated space will be used. Existing partitions are not shrunk or formatted."
        self.output_show('PARTITION MANAGER','PREVIEW',text,'READY')
        return disk,sizes

    def partition_preview_custom(self):
        try:size=self._parse_gb_value(self.part_gb.get())
        except Exception as e:messagebox.showerror('Partition',str(e));return
        self._partition_preview([size])

    def _equal_split_plan(self, n):
        """Plan an equal split of the usable data area on a disk.

        Windows EFI/System/Recovery partitions are excluded. For the automatic
        equal-split workflow we intentionally support one existing data volume
        (normally C:) plus any unallocated space. That lets C: become partition
        #1 and creates the remaining equal partitions from newly unallocated
        space. Existing system/recovery partitions are never touched.
        """
        disk=self._selected_partition_disk()
        script=f"""
$d=Get-Disk -Number {disk} -ErrorAction Stop
$all=@(Get-Partition -DiskNumber {disk} -ErrorAction Stop | Where-Object {{ $_.Size -gt 0 }} | Sort-Object Offset)
$parts=@($all | Where-Object {{ $_.DriveLetter -and $_.Type -notmatch 'Reserved|Recovery|System' }} | ForEach-Object {{
  try {{
    $v=Get-PartitionSupportedSize -DiskNumber {disk} -PartitionNumber $_.PartitionNumber -ErrorAction Stop
    [pscustomobject]@{{PartitionNumber=$_.PartitionNumber;DriveLetter=$_.DriveLetter;Size=$_.Size;MinSize=$v.SizeMin;MaxSize=$v.SizeMax;Offset=$_.Offset}}
  }} catch {{ }}
}})
if($parts.Count -ne 1) {{
  [pscustomobject]@{{Status='UNSUPPORTED_LAYOUT';DataVolumes=$parts.Count}} | ConvertTo-Json -Compress
  exit 0
}}
$c=$parts[0]
# Calculate only the FREE EXTENT immediately following the existing data volume.
# This is important when Windows has a Recovery/MSR partition after C:. Total
# disk-free bytes may include space elsewhere that New-Partition cannot use for
# this split. The contiguous extent after C: is safe to shrink into and reuse.
$cEnd=[uint64]$c.Offset+[uint64]$c.Size
$next=@($all | Where-Object {{ [uint64]$_.Offset -gt $cEnd }} | Sort-Object Offset | Select-Object -First 1)
if($next.Count -gt 0) {{
  $contiguousFree=[math]::Max(0,[uint64]$next[0].Offset-$cEnd)
}} else {{
  $contiguousFree=[math]::Max(0,[uint64]$d.Size-$cEnd)
}}
$usable=[uint64]$c.Size+[uint64]$contiguousFree
$target=$usable/{n}
[pscustomobject]@{{Status='OK';Disk={disk};DriveLetter=$c.DriveLetter;PartitionNumber=$c.PartitionNumber;CurrentSize=$c.Size;MinSize=$c.MinSize;Free=$contiguousFree;Usable=$usable;Target=$target;NewCount={n-1};FollowingPartition=if($next.Count -gt 0){{[int]$next[0].PartitionNumber}}else{{0}}}} | ConvertTo-Json -Compress
"""
        rc,out=ps(script,60)
        if rc!=0 or not out.strip():
            raise RuntimeError(out.strip() or 'Unable to calculate equal split.')
        data=json.loads(out.strip().splitlines()[-1])
        if data.get('Status')!='OK':
            if data.get('Status')=='DATA_VOLUME_NOT_LAST':
                raise RuntimeError('AUTO EQUAL SPLIT layout is unsupported: ZYNTRASEC could not identify one existing data volume and a usable contiguous free extent. No partition was changed.')
            raise RuntimeError('AUTO EQUAL SPLIT currently supports one existing data volume (normally C:) plus unallocated space. EFI/System/Recovery partitions are excluded.')
        target=float(data['Target'])/1024**3
        current=float(data['CurrentSize'])/1024**3
        free=float(data['Free'])/1024**3
        min_size=float(data['MinSize'])/1024**3
        shrink=max(0.0,current-target)
        if target > current + 0.01:
            raise RuntimeError(f"Automatic equal split would require extending {data.get('DriveLetter')}: first; this safe workflow only performs a shrink + create operation.")
        if target < min_size:
            raise RuntimeError(f"Windows minimum size for {data.get('DriveLetter')}: is {min_size:.2f} GB, so {n} equal partitions cannot be created safely.")
        return data, target, current, free, shrink

    def partition_preview_equal(self):
        try:
            n=int(self.part_count.get())
        except Exception:
            messagebox.showerror('Partition','Equal parts must be an integer.');return
        if n<1 or n>32:
            messagebox.showerror('Partition','Choose 1–32 parts.');return
        if n==1:
            self.output_show('PARTITION MANAGER','EQUAL SPLIT','Equal parts = 1 means no split is required. The existing data volume is already one partition.','READY')
            return
        try:
            data,target,current,free,shrink=self._equal_split_plan(n)
        except Exception as e:
            self.output_show('PARTITION MANAGER','EQUAL SPLIT BLOCKED',str(e),'BLOCKED')
            messagebox.showwarning('Equal Split Blocked',str(e));return
        text=(f"DISK {data['Disk']}\n"
              f"EXISTING DATA VOLUME: {data['DriveLetter']}:\n"
              f"CURRENT CANDIDATE SIZE: {current:.2f} GB\n"
              f"UNALLOCATED: {free:.2f} GB\n"
              f"USABLE DATA CAPACITY: {float(data['Usable'])/1024**3:.2f} GB\n\n"
              f"EQUAL PARTS: {n}\n"
              f"TARGET SIZE EACH: {target:.2f} GB\n"
              f"SHRINK {data['DriveLetter']}: BY: {shrink:.2f} GB\n"
              f"NEW PARTITIONS TO CREATE: {n-1}\n\n"
              "PARTITION 1 = existing data volume resized to the target size.\n"
              "PARTITIONS 2..N = newly created from the released/unallocated space.\n"
              "EFI / System / Recovery partitions are NOT touched.\n\n"
              "RESULT: READY FOR EQUAL SPLIT\n"
              "Preview only. No partition changes have been made.")
        self.output_show('PARTITION MANAGER','EQUAL SPLIT PREVIEW',text,'READY')

    def partition_create_custom(self):
        """Create a custom-sized partition using the existing safe auto workflow."""
        try:
            size = self._parse_gb_value(self.part_gb.get())
        except Exception as e:
            messagebox.showerror("Partition", str(e))
            return
        if size <= 0:
            messagebox.showerror("Partition", "GB must be greater than 0.")
            return
        self.partition_auto([size])

    def partition_create_equal(self):
        self.output_show('PARTITION MANAGER','APPLY EQUAL SPLIT','CREATE action started. Preview is not being run. Waiting for confirmation...','CONFIRM')
        try:
            n=int(self.part_count.get())
        except Exception:
            messagebox.showerror('Partition','Equal parts must be an integer.');return
        if n<1 or n>32:
            messagebox.showerror('Partition','Choose 1–32 parts.');return
        if not is_admin():
            messagebox.showwarning('Admin required','Run ZYNTRASEC as Administrator.');return
        if n==1:
            self.output_show('PARTITION MANAGER','EQUAL SPLIT','Equal parts = 1: no split required.','READY');return
        try:
            data,target,current,free,shrink=self._equal_split_plan(n)
        except Exception as e:
            self.output_show('PARTITION MANAGER','EQUAL SPLIT BLOCKED',str(e),'BLOCKED')
            messagebox.showwarning('Equal Split Blocked',str(e));return
        confirm=(f'EQUAL SPLIT DISK {data["Disk"]}\n\n'
                 f'Existing volume: {data["DriveLetter"]}:\n'
                 f'Current size: {current:.2f} GB\n'
                 f'Final size of {data["DriveLetter"]}: {target:.2f} GB\n'
                 f'Shrink: {shrink:.2f} GB\n\n'
                 f'Number of equal partitions: {n}\n'
                 f'Each partition: ~{target:.2f} GB\n'
                 f'New partitions to create: {n-1}\n\n'
                 'EFI / System / Recovery partitions will NOT be modified.\n'
                 'The existing data volume will be resized. Back up important data first.\n\n'
                 'Continue?')
        if not messagebox.askyesno('CONFIRM EQUAL SPLIT',confirm): return
        disk=int(data['Disk']); drive=str(data['DriveLetter']); target_bytes=int(target*1024**3)
        new_count=n-1
        def work():
            # Re-read live state immediately before changing anything.
            read_script=(f"$v=Get-Partition -DriveLetter '{drive}' -ErrorAction Stop; "
                         f"$x=Get-PartitionSupportedSize -DiskNumber {disk} -PartitionNumber $v.PartitionNumber -ErrorAction Stop; "
                         f"[pscustomobject]@{{Size=$v.Size;Min=$x.SizeMin;Max=$x.SizeMax}} | ConvertTo-Json -Compress")
            r0,o0=ps(read_script,60)
            if r0!=0: return {'stage':'READ','rc':r0,'out':o0}
            try:
                live=json.loads(o0.strip().splitlines()[-1]); live_size=int(live['Size']); live_min=int(live['Min'])
            except Exception:
                return {'stage':'READ','rc':1,'out':'Could not read live partition size.\n'+o0}
            if target_bytes < live_min:
                return {'stage':'RESIZE','rc':1,'out':f'Target size {target/1:.2f} GB is below Windows minimum supported size ({live_min/1024**3:.2f} GB).'}

            # Step 1: shrink C: only. No format/delete operation is performed.
            if live_size > target_bytes + 1024*1024:
                r1,o1=ps(f"Resize-Partition -DriveLetter '{drive}' -Size {target_bytes} -ErrorAction Stop | Format-List | Out-String",300)
                if r1!=0:
                    return {'stage':'RESIZE','rc':r1,'out':o1}
            else:
                r1,o1=0,'Source volume already at/under target; no shrink needed.'

            # Step 2: force a storage rescan and read the real unallocated space.
            scan_script=(f"Update-HostStorageCache -ErrorAction SilentlyContinue; "
                         f"Start-Sleep -Seconds 3; "
                         f"$d=Get-Disk -Number {disk} -ErrorAction Stop; "
                         f"[pscustomobject]@{{Size=$d.Size;Allocated=$d.AllocatedSize;Free=($d.Size-$d.AllocatedSize)}} | ConvertTo-Json -Compress")
            r2,o2=ps(scan_script,60)
            if r2!=0:
                return {'stage':'RESCAN','rc':r2,'out':o2}
            try:
                ds=json.loads(o2.strip().splitlines()[-1]); free_now=int(ds['Free'])
            except Exception:
                return {'stage':'RESCAN','rc':1,'out':'Could not read unallocated space after shrink.\n'+o2}

            # Step 3: create each new partition from the live unallocated space.
            # Windows can reject a byte-exact size because of partition alignment.
            # For the FINAL partition, therefore use -UseMaximumSize. This is the
            # most reliable way to consume the actual remaining unallocated extent.
            created=[]
            remaining=new_count
            for i in range(new_count):
                is_final = (remaining == 1)
                if is_final:
                    # First try Storage Spaces/Storage module. If Windows rejects the
                    # PowerShell create operation, fall back to DiskPart. Both paths
                    # operate ONLY on the currently unallocated area of this selected
                    # disk; no existing partition is deleted or formatted.
                    script=(f"Update-HostStorageCache -ErrorAction SilentlyContinue; "
                            f"Start-Sleep -Seconds 2; "
                            f"try {{ "
                            f"$p=New-Partition -DiskNumber {disk} -UseMaximumSize -AssignDriveLetter -ErrorAction Stop; "
                            f"[pscustomobject]@{{Method='PowerShell';PartitionNumber=$p.PartitionNumber;DriveLetter=$p.DriveLetter;SizeGB=([math]::Round($p.Size/1GB,2))}} | ConvertTo-Json -Compress "
                            f"}} catch {{ "
                            f"$msg=$_.Exception.Message; "
                            f"$dp=@('select disk {disk}','create partition primary','assign') -join [Environment]::NewLine; "
                            f"$dpOut=$dp | diskpart.exe 2>&1 | Out-String; "
                            f"if($LASTEXITCODE -ne 0){{ throw ('PowerShell create failed: ' + $msg + '\nDiskPart fallback failed:\n' + $dpOut) }}; "
                            f"Start-Sleep -Seconds 2; Update-HostStorageCache -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; "
                            f"$ps=@(Get-Partition -DiskNumber {disk} -ErrorAction Stop | Sort-Object PartitionNumber | Select-Object -Last 1); "
                            f"if($ps.Count -eq 0){{ throw ('PowerShell create failed: ' + $msg + '\nDiskPart reported success but no new partition was detected.') }}; "
                            f"$q=$ps[0]; "
                            f"[pscustomobject]@{{Method='DiskPart fallback';PartitionNumber=$q.PartitionNumber;DriveLetter=$q.DriveLetter;SizeGB=([math]::Round($q.Size/1GB,2));PowerShellError=$msg}} | ConvertTo-Json -Compress "
                            f"}}")
                else:
                    # Leave enough aligned space for the remaining partitions.
                    script=(f"Update-HostStorageCache -ErrorAction SilentlyContinue; "
                            f"Start-Sleep -Seconds 2; "
                            f"$d=Get-Disk -Number {disk} -ErrorAction Stop; "
                            f"$free=[uint64]$d.Size-[uint64]$d.AllocatedSize; "
                            f"$size=[uint64]([math]::Floor((([double]$free/[double]{remaining})/1MB)))*1MB; "
                            f"if($size -lt 64MB){{throw ('Not enough unallocated space remains for partition {i+2}. Available: ' + [math]::Round(([double]$free/1GB),2) + ' GB')}}; "
                            f"$p=New-Partition -DiskNumber {disk} -Size ([uint64]$size) -AssignDriveLetter -ErrorAction Stop; "
                            f"[pscustomobject]@{{PartitionNumber=$p.PartitionNumber;DriveLetter=$p.DriveLetter;SizeGB=([math]::Round($p.Size/1GB,2))}} | ConvertTo-Json -Compress")
                rr,oo=ps(script,300)
                created.append((rr,oo))
                if rr!=0:
                    break
                remaining-=1
            return {'stage':'DONE','resize':(r1,o1),'created':created,'rescan':o2}
        def done(res):
            if res.get('stage') in ('READ','RESIZE','RESCAN'):
                self.output_show('PARTITION MANAGER','EQUAL SPLIT FAILED',
                                 f"Stage: {res.get('stage')}\nExit code: {res.get('rc')}\n\n{res.get('out','')}", 'REVIEW')
                messagebox.showerror('Equal Split Failed',f"{res.get('stage')} failed.\n\n{res.get('out','')[-1800:]}")
                return
            created=res.get('created',[]); ok=sum(1 for rc,_ in created if rc==0)
            text=(f"EQUAL SPLIT: {n} PARTITIONS\n\n"
                  f"RESIZED {drive}: TO ~{target:.2f} GB\n"
                  f"NEW PARTITIONS CREATED: {ok}/{new_count}\n\n")
            for i,(rc,out) in enumerate(created,2):
                text += f"PARTITION {i}: {'CREATED' if rc==0 else 'FAILED'}\n{out[-2500:]}\n\n"
            # Final live verification: confirm the released space was allocated.
            try:
                vr,vo=ps(f"$d=Get-Disk -Number {disk} -ErrorAction Stop; [pscustomobject]@{{Allocated=$d.AllocatedSize;Free=($d.Size-$d.AllocatedSize)}} | ConvertTo-Json -Compress",30)
                if vr==0 and vo.strip():
                    vd=json.loads(vo.strip().splitlines()[-1])
                    text += f"\nFINAL DISK VERIFY\nAllocated: {float(vd['Allocated'])/1024**3:.2f} GB\nUnallocated: {float(vd['Free'])/1024**3:.2f} GB\n"
            except Exception:
                pass
            status='COMPLETE' if ok==new_count else 'REVIEW'
            self.output_show('PARTITION MANAGER','EQUAL SPLIT',text,status)
            self.partition_refresh_disks()
            if ok==new_count:
                messagebox.showinfo('Equal Split Complete',f'{n} equal partitions created successfully.\n\nEach target was approximately {target:.2f} GB.\n\nThe remaining unallocated space was converted into the new partition(s).\n\nEFI/System/Recovery were not modified.')
            else:
                messagebox.showwarning('Equal Split Review',f'{ok} of {new_count} new partitions were created. Check the output and Disk Management.')
        self._async_job(work,done,'EQUAL SPLIT: RESIZING + CREATING...')

    def partition_auto(self, requested_sizes=None):
        try:
            disk=self._selected_partition_disk()
            if requested_sizes is None:
                requested_sizes=[self._parse_gb_value(self.part_gb.get())]
            requested_sizes=[float(x) for x in requested_sizes]
            if not requested_sizes or any(x<=0 for x in requested_sizes): raise ValueError("Partition size must be greater than 0 GB.")
        except Exception as e:
            messagebox.showerror('Auto Partition',str(e)); return
        if not is_admin():
            messagebox.showwarning('Admin required','Run ZYNTRASEC as Administrator.'); return
        try:
            info=self._get_disk_unallocated(disk); free=float(info.get('Unallocated') or 0)/1024**3
        except Exception as e:
            messagebox.showerror('Auto Partition',str(e)); return
        total_needed=sum(requested_sizes)
        need=max(0.0,total_needed-free)
        # Reserve a small alignment/metadata margin during Windows volume resize.
        safety_gb=0.0625  # 64 MiB
        shrink_need=max(0.0,need+safety_gb)
        if need <= 0.01:
            confirm=(f'Disk {disk} has {free:.2f} GB unallocated.\n\n'
                     f'Create {len(requested_sizes)} partition(s):\n'+"\n".join(f'{x:.2f} GB' for x in requested_sizes)+
                     '\n\nOnly unallocated space will be used.')
            if not messagebox.askyesno('AUTO PARTITION',confirm): return
            def work_existing_free():
                # Use the live unallocated extent. For a single requested partition,
                # -UseMaximumSize avoids Windows alignment/metadata rounding failures
                # when Disk Management displays e.g. 5.00 GB but the exact byte count
                # is a few MB short of the requested GiB value.
                parts=[]
                if len(requested_sizes)==1:
                    script=(f"Update-HostStorageCache -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; "
                            f"$p=New-Partition -DiskNumber {disk} -UseMaximumSize -AssignDriveLetter -ErrorAction Stop; "
                            f"[pscustomobject]@{{PartitionNumber=$p.PartitionNumber;DriveLetter=$p.DriveLetter;SizeGB=([math]::Round($p.Size/1GB,2))}} | ConvertTo-Json -Compress")
                    return ps(script,180)
                for i,x in enumerate(requested_sizes):
                    is_final=(i==len(requested_sizes)-1)
                    if is_final:
                        script=(f"Update-HostStorageCache -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; "
                                f"$p=New-Partition -DiskNumber {disk} -UseMaximumSize -AssignDriveLetter -ErrorAction Stop; "
                                f"[pscustomobject]@{{PartitionNumber=$p.PartitionNumber;DriveLetter=$p.DriveLetter;SizeGB=([math]::Round($p.Size/1GB,2))}} | ConvertTo-Json -Compress")
                    else:
                        script=(f"Update-HostStorageCache -ErrorAction SilentlyContinue; Start-Sleep -Seconds 1; "
                                f"$p=New-Partition -DiskNumber {disk} -Size {int(x*1024**3)} -AssignDriveLetter -ErrorAction Stop; "
                                f"[pscustomobject]@{{PartitionNumber=$p.PartitionNumber;DriveLetter=$p.DriveLetter;SizeGB=([math]::Round($p.Size/1GB,2))}} | ConvertTo-Json -Compress")
                    rc_p,out_p=ps(script,180)
                    parts.append((rc_p,out_p))
                    if rc_p!=0: break
                return (0,'\n'.join(o for _,o in parts)) if parts and all(r==0 for r,_ in parts) else next((r,o) for r,o in parts if r!=0)
            def done_existing(res):
                rc_p,out_p=res
                status='COMPLETE' if rc_p==0 else 'REVIEW'
                text='CREATE PARTITION(S): '+('SUCCESS\n' if rc_p==0 else 'FAILED\n')+(out_p or '')
                try:
                    vr,vo=ps(f"$d=Get-Disk -Number {disk} -ErrorAction Stop; [pscustomobject]@{{Allocated=$d.AllocatedSize;Free=($d.Size-$d.AllocatedSize)}} | ConvertTo-Json -Compress",30)
                    if vr==0 and vo.strip():
                        vd=json.loads(vo.strip().splitlines()[-1])
                        text += f"\nFINAL DISK VERIFY\nAllocated: {float(vd['Allocated'])/1024**3:.2f} GB\nUnallocated: {float(vd['Free'])/1024**3:.2f} GB\n"
                except Exception: pass
                self.output_show('PARTITION MANAGER','AUTO PARTITION',text,status)
                self.partition_refresh_disks()
                if rc_p!=0:
                    messagebox.showerror('Auto Partition',out_p or 'Partition creation failed.')
            self._async_job(work_existing_free,done_existing,'AUTO PARTITION: ALLOCATING UNALLOCATED SPACE...')
            return
        script=f"""$need=[math]::Ceiling({shrink_need}*1GB)
$candidates=@(Get-Partition -DiskNumber {disk} -ErrorAction Stop | Where-Object {{ $_.DriveLetter -and $_.Type -notmatch 'Reserved|Recovery|System' }} | ForEach-Object {{
  try {{ $v=Get-PartitionSupportedSize -DiskNumber {disk} -PartitionNumber $_.PartitionNumber -ErrorAction Stop; [pscustomobject]@{{PartitionNumber=$_.PartitionNumber;DriveLetter=$_.DriveLetter;Size=$_.Size;MinSize=$v.SizeMin;Shrinkable=($_.Size-$v.SizeMin)}} }} catch {{ }}
}} | Where-Object {{ $_.Shrinkable -ge $need }} | Sort-Object Shrinkable -Descending)
if(-not $candidates) {{ Write-Output 'NO_SHRINKABLE_VOLUME'; exit 2 }}
$c=$candidates[0]
[pscustomobject]@{{PartitionNumber=$c.PartitionNumber;DriveLetter=$c.DriveLetter;CurrentSizeGB=[math]::Round($c.Size/1GB,2);MinSizeGB=[math]::Round($c.MinSize/1GB,2);ShrinkByGB=[math]::Round($need/1GB,2)}} | ConvertTo-Json -Compress"""
        rc,out=ps(script,60)
        if rc!=0 or not out.strip() or 'NO_SHRINKABLE_VOLUME' in out:
            msg=(f'Need {need:.2f} GB additional unallocated space, but Windows did not report a suitable shrinkable volume.\n\n'
                 'No partition was changed. Try Disk Management to shrink a suitable volume.')
            self.output_show('PARTITION MANAGER','AUTO PARTITION BLOCKED',msg,'ATTENTION')
            messagebox.showerror('Auto Partition',msg); return
        try: cand=json.loads(out.strip().splitlines()[-1])
        except Exception:
            messagebox.showerror('Auto Partition','Could not read shrinkable volume information. No changes were made.'); return
        confirm=(f'AUTO PARTITION\n\nDisk {disk}\nSource volume: {cand.get("DriveLetter")}:\n'
                 f'Current size: {float(cand.get("CurrentSizeGB",0)):.2f} GB\n'
                 f'Automatic shrink: {float(cand.get("ShrinkByGB",need)):.2f} GB\n'
                 f'New partition(s):\n'+"\n".join(f'  {i+1}. {x:.2f} GB' for i,x in enumerate(requested_sizes))+
                 '\n\nThe source volume will be shrunk automatically. Windows may refuse if files cannot be moved.\n'
                 'Backup important data before continuing.\n\nContinue?')
        if not messagebox.askyesno('CONFIRM AUTO PARTITION',confirm): return
        def work():
            # Re-read the source volume size immediately before resize to avoid stale-size races.
            drive=cand.get('DriveLetter')
            rc0,out0=ps(f"$v=Get-Partition -DriveLetter '{drive}' -ErrorAction Stop; [pscustomobject]@{{Size=$v.Size}} | ConvertTo-Json -Compress",30)
            if rc0!=0: return {'shrink':(rc0,out0),'create':None}
            try: current=int(json.loads(out0.strip().splitlines()[-1])['Size'])
            except Exception: return {'shrink':(1,'Could not read current source partition size.'),'create':None}
            shrink_bytes=int(math.ceil(shrink_need*1024**3)); new_size=current-shrink_bytes
            script1=f"Resize-Partition -DriveLetter '{drive}' -Size {new_size} -ErrorAction Stop | Out-String"
            rc1,out1=ps(script1,180)
            if rc1!=0: return {'shrink':(rc1,out1),'create':None}
            # Refresh storage state and verify the real unallocated extent before creating partitions.
            requested_bytes=sum(int(x*1024**3) for x in requested_sizes)
            script2=(f"Start-Sleep -Seconds 2; Update-HostStorageCache -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; "
                     f"$d=Get-Disk -Number {disk} -ErrorAction Stop; $free=[uint64]($d.Size-$d.AllocatedSize); "
                     f"if($free -lt {requested_bytes}){{ throw ('Not enough available capacity after shrink. Required: ' + [math]::Round({requested_bytes}/1GB,2) + ' GB; Available: ' + [math]::Round($free/1GB,2) + ' GB') }}; "
                     f"$parts=@(); "+"; ".join([
                         (f"$p=New-Partition -DiskNumber {disk} -UseMaximumSize -AssignDriveLetter -ErrorAction Stop; $parts += ($p | Format-List | Out-String)" if i==len(requested_sizes)-1 else f"$p=New-Partition -DiskNumber {disk} -Size {int(x*1024**3)} -AssignDriveLetter -ErrorAction Stop; $parts += ($p | Format-List | Out-String)")
                         for i,x in enumerate(requested_sizes)
                     ])+"; $parts -join '\n'")
            rc2,out2=ps(script2,180)
            return {'shrink':(rc1,out1),'create':(rc2,out2)}
        def done(res):
            sr=res.get('shrink'); cr=res.get('create')
            if sr and sr[0]!=0:
                self.output_show('PARTITION MANAGER','AUTO PARTITION FAILED','Automatic shrink failed.\n\n'+(sr[1] or ''),'REVIEW'); return
            if not cr:
                self.output_show('PARTITION MANAGER','AUTO PARTITION FAILED','No create step was completed.','REVIEW'); return
            status='COMPLETE' if cr[0]==0 else 'REVIEW'
            text='AUTOMATIC SHRINK: SUCCESS\n'+(sr[1] or '')
            text += f'\n\nCREATE PARTITION(S): {"SUCCESS" if cr[0]==0 else "FAILED"}\n'
            text += (cr[1] or '') + '\n'
            try:
                vr,vo=ps(f"$d=Get-Disk -Number {disk} -ErrorAction Stop; [pscustomobject]@{{Allocated=$d.AllocatedSize;Free=($d.Size-$d.AllocatedSize)}} | ConvertTo-Json -Compress",30)
                if vr==0 and vo.strip():
                    vd=json.loads(vo.strip().splitlines()[-1])
                    text += f'\nFINAL VERIFY: {"SUCCESS" if cr[0]==0 else "REVIEW"}\nAllocated: {float(vd["Allocated"])/1024**3:.2f} GB\nUnallocated: {float(vd["Free"])/1024**3:.2f} GB\n'
            except Exception: pass
            self.output_show('PARTITION MANAGER','AUTO PARTITION',text,status)
            self.partition_refresh_disks()
        self._async_job(work,done,'AUTO PARTITION: SHRINKING + CREATING...')

    def manage(self):
        self.header("🛠 MANAGE EXISTING PC","Audit current configuration, select exactly what you want to change, then verify.")
        ttk.Button(self.page,text="🔎 RUN FULL SCAN",command=self.scan).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="💾 BACKUP BEFORE CHANGES",command=self.make_backup).pack(anchor="w",padx=8,pady=4)
        self.output_show("MANAGE", "READY", "MANAGE MODE\n\nUse the left modules to make targeted changes.\n\nWorkflow: BACKUP → APPLY → VERIFY → REPORT\n\nNo mass registry reset or mass ACL reset is performed.")

    def scan(self):
        self.header("🔎 FULL SYSTEM SCAN","Read-only audit.")
        self.output_show("FULL SYSTEM SCAN", "START", "SCAN STARTED...", "RUNNING")
        def work():
            data=[]
            rc,o=run("whoami",20);data.append(("Identity","OK" if rc==0 else "CHECK",o.strip()))
            rc,o=ps("(Get-NetFirewallProfile | Where Enabled -eq $false).Count",20);data.append(("Firewall","OK" if o.strip()=="0" else "REVIEW",o.strip()))
            rc,o=ps("(Get-MpComputerStatus).RealTimeProtectionEnabled",20);data.append(("Defender","OK" if "True" in o else "REVIEW",o.strip()))
            rc,o=ps("(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System').EnableLUA",20);data.append(("UAC","OK" if o.strip()=="1" else "REVIEW",o.strip()))
            for d in ["C:\\","D:\\"]:
                try:u=shutil.disk_usage(d);data.append((d,"OK" if u.free>50*1024**3 else "LOW",f"{human(u.free)} free / {human(u.total)} total"))
                except:pass
            return data
        def done(data):
            text="\n".join(f"{a:<18} {b:<10} {c}" for a,b,c in data)
            self.output_show("FULL SYSTEM SCAN", "SCAN", text, "COMPLETE")
            for a,b,c in data:self.logit(f"{a}: {b} {c}")
        self._async_job(work,done,"SCANNING...")
        ttk.Button(self.page,text="BACK",command=self.manage).pack(anchor="w",padx=8,pady=4)

    def _safe_close(self):
        if getattr(self, "_closing", False):
            return
        self._closing=True
        try:
            # Cancel known repeating UI callbacks first.
            for attr in ("_perf_after", "_partition_refresh_after"):
                aid=getattr(self, attr, None)
                if aid:
                    try:self.after_cancel(aid)
                    except Exception:pass
            # Stop only processes launched by ZYNTRASEC itself.
            _stop_owned_processes()
        finally:
            self.destroy()

    def _preferred_local_user(self, rows):
        """Choose a safe default target: enabled standard local user, preferring pcuser.
        The currently signed-in Administrator is never the default when a standard local user exists.
        """
        enabled=[r for r in rows if r.get("enabled", "").lower()=="true"]
        pcuser=next((r for r in enabled if r.get("name", "").lower()=="pcuser" and r.get("admin", "").lower()!="true"), None)
        if pcuser: return pcuser["name"]
        standard=next((r for r in enabled if r.get("admin", "").lower()!="true"), None)
        if standard: return standard["name"]
        current=os.environ.get("USERNAME", "")
        if current in [r.get("name") for r in enabled]: return current
        return enabled[0]["name"] if enabled else ""


    def refresh_target_users(self):
        try:
            rows=self._discover_user_rows()
            self._target_rows={r["name"]:r for r in rows}
            names=[r["name"] for r in rows if r["enabled"].lower()=="true"]
            self.tuser["values"]=names
            preferred=self._preferred_local_user(rows)
            if preferred in names:
                self.tuser.set(preferred)
            elif names:
                self.tuser.set(names[0])
            self.update_target_info()
            if hasattr(self,"tuser"):
                self.tuser.bind("<<ComboboxSelected>>",lambda e:self.update_target_info())
        except Exception as e:
            self.tuser["values"]=[]
            self.target_info.config(text="USER DISCOVERY ERROR",fg=RED)

    def update_target_info(self):
        name=self.tuser.get().strip()
        row=getattr(self,"_target_rows",{}).get(name)
        if not row:
            self.target_info.config(text="No user selected",fg=MUTED)
            return
        role="ADMINISTRATOR" if row["admin"].lower()=="true" else "STANDARD USER"
        self.target_info.config(text=f"{role}  |  {'ENABLED' if row['enabled'].lower()=='true' else 'DISABLED'}",fg=GREEN)

    def _resolve_user(self, username):
        username=(username or "").strip()
        if not username:
            raise RuntimeError("Target username is empty.")

        # Use the exact account already discovered by the Users/Policies dropdown.
        for attr in ("_policy_rows","_target_rows"):
            rows=getattr(self,attr,{})
            row=rows.get(username)
            if row and row.get("sid"):
                sid=row["sid"]
                profile=row.get("profile","")
                if profile and os.path.isfile(os.path.join(profile,"NTUSER.DAT")):
                    return sid,profile

        safe=username.replace("'","''")
        code=(
            "$u=Get-LocalUser -Name '"+safe+"' -ErrorAction Stop; "
            "$sid=$u.SID.Value; "
            "$p=Get-CimInstance Win32_UserProfile | Where-Object {$_.SID -eq $sid} | Select-Object -First 1; "
            "if(-not $p){ throw 'PROFILE_NOT_FOUND' }; "
            "Write-Output ($sid+'|'+$p.LocalPath)"
        )
        rc,out=ps(code)
        if rc!=0 or "|" not in out:
            raise RuntimeError("Windows user could not be resolved: "+username)
        line=[x.strip() for x in out.splitlines() if "|" in x][-1]
        sid,profile=line.split("|",1)
        return sid,profile

    def _discover_user_rows(self):
        code = (
            "Get-LocalUser | ForEach-Object { "
            "$n=$_.Name; $sid=$_.SID.Value; $en=$_.Enabled; "
            "$isAdmin=$false; "
            "try { $isAdmin = [bool](Get-LocalGroupMember -Group 'Administrators' -ErrorAction Stop | "
            "Where-Object { $_.SID.Value -eq $sid }) } catch {}; "
            "$p=Get-CimInstance Win32_UserProfile | Where-Object SID -eq $sid | Select-Object -First 1; "
            "$path=if($p){$p.LocalPath}else{''}; "
            "'{0}|{1}|{2}|{3}|{4}' -f $n,$sid,$en,$isAdmin,$path }"
        )
        rc,out=ps(code)
        rows=[]
        for line in out.splitlines():
            p=line.strip().split("|",4)
            if len(p)==5 and p[0]:
                rows.append({"name":p[0],"sid":p[1],"enabled":p[2],"admin":p[3],"profile":p[4]})
        return rows

    def _user_hive(self, username):
        sid,profile=self._resolve_user(username)

        # First check the actual loaded HKEY_USERS hive using reg.exe directly.
        # This is the correct path when the target account is currently signed in.
        q=subprocess.run(
            ["reg.exe","query",fr"HKU\{sid}"],
            capture_output=True,text=True
        )
        if q.returncode==0:
            return sid,False,None

        # If the target is not signed in, temporarily load NTUSER.DAT.
        # If Windows reports ERROR_SHARING_VIOLATION, do not repeatedly retry;
        # explain that the profile is currently in use.
        hive_name=f"ZYNTRASEC_TEMP_{os.getpid()}"
        ntuser=os.path.join(profile,"NTUSER.DAT")
        if not os.path.isfile(ntuser):
            raise RuntimeError(f"NTUSER.DAT not found for {username}: {ntuser}")

        load=subprocess.run(
            ["reg.exe","load",fr"HKU\{hive_name}",ntuser],
            capture_output=True,text=True
        )
        if load.returncode!=0:
            msg=(load.stdout or "")+(load.stderr or "")
            if "being used by another process" in msg.lower() or "sharing violation" in msg.lower() or "error: 32" in msg.lower():
                raise RuntimeError(
                    f"The target account '{username}' is currently using its profile, "
                    "but Windows did not expose its hive under HKEY_USERS. "
                    "Sign out that user and try again, or use the user's currently "
                    "loaded hive from an Administrator session."
                )
            raise RuntimeError("Could not load the target user's registry hive.\n"+msg)
        return hive_name,True,sid

    def _close_user_hive(self, hive_name, was_loaded, original_sid=None):
        if was_loaded:
            subprocess.run(["reg.exe","unload",fr"HKU\{hive_name}"],
                           capture_output=True,text=True)

    def _policy_map(self):
        return {
            "CMD":("Software\\Policies\\Microsoft\\Windows\\System","DisableCMD"),
            "Registry Editor":("Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System","DisableRegistryTools"),
            "Task Manager":("Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System","DisableTaskMgr"),
            "Control Panel / Settings":("Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer","NoControlPanel")
        }

    def _query_registry_value(self, root, sub, val):
        # Use reg.exe directly (no cmd.exe/shell quoting) and parse only the
        # requested REG_DWORD. This makes policy verification reliable.
        key=f"{root}\\{sub}"
        try:
            p=subprocess.run(["reg.exe","query",key,"/v",val],capture_output=True,text=True,timeout=30)
            if p.returncode!=0:
                return None
            for line in (p.stdout or "").splitlines():
                parts=line.strip().split()
                if len(parts)>=3 and parts[0].lower()==val.lower() and parts[1].upper()=="REG_DWORD":
                    raw=parts[2]
                    try:
                        return int(raw,16) if raw.lower().startswith("0x") else int(raw)
                    except ValueError:
                        return None
        except Exception:
            return None
        return None

    def _read_user_value(self, username, name):
        hive,loaded,orig_sid=self._user_hive(username)
        try:
            sub,val=self._policy_map()[name]
            return self._query_registry_value(f"HKU\\{hive}",sub,val)
        finally:
            self._close_user_hive(hive,loaded,orig_sid)

    def _read_machine_value(self, name):
        sub,val=self._policy_map()[name]
        # Read-only: never modify HKLM from the per-user policy controls.
        return self._query_registry_value("HKLM",sub,val)

    def _policy_audit_detail(self, username, name):
        uv=self._read_user_value(username,name)
        mv=self._read_machine_value(name)
        user_state="BLOCKED" if uv is not None and int(uv)!=0 else "ALLOWED"
        machine_state="BLOCKED" if mv is not None and int(mv)!=0 else "NOT SET"
        # This is a registry-level indication only; Group Policy precedence can vary.
        effective="BLOCKED" if user_state=="BLOCKED" or machine_state=="BLOCKED" else "ALLOWED"
        return {"user":uv,"machine":mv,"user_state":user_state,"machine_state":machine_state,"effective":effective}

    def _write_user_value(self, username, name, value):
        # Write only to the target user's loaded hive and fail loudly if reg.exe
        # cannot apply the requested change. The previous implementation ignored
        # reg.exe's return code, so a failed write could look like a successful
        # BLOCK operation until the later audit.
        hive,loaded,orig_sid=self._user_hive(username)
        try:
            sub,val=self._policy_map()[name]
            key=f"HKU\\{hive}\\{sub}"
            if value is None:
                args=["reg.exe","delete",key,"/v",val,"/f"]
                expected=None
            else:
                args=["reg.exe","add",key,"/v",val,"/t","REG_DWORD","/d",str(int(value)),"/f"]
                expected=int(value)
            p=subprocess.run(args,capture_output=True,text=True,timeout=30)
            output=((p.stdout or "")+(p.stderr or "")).strip()
            if p.returncode!=0:
                raise RuntimeError(f"Windows registry write failed for {name}.\n\n{output or 'reg.exe returned an error.'}")

            # Immediate raw verification before the hive is closed/unloaded.
            actual=self._query_registry_value(f"HKU\\{hive}",sub,val)
            if actual!=expected:
                raise RuntimeError(
                    f"Registry write did not verify for {name}.\n\n"
                    f"Expected value: {expected!r}\nActual value: {actual!r}\n"
                    f"Registry path: {key}\n"
                    f"reg.exe output: {output or '(none)'}"
                )
            return actual
        finally:
            self._close_user_hive(hive,loaded,orig_sid)

    def _rollback_values_direct(self, username, states):
        errors=[]
        for name,val in states.items():
            try:
                self._write_user_value(username,name,val)
            except Exception as e:
                errors.append(f"{name}: {e}")
        return errors

    def _set_user_restriction(self, username, name, disabled):
        # Only the target user's policy hive is changed. Machine policy is read-only here.
        self._write_user_value(username,name,1 if disabled else None)

    def _audit_temp(self, action, target, details=""):
        try:
            self.audit_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_file,"a",encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {action} | user={target} | {details}\n")
        except Exception: pass

    def _require_admin_approval(self):
        if not is_admin():
            messagebox.showwarning("Administrator required","Run ZYNTRASEC as Administrator."); return False
        pin=messagebox.askyesno("Administrator approval","Windows Administrator approval is required for.\n\nContinue?")
        if not pin: return False
        return True



    def change_center(self):
        self.header("⚙ CHANGE CENTER","Targeted settings. Current value → change → verify.")
        settings=[
            ("UAC","UAC controls elevation prompts.",self.uac_dialog),
            ("Power Plan","Choose a Windows power plan.",self.power_dialog),
            ("User TEMP / TMP","Change environment variable paths.",self.temp_paths),
            ("Policies","Enable/disable common restrictions.",self.policies),
            ("Folder ACL","Edit a selected folder ACL.",self.acl),
        ]
        for a,b,fn in settings:
            r=tk.Frame(self.page,bg=PANEL);r.pack(fill="x",padx=8,pady=4)
            tk.Label(r,text=a,bg=PANEL,fg=TEXT,width=25,anchor="w",font=("Consolas",10,"bold")).pack(side="left",padx=8,pady=8)
            tk.Label(r,text=b,bg=PANEL,fg=MUTED).pack(side="left",fill="x",expand=True)
            ttk.Button(r,text="CHANGE",command=fn).pack(side="right",padx=7)

    def uac_dialog(self):
        if not is_admin():messagebox.showwarning("Admin required","Run as Administrator.");return
        v=tk.StringVar(value="Always notify")
        win=tk.Toplevel(self);win.title("UAC");win.configure(bg=BG);win.geometry("480x300")
        tk.Label(win,text="UAC SETTING",bg=BG,fg=GREEN,font=("Consolas",16,"bold")).pack(pady=15)
        opts=["Always notify","Notify when apps change","Notify without dimming","Never notify"]
        for x in opts:tk.Radiobutton(win,text=x,variable=v,value=x,bg=BG,fg=TEXT,selectcolor="#102719",activebackground=BG).pack(anchor="w",padx=30,pady=3)
        ttk.Button(win,text="APPLY",command=lambda:(self.apply_uac(v.get()),win.destroy())).pack(pady=15)
    def apply_uac(self,v):
        mp={"Always notify":2,"Notify when apps change":5,"Notify without dimming":5,"Never notify":0}
        ps(f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name ConsentPromptBehaviorAdmin -Type DWord -Value {mp[v]}")
        self.logit("UAC set: "+v)

    def power_dialog(self):
        if not is_admin():messagebox.showwarning("Admin required","Run as Administrator.");return
        win=tk.Toplevel(self);win.title("Power Plan");win.configure(bg=BG);win.geometry("480x260")
        v=tk.StringVar(value="Balanced")
        for x in ["Balanced","High performance","Power saver"]:
            tk.Radiobutton(win,text=x,variable=v,value=x,bg=BG,fg=TEXT,selectcolor="#102719",activebackground=BG).pack(anchor="w",padx=30,pady=5)
        ttk.Button(win,text="APPLY",command=lambda:(self.apply_power(v.get()),win.destroy())).pack(pady=15)
    def apply_power(self,v):
        ids={"Balanced":"SCHEME_BALANCED","High performance":"SCHEME_MIN","Power saver":"SCHEME_MAX"}
        run(f"powercfg /setactive {ids[v]}");self.logit("Power plan: "+v)

    def temp_paths(self):
        win=tk.Toplevel(self);win.title("TEMP / TMP");win.configure(bg=BG);win.geometry("700x300")
        fields={}
        for i,name in enumerate(["TEMP","TMP"]):
            tk.Label(win,text=name,bg=BG,fg=TEXT).grid(row=i,column=0,padx=12,pady=12)
            e=tk.Entry(win,bg="#06100a",fg=TEXT,insertbackground=GREEN,width=55);e.insert(0,os.environ.get(name,""));e.grid(row=i,column=1);fields[name]=e
        tk.Label(win,text="Path must exist or be creatable and should be writable by the user.",bg=BG,fg=MUTED).grid(row=2,column=0,columnspan=2,pady=8)
        ttk.Button(win,text="APPLY USER TEMP/TMP",command=lambda:self.apply_temp_paths(fields,win)).grid(row=3,column=0,columnspan=2,pady=12)
    def apply_temp_paths(self,fields,win):
        vals={k:v.get().strip() for k,v in fields.items()}
        if not all(vals.values()):return
        for p in vals.values():
            try:Path(p).mkdir(parents=True,exist_ok=True)
            except Exception as e:messagebox.showerror("Path error",str(e));return
        self.make_env_backup()
        for k,v in vals.items():run(f'setx {k} "{v}"')
        self.logit(f"User TEMP/TMP updated. Sign out/in required: {vals}")
        messagebox.showinfo("Applied","TEMP/TMP updated for future processes. Sign out and back in for all apps to inherit the new values.")
        win.destroy()
    def make_env_backup(self):
        p=self.backup_root/f"ZYNTRASEC_ENV_{datetime.now():%Y%m%d_%H%M%S}.json"
        p.write_text(json.dumps({"TEMP":os.environ.get("TEMP"),"TMP":os.environ.get("TMP")},indent=2),encoding="utf-8")

    def users(self):
        self.header("👤 USERS","Actual Windows local accounts discovered from the system. Select these accounts in Policies or.")
        t=ttk.Treeview(self.page,columns=("Name","Role","Enabled","SID","Profile"),show="headings")
        for c,w in [("Name",180),("Role",170),("Enabled",100),("SID",300),("Profile",360)]:
            t.heading(c,text=c);t.column(c,width=w)
        t.pack(fill="both",expand=True,padx=8,pady=8)
        rows=self._discover_user_rows()
        self.discovered_users=rows
        for r in rows:
            role="ADMINISTRATOR" if r["admin"].lower()=="true" else "STANDARD USER"
            t.insert("", "end",values=(r["name"],role,r["enabled"],r["sid"],r["profile"]))
        ttk.Button(self.page,text="↻ REFRESH",command=self.users).pack(anchor="w",padx=8,pady=5)
        ttk.Button(self.page,text="OPEN LOCAL USERS",command=lambda:run("lusrmgr.msc")).pack(anchor="w",padx=8,pady=5)

    def _builtin_app_path(self, name):
        windir=Path(os.environ.get("WINDIR", r"C:\Windows"))
        if name == "PowerShell":
            return str(windir/"System32"/"WindowsPowerShell"/"v1.0"/"powershell.exe")
        if name == "PowerShell ISE":
            return str(windir/"System32"/"WindowsPowerShell"/"v1.0"/"powershell_ise.exe")
        return None

    def _builtin_app_status(self, username, name):
        exe=self._builtin_app_path(name)
        if not exe or not os.path.isfile(exe): return "NOT INSTALLED"
        return self._custom_app_policy_state(username, exe)

    def _builtin_app_action(self, username, name, block):
        exe=self._builtin_app_path(name)
        if not exe or not os.path.isfile(exe):
            messagebox.showwarning(name, f"{name} was not found on this PC.")
            return False
        ok=self._custom_app_change(username, exe, block)
        if ok: self.refresh_policy_statuses()
        return ok

    def policies(self):
        self.policy_custom_apps=self._load_policy_apps()
        self.header("▣ POLICIES","Built-in Windows policies and added EXE applications use the same BLOCK / ALLOW workflow for the selected local user.")

        # Fixed header/action area. It never scrolls.
        top=tk.Frame(self.page,bg=PANEL);top.pack(fill="x",padx=10,pady=6)
        tk.Label(top,text="Target user:",bg=PANEL,fg=TEXT).pack(side="left",padx=8)
        self.puser=ttk.Combobox(top,width=24,state="readonly")
        self.puser.pack(side="left",padx=8)
        ttk.Button(top,text="↻ REFRESH USERS",command=self.refresh_policy_users).pack(side="left",padx=4)
        ttk.Button(top,text="CHECK ALL SOURCES",command=self.check_policy_user).pack(side="left",padx=4)
        ttk.Button(top,text="AUDIT ALL USERS",command=self.check_all_policy_users).pack(side="left",padx=4)
        ttk.Button(top,text="➕ ADD APP",command=self.add_policy_app).pack(side="left",padx=4)
        self.policy_status=tk.Label(top,text="NOT CHECKED",bg=PANEL,fg=MUTED);self.policy_status.pack(side="left",padx=10)

        self.policy_info=tk.Label(self.page,text="",bg=BG,fg=MUTED,font=("Consolas",10),justify="left")
        self.policy_info.pack(anchor="w",padx=18)
        tk.Label(self.page,text="Built-in policies and added applications are shown together. Use the list scrollbar for any number of EXE entries; the output console stays fixed below.",bg=BG,fg=MUTED,font=("Consolas",9),wraplength=1100,justify="left").pack(anchor="w",padx=18,pady=(0,4))

        self._policy_rows={}
        self._policy_status_labels={}
        self._policy_summary_label=None
        self.refresh_policy_users()

        legend=tk.Frame(self.page,bg=BG);legend.pack(fill="x",padx=18,pady=(0,4))
        tk.Label(legend,text="POLICY STATUS",bg=BG,fg=TEXT,font=("Consolas",10,"bold"),anchor="w").pack(side="left")
        self._policy_summary_label=tk.Label(legend,text="  Checking...",bg=BG,fg=MUTED,font=("Consolas",9),anchor="w");self._policy_summary_label.pack(side="left",padx=10)

        # Global actions are fixed above the scrollable policy list.
        allb=tk.Frame(self.page,bg=BG);allb.pack(fill="x",padx=10,pady=(0,5))
        btn_kw=dict(bg="#063d20",fg=GREEN,activebackground="#0b5b30",activeforeground="white",relief="flat",font=("Consolas",10,"bold"),padx=12,pady=6)
        tk.Button(allb,text="BLOCK ALL POLICIES",command=lambda:self.policy_all_action(True),**btn_kw).pack(side="left",padx=4)
        tk.Button(allb,text="ALLOW ALL POLICIES",command=lambda:self.policy_all_action(False),**btn_kw).pack(side="left",padx=4)
        tk.Button(allb,text="REFRESH STATUS",command=self.refresh_policy_statuses,**btn_kw).pack(side="left",padx=4)

        # Scrollable policy list. 4 built-ins + 100+ EXEs remain manageable without
        # pushing the output console or other fixed controls off-screen.
        list_host=tk.Frame(self.page,bg=BG,highlightbackground="#146b38",highlightthickness=1)
        list_host.pack(fill="both",expand=True,padx=10,pady=(0,4))
        self.policy_canvas=tk.Canvas(list_host,bg=BG,highlightthickness=0,borderwidth=0)
        self.policy_scroll=CyberScrollbar(list_host,orient="vertical",command=self.policy_canvas.yview)
        self.policy_canvas.configure(yscrollcommand=self.policy_scroll.set)
        self.policy_canvas.pack(side="left",fill="both",expand=True)
        self.policy_scroll.pack(side="right",fill="y")
        self.policy_rows_frame=tk.Frame(self.policy_canvas,bg=BG)
        self._policy_window=self.policy_canvas.create_window((0,0),window=self.policy_rows_frame,anchor="nw")
        self.policy_rows_frame.bind("<Configure>",lambda e:self.policy_canvas.configure(scrollregion=self.policy_canvas.bbox("all")))
        self.policy_canvas.bind("<Configure>",lambda e:self.policy_canvas.itemconfigure(self._policy_window,width=e.width))
        self.policy_canvas.bind("<MouseWheel>",lambda e:self.policy_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))
        self.policy_rows_frame.bind("<MouseWheel>",lambda e:self.policy_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        for name in ["CMD","Registry Editor","Task Manager","Control Panel / Settings"]:
            row=tk.Frame(self.policy_rows_frame,bg=PANEL);row.pack(fill="x",pady=3)
            tk.Label(row,text=name,bg=PANEL,fg=TEXT,anchor="w").pack(side="left",fill="x",expand=True,padx=10,pady=7)
            status=tk.Label(row,text="STATUS: CHECKING...",bg=PANEL,fg=MUTED,font=("Consolas",9),width=44,anchor="w");status.pack(side="left",padx=8)
            ttk.Button(row,text="REMOVE APP",command=lambda n=name:self.remove_policy_entry(n)).pack(side="right",padx=3,pady=3)
            ttk.Button(row,text="VERIFY",command=lambda n=name:self.verify_policy_entry(n)).pack(side="right",padx=3,pady=3)
            ttk.Button(row,text="🟢 ALLOW",command=lambda n=name:self.policy_action(n,False)).pack(side="right",padx=3,pady=3)
            ttk.Button(row,text="🔴 BLOCK",command=lambda n=name:self.policy_action(n,True)).pack(side="right",padx=3,pady=3)
            self._policy_status_labels[name]=status

        for item in list(self.policy_custom_apps):
            self._add_policy_row(item)

        self.after_idle(self.refresh_policy_statuses)

    def _add_policy_row(self,item):
        # Custom EXE rows intentionally use the EXACT same layout/widgets as
        # built-in policy rows so every entry has identical height, spacing,
        # status column and button appearance.
        name=item.get("name",Path(item.get("exe","")).stem)
        exe=item.get("exe","")
        key="APP::"+exe
        row=tk.Frame(self.policy_rows_frame,bg=PANEL)
        row.pack(fill="x",pady=3)
        tk.Label(row,text=name,bg=PANEL,fg=TEXT,anchor="w").pack(
            side="left",fill="x",expand=True,padx=10,pady=7)
        status=tk.Label(row,text="STATUS: CHECKING...",bg=PANEL,fg=MUTED,
                        font=("Consolas",9),width=44,anchor="w")
        status.pack(side="left",padx=8)
        # Use ttk.Button exactly like built-in rows. This removes the
        # different filled green appearance seen on added EXE rows.
        ttk.Button(row,text="REMOVE APP",
                   command=lambda e=exe:self.remove_policy_app(e)).pack(
                       side="right",padx=3,pady=3)
        ttk.Button(row,text="VERIFY",
                   command=lambda e=exe:self.verify_policy_app(e)).pack(
                       side="right",padx=3,pady=3)
        ttk.Button(row,text="🟢 ALLOW",
                   command=lambda e=exe:self._policy_custom_action(e,False)).pack(
                       side="right",padx=3,pady=3)
        ttk.Button(row,text="🔴 BLOCK",
                   command=lambda e=exe:self._policy_custom_action(e,True)).pack(
                       side="right",padx=3,pady=3)
        self._policy_status_labels[key]=status
        self._policy_rows[key]=row

    def add_policy_app(self):
        # ADD APP must not race the initial/background policy refresh. If a status
        # check is still running, defer the dialog until that job has completed
        # instead of leaving the user with the generic "Another operation" popup.
        if getattr(self, "_job_running", False):
            if getattr(self, "_add_app_waiting", False):
                return
            self._add_app_waiting = True
            self.policy_status.config(text="FINISHING POLICY CHECK...", fg=WARN)
            def retry():
                self._add_app_waiting = False
                if getattr(self, "_job_running", False):
                    self._add_app_waiting = True
                    self.after(250, retry)
                else:
                    self.add_policy_app()
            self.after(250, retry)
            return

        exe=filedialog.askopenfilename(title="Add application to Policies",filetypes=[("Executable","*.exe"),("All files","*.*")])
        if not exe:return
        exe=os.path.abspath(exe)
        if not os.path.isfile(exe):
            messagebox.showwarning("Policies","Selected executable does not exist.");return
        if self._policy_app_is_pinned(exe):
            messagebox.showinfo("Policies","This application is already in Policies.");return
        name=Path(exe).stem
        # New EXE policies inherit the current built-in policy mode when it is unambiguous.
        # Built-in policies are independent user-hive registry values; arbitrary EXEs cannot
        # be represented by those same registry values, so the EXE uses the same user-targeted
        # BLOCK/ALLOW workflow through its per-file ACL. We never guess when the four built-ins
        # are mixed: the administrator chooses the initial state explicitly.
        try:
            target=self.puser.get().strip()
            self._resolve_user(target)
            states={n:self._policy_audit_detail(target,n)["effective"] for n in self._policy_map()}
            unique=set(states.values())
            if unique=={"BLOCKED"}:
                initial_block=True
            elif unique=={"ALLOWED"}:
                initial_block=False
            else:
                detail="\n".join(f"{n}: {v}" for n,v in states.items())
                choice=messagebox.askyesno(
                    "Initial application policy",
                    f"The built-in policies are currently mixed for {target}:\n\n{detail}\n\n"
                    f"The new app cannot inherit multiple different states.\n\n"
                    f"YES = BLOCK the new app\nNO = ALLOW the new app"
                )
                initial_block=choice
            # Persist the app first, then apply the initial state silently.
            # Do NOT call _custom_app_change() here because that method rebuilds the
            # entire Policies page and can race the status-refresh job.
            self._add_custom_to_policies(exe)
            if initial_block:
                if not self._custom_app_policy_change_silent(target,exe,True):
                    raise RuntimeError("Could not apply BLOCK policy to the new application.")
                initial_state="BLOCKED"
            else:
                # Explicitly verify ALLOW without creating a DisallowRun entry.
                initial_state=self._custom_app_policy_state(target,exe)
                if initial_state != "ALLOWED":
                    if not self._custom_app_policy_change_silent(target,exe,False):
                        raise RuntimeError("Could not verify ALLOW state for the new application.")
                    initial_state="ALLOWED"
            self.logit(f"Application added to Policies: {exe}; inherited_mode={initial_state}")
            # Rebuild exactly once, after the operation is complete.
            self.policies()
        except Exception as e:
            # Do not leave a half-added policy entry when initial enforcement fails.
            self._remove_policy_app(exe)
            messagebox.showerror("ADD APP",str(e))

    def refresh_policy_statuses(self):
        u=self.puser.get().strip() if hasattr(self,"puser") else ""
        labels=dict(getattr(self,"_policy_status_labels",{}))
        if not u or not labels:return
        keys=list(labels.keys())
        def work():
            result={};blocked=allowed=errors=0
            for key in keys:
                try:
                    if key.startswith("APP::"):
                        exe=key[5:]; state=self._custom_app_policy_state(u,exe) if os.path.isfile(exe) else "MISSING"
                        result[key]=state
                    else:
                        result[key]=self._policy_audit_detail(u,key)["effective"]
                except Exception: result[key]="ERROR"
            for state in result.values():
                if state=="BLOCKED":blocked+=1
                elif state=="ALLOWED":allowed+=1
                else:errors+=1
            return result,blocked,allowed,errors
        def done(data):
            result,blocked,allowed,errors=data
            for key,state in result.items():
                label=labels.get(key)
                if not label or not label.winfo_exists():continue
                if key.startswith("APP::"):
                    if state=="BLOCKED":label.config(text="STATUS: 🔴 BLOCKED | USER POLICY",fg="#ff5c5c")
                    elif state=="ALLOWED":label.config(text="STATUS: 🟢 ALLOWED | NO ACTIVE BLOCK",fg=GREEN)
                    elif state=="MISSING":label.config(text="STATUS: ⚪ MISSING",fg=MUTED)
                    else:label.config(text="STATUS: ⚠ CHECK ERROR",fg="#ff5c5c")
                else:
                    if state=="BLOCKED":label.config(text="STATUS: 🔴 BLOCKED | USER POLICY",fg="#ff5c5c")
                    elif state=="ALLOWED":label.config(text="STATUS: 🟢 ALLOWED | NO ACTIVE BLOCK",fg=GREEN)
                    else:label.config(text="STATUS: ⚠ CHECK ERROR",fg="#ff5c5c")
            if getattr(self,"_policy_summary_label",None) is not None:
                total=len(labels);txt=f"🔴 {blocked} BLOCKED   |   🟢 {allowed} ALLOWED   |   ⚠ {errors} ERROR" if errors else f"🔴 {blocked} BLOCKED   |   🟢 {allowed} ALLOWED   |   TOTAL {total}"
                self._policy_summary_label.config(text=txt,fg="#ffcc00" if errors else GREEN)
        self._async_job(work,done,"CHECKING POLICIES...")

    def refresh_policy_users(self):
        if not hasattr(self,"puser"): return
        self.puser["values"]=("Loading...",); self.puser.set("Loading...")
        def work(): return self._discover_user_rows()
        def done(rows):
            self._policy_rows={r["name"]:r for r in rows}
            names=[r["name"] for r in rows if str(r.get("enabled","")).lower()=="true"]
            self.puser["values"]=names
            preferred=self._preferred_local_user(rows)
            if preferred in names:self.puser.set(preferred)
            elif names:self.puser.set(names[0])
            self.update_policy_info(); self.refresh_policy_statuses()
        self._async_job(work,done,"LOADING USERS...")

    def update_policy_info(self):
        name=self.puser.get().strip()
        row=self._policy_rows.get(name)
        if not row:
            self.policy_info.config(text="No Windows user selected.",fg=MUTED)
            return
        role="ADMINISTRATOR" if row["admin"].lower()=="true" else "STANDARD USER"
        self.policy_info.config(text=f"SID: {row['sid']}    ROLE: {role}    STATUS: {'ENABLED' if row['enabled'].lower()=='true' else 'DISABLED'}",fg=GREEN)
        self.puser.bind("<<ComboboxSelected>>",lambda e:self.update_policy_info())

    def check_policy_user(self):
        u=self.puser.get().strip()
        if not u:return
        self.policy_status.config(text="CHECKING...",fg=WARN)
        def work():
            sid,profile=self._resolve_user(u); states=[]
            for name in self._policy_map():
                try:
                    d=self._policy_audit_detail(u,name);states.append(f"{name}: EFFECTIVE={d['effective']} | USER={d['user_state']} | MACHINE={d['machine_state']}")
                except Exception:states.append(f"{name}: CHECK ERROR")
            return sid,states
        def done(r):
            sid,states=r;self.policy_status.config(text=f"FULL AUDIT OK: {u}",fg=GREEN);self.update_policy_info();self.logit(f"Full policy audit completed for {u}: "+" | ".join(states));self.refresh_policy_statuses()
        self._async_job(work,done,"AUDITING POLICY...")

    def check_all_policy_users(self):
        self.policy_status.config(text="AUDITING ALL USERS...",fg=WARN)
        rows=list(self._policy_rows.values())
        def work():
            out=[]
            for row in rows:
                if str(row.get("enabled","")).lower()!="true":continue
                name=row["name"];states=[]
                for item in self._policy_map():
                    try:
                        d=self._policy_audit_detail(name,item);states.append(f"{item}=EFFECTIVE:{d['effective']}/USER:{d['user_state']}/MACHINE:{d['machine_state']}")
                    except Exception:states.append(f"{item}=CHECK ERROR")
                out.append((name," | ".join(states)))
            return out
        def done(out):
            self.policy_status.config(text=f"AUDIT COMPLETE: {len(out)} USER(S)",fg=GREEN)
            self.logit("All-user policy audit: "+" || ".join(f"{n}: {v}" for n,v in out))
        self._async_job(work,done,"AUDITING USERS...")

    def _admin_target_warning(self, username, action_text):
        """Extra confirmation when the selected target is an Administrator account.
        This prevents accidentally locking the operator out of their own tools.
        """
        row=self._policy_rows.get(username,{})
        is_target_admin=str(row.get("admin","")).lower()=="true"
        current=os.environ.get("USERNAME","").lower()
        is_current=(username.lower()==current)
        if not (is_target_admin or is_current):
            return True
        msg=(
            "⚠ ADMINISTRATOR ACCOUNT WARNING\n\n"
            f"Target user: {username}\n"
            f"Requested action: {action_text}\n\n"
            "This target is an Administrator account (and may be the account running ZYNTRASEC).\n"
            "Changing these restrictions can block Command Prompt, Registry Editor, Task Manager, "
            "or Control Panel/Settings for this administrator.\n\n"
            "A backup will be created before the change.\n"
            "Machine-level policy will NOT be modified by this module.\n\n"
            "Do you want to continue?"
        )
        return messagebox.askyesno("ADMINISTRATOR CHANGE WARNING", msg, icon="warning")

    def _save_policy_recovery_state(self, username, states, app_states=None):
        """Save exact target-user policy values for independent emergency recovery."""
        payload={"created":datetime.now().isoformat(),"target":username,"states":states,"app_states":app_states or {}}
        self.recovery_root.mkdir(parents=True,exist_ok=True)
        tmp=self.recovery_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload,indent=2),encoding="utf-8")
        os.replace(tmp,self.recovery_file)
        try:
            run(f'attrib +h "{self.recovery_file}"')
        except Exception: pass
        self.logit(f"Emergency recovery snapshot saved for {username}.")

    def _restore_recovery_state(self):
        if not is_admin():
            messagebox.showwarning("Administrator required","Run ZYNTRASEC as Administrator."); return False
        if not self.recovery_file.exists():
            messagebox.showinfo("Emergency Recovery","No emergency recovery snapshot exists."); return False
        try:
            payload=json.loads(self.recovery_file.read_text(encoding="utf-8"))
            target=payload["target"]; states=payload["states"]
            if not messagebox.askyesno("EMERGENCY RECOVERY", f"Restore the last safe policy state?\n\nTarget: {target}\nSnapshot: {payload.get('created','unknown')}\n\nThis restores only the saved USER policy values."):
                return False
            self._resolve_user(target)
            for name,val in states.items(): self._write_user_value(target,name,val)
            app_states=payload.get("app_states",{}) or {}
            app_failures=[]
            for exe,expected in app_states.items():
                if expected not in ("BLOCKED","ALLOWED") or not os.path.isfile(exe):
                    continue
                try:
                    self._custom_app_policy_change_silent(target,exe,expected=="BLOCKED")
                    actual=self._custom_app_policy_state(target,exe)
                    if actual!=expected:
                        app_failures.append(f"{Path(exe).stem}: expected {expected}, got {actual}")
                except Exception as e:
                    app_failures.append(f"{Path(exe).stem}: {e}")
            failures=[]
            for name,val in states.items():
                actual=self._read_user_value(target,name)
                if actual!=val: failures.append(f"{name}: expected {val!r}, got {actual!r}")
            failures.extend(app_failures)
            self._audit_temp("EMERGENCY_RESTORE",target,"; ".join(failures) if failures else "verified")
            if failures:
                messagebox.showwarning("Recovery verification","Recovery attempted, but verification found:\n\n"+"\n".join(failures)); return False
            messagebox.showinfo("Emergency Recovery","Last safe policy state restored and verified.")
            self.logit(f"Emergency recovery verified for {target}.")
            self.check_policy_user(); self.refresh_policy_statuses(); return True
        except Exception as e:
            messagebox.showerror("Emergency Recovery",str(e)); return False

    def emergency_recovery(self):
        self.header("🛟 EMERGENCY RECOVERY","Restore the last saved policy state without changing machine-level policy.")
        exists=self.recovery_file.exists()
        text="LAST SAFE SNAPSHOT: AVAILABLE" if exists else "LAST SAFE SNAPSHOT: NOT AVAILABLE"
        tk.Label(self.page,text=text,bg=BG,fg=GREEN if exists else WARN,font=("Consolas",14,"bold")).pack(anchor="w",padx=12,pady=12)
        if exists:
            try:
                data=json.loads(self.recovery_file.read_text(encoding="utf-8")); target=data.get("target","unknown"); created=data.get("created","unknown")
                detail=f"Target: {target}\nCreated: {created}\n\nOnly the saved USER policy values will be restored.\nMachine-level policy is never changed by this recovery module."
            except Exception:
                detail="Recovery snapshot exists but could not be read."
        else: detail="Make a policy change from ZYNTRASEC to create a recovery snapshot."
        tk.Label(self.page,text=detail,bg=PANEL,fg=TEXT,justify="left",anchor="w",padx=12,pady=12).pack(fill="x",padx=10)
        ttk.Button(self.page,text="🛟 RESTORE LAST SAFE STATE",command=self._restore_recovery_state).pack(anchor="w",padx=10,pady=10)
        ttk.Button(self.page,text="↻ CHECK STATUS",command=self.emergency_recovery).pack(anchor="w",padx=10,pady=4)

    def _policy_custom_action(self, exe, block):
        u=self.puser.get().strip()
        try:
            if self._custom_app_change(u,exe,block):
                self.refresh_policy_statuses()
        except Exception as e:
            messagebox.showerror("Policy change",str(e))

    def verify_policy_entry(self, name):
        """Verify either a built-in policy or an added EXE from the same row UI."""
        try:
            if name in self._policy_map():
                u=self.puser.get().strip()
                if not u:
                    return
                detail=self._policy_audit_detail(u,name)
                text=(f"{name}\n\n"
                      f"USER: {detail.get('user_state')}\n"
                      f"MACHINE: {detail.get('machine_state')}\n"
                      f"EFFECTIVE: {detail.get('effective')}")
                self.refresh_policy_statuses()
                messagebox.showinfo("VERIFY",text)
                self.logit(f"Built-in policy verified: {name}; user={u}; effective={detail.get('effective')}")
                return
            # Added EXE: name is displayed name, find matching saved app.
            item=next((x for x in self.policy_custom_apps if x.get('name')==name),None)
            if item:
                self.verify_policy_app(item.get('exe',''))
        except Exception as e:
            messagebox.showerror("VERIFY",str(e))

    def remove_policy_entry(self, name):
        """Keep the same four-button UI. Built-in policies cannot be removed; their policy remains available."""
        if name in self._policy_map():
            messagebox.showinfo("REMOVE APP",
                f"{name} is a built-in Windows policy.\n\n"
                "Built-in policies cannot be removed from ZYNTRASEC.\n"
                "Use ALLOW if you want to turn the restriction off.")
            self.logit(f"Remove requested for built-in policy (not removable): {name}")
            return
        item=next((x for x in self.policy_custom_apps if x.get('name')==name),None)
        if item:
            self.remove_policy_app(item.get('exe',''))

    def verify_policy_app(self, exe):
        u=self.puser.get().strip()
        if not u:
            return
        try:
            state=self._custom_app_policy_state(u,exe)
            label=self._policy_status_labels.get("APP::"+exe)
            if label and label.winfo_exists():
                if state=="BLOCKED":
                    label.config(text="STATUS: 🔴 BLOCKED | USER POLICY",fg="#ff5c5c")
                elif state=="ALLOWED":
                    label.config(text="STATUS: 🟢 ALLOWED | NO ACTIVE BLOCK",fg=GREEN)
                else:
                    label.config(text=f"STATUS: ⚠ {state}",fg=WARN)
            messagebox.showinfo("VERIFY",f"{Path(exe).stem}\n\nUSER: {state}\nMACHINE: NOT SET\nEFFECTIVE: {state}")
            self.logit(f"Policy app verified: {exe}; user={u}; state={state}")
        except Exception as e:
            messagebox.showerror("VERIFY",str(e))

    def remove_policy_app(self, exe):
        u=self.puser.get().strip()
        item=next((x for x in self.policy_custom_apps if os.path.normcase(x.get("exe",""))==os.path.normcase(exe)),None)
        if not item:
            return
        name=item.get("name",Path(exe).stem)
        try:
            state=self._custom_app_policy_state(u,exe) if os.path.isfile(exe) else "MISSING"
            if state=="BLOCKED":
                if not messagebox.askyesno("REMOVE APP",f"{name} is currently BLOCKED for {u}.\n\nRemove the app from Policies and ALLOW its file access first?\n\nThis keeps the system from leaving an unmanaged blocked EXE."):
                    return
                if not self._custom_app_change(u,exe,False):
                    return
            elif state=="CHECK ERROR":
                messagebox.showwarning("REMOVE APP","The EXE permissions could not be verified. The app was not removed.")
                return
            if not messagebox.askyesno("REMOVE APP",f"Remove {name} from Policies?\n\nIt will no longer be managed by ZYNTRASEC Policies."):
                return
            self._remove_policy_app(exe)
            self.logit(f"Application removed from Policies: {exe}")
            self.policies()
        except Exception as e:
            messagebox.showerror("REMOVE APP",str(e))

    def move_policy_app_to_custom(self, exe):
        # Compatibility for older saved callbacks; current UI intentionally has no
        # separate Custom Apps destination. Use REMOVE APP from Policies instead.
        self.remove_policy_app(exe)

    def policy_all_action(self, enable_restrictions):
        """Enable/disable all built-in and added EXE policies for the selected user.
        Built-ins use their existing per-user policy values. Added EXEs use the same
        target-user policy workflow through DisallowRun. Machine-level policy is never
        modified. Every operation is verified and failures are reported without hiding
        the successful items.
        """
        u=self.puser.get().strip()
        builtins=list(self._policy_map().keys())
        apps=list(self.policy_custom_apps)
        try:
            self._resolve_user(u)
            before={name:self._policy_audit_detail(u,name) for name in builtins}
            app_before={}
            for item in apps:
                exe=item.get("exe","")
                app_before[exe]=self._custom_app_policy_state(u,exe) if os.path.isfile(exe) else "MISSING"

            desired="BLOCK ALL" if enable_restrictions else "ALLOW ALL"
            lines=[f"{name}: USER={d['user_state']} | MACHINE={d['machine_state']} | EFFECTIVE={d['effective']}"
                   for name,d in before.items()]
            if apps:
                lines += [f"{item.get('name',Path(item.get('exe','')).stem)}: APP={app_before.get(item.get('exe',''),'MISSING')}"
                          for item in apps]
            warning=""
            if enable_restrictions:
                machine_blocked=[name for name,d in before.items() if d["machine_state"]=="BLOCKED"]
                if machine_blocked:
                    warning="\n\nWARNING: Machine-level policy is already BLOCKED for: " + ", ".join(machine_blocked) + ". Machine policy will NOT be changed."
            if not self._admin_target_warning(u, desired):
                return
            if not messagebox.askyesno("Confirm all policy changes",
                f"{desired}\n\nUser: {u}\n\nCurrent status:\n" + "\n".join(lines) +
                "\n\nOnly this user's policy hive will be changed.\nMachine policy is read-only." + warning):
                return

            self.make_backup()
            recovery={name: before[name]["user"] for name in builtins}
            self._save_policy_recovery_state(u, recovery, app_before)

            failures=[]
            # Built-in policies
            for name in builtins:
                try:
                    self._set_user_restriction(u,name,enable_restrictions)
                except Exception as e:
                    failures.append(f"{name}: {e}")

            # Added EXE policies
            for item in apps:
                exe=item.get("exe","")
                if not exe or not os.path.isfile(exe):
                    failures.append(f"{item.get('name',Path(exe).stem)}: executable missing")
                    continue
                try:
                    if not self._custom_app_policy_change_silent(u,exe,enable_restrictions):
                        failures.append(f"{item.get('name',Path(exe).stem)}: policy change failed")
                except Exception as e:
                    failures.append(f"{item.get('name',Path(exe).stem)}: {e}")

            # Verify built-ins and apps
            after={name:self._policy_audit_detail(u,name) for name in builtins}
            for name,d in after.items():
                expected="BLOCKED" if enable_restrictions else "ALLOWED"
                if d["user_state"] != expected:
                    failures.append(f"{name}: expected USER={expected}, got USER={d['user_state']}")
                self.logit(f"ALL POLICY change verified: {name} | USER={d['user_state']} | MACHINE={d['machine_state']} | EFFECTIVE={d['effective']}")
            for item in apps:
                exe=item.get("exe","")
                if os.path.isfile(exe):
                    state=self._custom_app_policy_state(u,exe)
                    expected="BLOCKED" if enable_restrictions else "ALLOWED"
                    if state != expected:
                        failures.append(f"{item.get('name',Path(exe).stem)}: expected {expected}, got {state}")
                    self.logit(f"ALL APP policy verified: {exe}; user={u}; state={state}")

            self.check_policy_user()
            self.refresh_policy_statuses()
            state="ENABLED" if enable_restrictions else "DISABLED"
            if failures:
                messagebox.showwarning("Policy operation completed with errors",
                    f"{desired} completed for {u}, but some items need attention:\n\n" + "\n".join(failures))
            else:
                messagebox.showinfo("Policies updated",
                    f"{desired}\n\nUser: {u}\nBuilt-in policies: {len(builtins)}\nAdded applications: {len(apps)}\n\nAll requested policies were verified as {state}.")
        except Exception as e:
            messagebox.showerror("All Policies",str(e))

    def _custom_app_policy_change_silent(self, username, exe, block):
        """Apply one custom-app DisallowRun state without showing per-app dialogs.
        Used by BLOCK/ALLOW ALL so the UI remains one operation instead of opening
        a separate confirmation/info popup for every application.
        """
        if not is_admin():
            raise RuntimeError("Run ZYNTRASEC as Administrator to change application access.")
        if not os.path.isfile(exe):
            raise RuntimeError("Selected executable does not exist.")
        hive,loaded,orig_sid=self._user_hive(username)
        try:
            base=fr"HKU\{hive}\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            key=base + r"\DisallowRun"
            wanted=Path(exe).name
            q=subprocess.run(["reg.exe","query",key],capture_output=True,text=True,timeout=30)
            entries=[]
            if q.returncode==0:
                for line in (q.stdout or "").splitlines():
                    parts=line.strip().split(None,2)
                    if len(parts)>=3 and parts[1].upper() in ("REG_SZ","REG_EXPAND_SZ"):
                        entries.append((parts[0],parts[2].strip()))
            matching=[n for n,v in entries if v.lower()==wanted.lower()]
            if block:
                p=subprocess.run(["reg.exe","add",base,"/v","DisallowRun","/t","REG_DWORD","/d","1","/f"],capture_output=True,text=True,timeout=30)
                if p.returncode!=0:
                    raise RuntimeError((p.stdout or p.stderr or "Failed to enable DisallowRun policy.").strip())
                if not matching:
                    numeric=[]
                    for n,v in entries:
                        try: numeric.append(int(n))
                        except ValueError: pass
                    value_name=str(max(numeric,default=0)+1)
                    p=subprocess.run(["reg.exe","add",key,"/v",value_name,"/t","REG_SZ","/d",wanted,"/f"],capture_output=True,text=True,timeout=30)
                    if p.returncode!=0:
                        raise RuntimeError((p.stdout or p.stderr or "Failed to add application policy.").strip())
            else:
                for value_name in matching:
                    p=subprocess.run(["reg.exe","delete",key,"/v",value_name,"/f"],capture_output=True,text=True,timeout=30)
                    if p.returncode!=0:
                        raise RuntimeError((p.stdout or p.stderr or "Failed to remove application policy.").strip())
                q2=subprocess.run(["reg.exe","query",key],capture_output=True,text=True,timeout=30)
                remaining=[]
                if q2.returncode==0:
                    for line in (q2.stdout or "").splitlines():
                        parts=line.strip().split(None,2)
                        if len(parts)>=3 and parts[1].upper() in ("REG_SZ","REG_EXPAND_SZ"):
                            remaining.append(parts)
                if not remaining:
                    subprocess.run(["reg.exe","delete",base,"/v","DisallowRun","/f"],capture_output=True,text=True,timeout=30)
            # Verify before unloading hive.
            state=self._custom_app_policy_state(username,exe)
            expected="BLOCKED" if block else "ALLOWED"
            if state!=expected:
                raise RuntimeError(f"Verification failed. Expected {expected}, got {state}.")
            self.logit(f"Policy app changed silently: {Path(exe).stem}; user={username}; state={state}")
            return True
        finally:
            self._close_user_hive(hive,loaded,orig_sid)

    def policy_action(self,name,disabled):
        u=self.puser.get().strip()
        try:
            self._resolve_user(u)
            before=self._policy_audit_detail(u,name)
            action="ALLOW" if not disabled else "BLOCK"
            machine_warning = before["machine_state"] == "BLOCKED"
            detail=(f"\n\nBefore: USER={before['user_state']} | MACHINE={before['machine_state']} | EFFECTIVE={before['effective']}"
                    f"\n\nThis action changes ONLY the selected user's policy hive.\nMachine policy is read-only.")
            if machine_warning and not disabled:
                detail += "\n\nWARNING: A machine-level policy is BLOCKED, so enabling this user may not remove the effective restriction."
            if not self._admin_target_warning(u, f"{action} {name}"):
                return
            if not messagebox.askyesno("Confirm policy change",f"{action}\n\nUser: {u}\nPolicy: {name}"+detail):
                return
            self.make_backup()
            self._save_policy_recovery_state(u, {name: before["user"]})
            self._set_user_restriction(u,name,disabled)
            after=self._policy_audit_detail(u,name)
            state="ALLOWED" if not disabled else "BLOCKED"
            self.logit(f"Policy {name}: {state} for {u} | USER={after['user_state']} | MACHINE={after['machine_state']} | EFFECTIVE={after['effective']}")
            self.check_policy_user()
            self.refresh_policy_statuses()
            if after["user_state"] != state:
                rollback_errors=self._rollback_values_direct(u,{name: before["user"]})
                detail=(f"{name}: expected USER={state}, got USER={after['user_state']}"
                        + (("\nRollback errors: " + "; ".join(rollback_errors)) if rollback_errors else "\nOriginal value restored."))
                messagebox.showwarning("Policy verification failed",detail)
                self.check_policy_user(); self.refresh_policy_statuses()
                return
            messagebox.showinfo("Policy changed",
                f"{name}\nUser: {u}\nRequested: {state}\n\n"
                f"Verified: USER={after['user_state']} | MACHINE={after['machine_state']} | EFFECTIVE={after['effective']}\n\n"
                "If the target user is currently signed in, Windows may require sign-out/sign-in for the restriction to refresh.")
        except Exception as e:
            messagebox.showerror("Policy change",str(e))

    def acl(self):
        self.header("🔐 ACL / FOLDERS",
                    "Targeted NTFS permissions. Review → BACKUP → APPLY → VERIFY. SYSTEM and Administrators are protected.")

        # Responsive ACL layout: controls are split into rows so no option is
        # pushed outside the visible page on smaller windows/resolutions.
        r=tk.Frame(self.page,bg=BG); r.pack(fill="x",padx=8,pady=2)
        self.apath=tk.Entry(r,bg="#06100a",fg=TEXT,insertbackground=GREEN,width=48)
        self.apath.insert(0,"D:\\PCYB"); self.apath.pack(side="left",fill="x",expand=True)
        ttk.Button(r,text="BROWSE",command=lambda:self.pick(self.apath)).pack(side="left",padx=4)
        ttk.Button(r,text="CHECK",command=self.check_acl).pack(side="left",padx=4)
        ttk.Button(r,text="CHECK USER ACCESS",command=self.check_acl_user).pack(side="left",padx=4)

        r1=tk.Frame(self.page,bg=BG); r1.pack(fill="x",padx=8,pady=2)
        for txt,fn in [
            ("DRY RUN",self.acl_dry_run),
            ("BACKUP",self.acl_backup),
            ("GUIDE / HOW TO USE",self.acl_guide),
            ("AUTO ACCESS DIAGNOSTIC",self.acl_auto_diagnostic),
        ]:
            ttk.Button(r1,text=txt,command=fn).pack(side="left",padx=4)

        r2=tk.Frame(self.page,bg=BG); r2.pack(fill="x",padx=8,pady=4)
        users=[u["name"] for u in discover_local_users() if not u.get("disabled")]
        ttk.Label(r2,text="USER:").pack(side="left")
        self.acl_user=tk.StringVar(value=(users[0] if users else os.environ.get("USERNAME","")))
        self.acl_user_box=ttk.Combobox(r2,textvariable=self.acl_user,values=users,width=18,state="readonly")
        self.acl_user_box.pack(side="left",padx=4)
        self.acl_recursive=tk.BooleanVar(value=False)
        ttk.Checkbutton(r2,text="Include subfolders/files",variable=self.acl_recursive).pack(side="left",padx=8)

        r3=tk.Frame(self.page,bg=BG); r3.pack(fill="x",padx=8,pady=2)
        for txt,fn in [
            ("ALLOW ONLY",self.allow_only_acl),
            ("ADMINISTRATORS ONLY",self.admins_only_acl),
            ("RESTORE USER ACCESS",self.restore_user_access),
            ("REMOVE USER ACCESS",self.remove_user_access),
        ]:
            ttk.Button(r3,text=txt,command=fn).pack(side="left",padx=4)

        r4=tk.Frame(self.page,bg=BG); r4.pack(fill="x",padx=8,pady=2)
        for txt,fn in [
            ("VERIFY",self.verify_acl),
            ("ROLLBACK",self.acl_rollback),
        ]:
            ttk.Button(r4,text=txt,command=fn).pack(side="left",padx=4)

        self.output_show(
            "ACL / FOLDERS","READY",
            "ORDER: BROWSE → USER → CHECK → CHECK USER ACCESS → DRY RUN → BACKUP → APPLY → VERIFY.\n"
            "APPLY = choose ONE: ALLOW ONLY / ADMINISTRATORS ONLY / RESTORE USER ACCESS / REMOVE USER ACCESS.\n"
            "Default scope is THIS FOLDER ONLY. Use GUIDE / HOW TO USE for the click-by-click sequence."
        )

    def acl_guide(self):
        # A safe click-by-click guide. It explains the order without
        # automatically performing permission-changing actions.
        dlg = tk.Toplevel(self)
        dlg.title("ZYNTRASEC // ACL STEP-BY-STEP GUIDE")
        dlg.configure(bg=BG)
        dlg.transient(self)
        dlg.geometry("760x620")
        dlg.minsize(700,560)

        tk.Label(
            dlg,
            text="🔐 ACL / FOLDERS — STEP-BY-STEP",
            bg=BG, fg=GREEN, font=("Consolas",18,"bold")
        ).pack(pady=(14,4))

        tk.Label(
            dlg,
            text="Use the options in this order. Change permissions only after BACKUP + DRY RUN.",
            bg=BG, fg=TEXT, font=("Consolas",10)
        ).pack(pady=(0,10))

        body=tk.Frame(dlg,bg=BG)
        body.pack(fill="both",expand=True,padx=16,pady=8)

        guide=(
            "STEP 1  — BROWSE\n"
            "Select the folder you want to manage.\n\n"
            "STEP 2  — USER\n"
            "Select the Windows local user (example: pcuser).\n\n"
            "STEP 3  — CHECK\n"
            "View the current NTFS ACL. No change is made.\n\n"
            "STEP 4  — CHECK USER ACCESS\n"
            "Check whether the selected user has a direct ACE and inspect the root ACL.\n\n"
            "STEP 5  — DRY RUN\n"
            "Preview what ALLOW ONLY / LOCK TO USER would change. No change is made.\n\n"
            "STEP 6  — BACKUP\n"
            "Save the current ACL before changing anything.\n\n"
            "STEP 7  — CHOOSE ONE ACTION\n"
            "  • ALLOW ONLY      → restrict broad access and grant the selected user.\n"
            "  • ADMINISTRATORS ONLY → keep administrative access protected.\n"
            "  • RESTORE USER ACCESS → give selected user READ/EXECUTE, MODIFY, or FULL CONTROL.\n"
            "  • REMOVE USER ACCESS  → remove that user's direct ACE only.\n\n"
            "STEP 8  — VERIFY\n"
            "Confirm selected user, SYSTEM, Administrators, and remaining broad ACEs.\n\n"
            "STEP 9  — ROLLBACK\n"
            "If a previous ACL backup must be restored, select the backup and restore it.\n\n"
            "IMPORTANT\n"
            "Keep 'Include subfolders/files' OFF unless you intentionally want a recursive change.\n"
            "Inherited permissions are identified before changes; parent ACLs are not changed in normal folder-only mode."
        )

        box=tk.Text(
            body,bg="#020502",fg=TEXT,insertbackground=GREEN,
            font=("Consolas",10),wrap="word",relief="flat"
        )
        box.pack(fill="both",expand=True)
        box.insert("1.0",guide)
        box.configure(state="disabled")

        ttk.Button(
            dlg,text="CLOSE GUIDE",command=dlg.destroy
        ).pack(pady=(4,14))

    def acl_auto_diagnostic(self):
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator.");return
        path=self.apath.get().strip()
        user=self.acl_user.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("ACL / Folders","Select a valid folder first.");return
        if not user:
            messagebox.showwarning("ACL / Folders","Select a local user first.");return

        self.output_show("ACL / FOLDERS","AUTO ACCESS DIAGNOSTIC",
                         f"Analyzing access source...\nTarget: {path}\nUser: {user}",
                         "RUNNING")

        def icacls_cmd(target):
            # A quoted root path such as "E:\\" is parsed incorrectly by cmd.exe.
            # Use the drive root without quotes; quote normal paths.
            ap=os.path.abspath(target)
            drive,tail=os.path.splitdrive(ap)
            if tail in ("\\", "/"):
                return f'icacls {drive}\\'
            return f'icacls "{ap}"'

        def principal_matches(line, selected_user):
            line=line.strip().lower()
            selected=selected_user.lower().strip()
            if not selected:
                return False
            short=selected.split('\\')[-1]
            # Match either DOMAIN\\user or plain user at the beginning of an ACE line.
            return line.startswith(selected + ':') or line.startswith(short + ':') or (('\\'+short+':') in line)

        def worker():
            items=[]
            commands=[
                ("WHOAMI","whoami"),
                ("USER / GROUP MEMBERSHIP",f'net user "{user}"'),
                ("TARGET ACL",icacls_cmd(path))
            ]
            for title,cmd in commands:
                rc,out=run(cmd,30)
                items.append((title,out.strip() or "(no output)"))

            parent=os.path.dirname(os.path.abspath(path).rstrip("\\/"))
            if not parent:
                parent=os.path.splitdrive(os.path.abspath(path))[0]+"\\"
            rc,out=run(icacls_cmd(parent),30)
            items.append((f"PARENT ACL: {parent}",out.strip() or "(no output)"))

            sid=self._resolve_local_sid(user)
            if sid:
                # /findsid is supplementary only; direct ACE detection is done from
                # the target ACL so a valid ACL is never reported as "no access" merely
                # because /findsid does not enumerate the root as expected.
                rc,out=run(f'icacls "{os.path.abspath(path)}" /findsid {sid} /C',60)
                items.append((f"USER SID: {sid}",out.strip() or "(no matching ACE from /findsid)"))
            else:
                items.append(("USER SID","Could not resolve selected user's SID."))

            target_text=items[2][1]
            target_lines=target_text.splitlines()
            groups=items[1][1].lower()
            parent_text=items[3][1]
            target_lower=target_text.lower()
            causes=[]

            direct_lines=[ln.strip() for ln in target_lines if principal_matches(ln,user)]
            if direct_lines:
                causes.append("DIRECT USER ACE: YES")
                causes.append("  " + direct_lines[0])
            else:
                causes.append("DIRECT USER ACE: NOT DETECTED ON TARGET ROOT")

            admin_member=("local group memberships" in groups and "*administrators" in groups) or "*administrators" in groups
            if admin_member:
                causes.append("ADMINISTRATORS GROUP: YES — user inherits access through BUILTIN\\Administrators when that group has access.")
            else:
                causes.append("ADMINISTRATORS GROUP: not detected")

            if "builtin\\users:" in target_lower:
                causes.append("BUILTIN\\Users ACE: YES")
            else:
                causes.append("BUILTIN\\Users ACE on target root: NO")
            if "authenticated users:" in target_lower:
                causes.append("Authenticated Users ACE: YES")
            else:
                causes.append("Authenticated Users ACE on target root: NO")
            if "everyone:" in target_lower:
                causes.append("Everyone ACE: YES")
            else:
                causes.append("Everyone ACE on target root: NO")
            if "(i)" in target_lower:
                causes.append("INHERITED ACEs: YES — review the parent ACL/inheritance chain.")
            else:
                causes.append("INHERITED ACEs: not detected in target output")

            if parent_text and "successfully processed 0 files" not in parent_text.lower() and "error" not in parent_text.lower():
                causes.append("PARENT ACL: collected successfully")
            elif parent_text:
                causes.append("PARENT ACL: check the collected parent output for errors")

            report=(f"TARGET: {path}\n"
                    f"USER: {user}\n\n"
                    "LIKELY ACCESS SOURCES\n"
                    + "-"*70 + "\n"
                    + "\n".join("• "+x for x in causes)
                    + "\n\nNO PERMISSIONS WERE CHANGED.\n\n"
                    + "\n\n".join(title+"\n"+"-"*70+"\n"+body for title,body in items))
            return 0,report

        def done(result):
            rc,report=result
            self.output_show("ACL / FOLDERS","AUTO ACCESS DIAGNOSTIC",report,
                             "SUCCESS" if rc==0 else "REVIEW")
            self.logit(f"ACL auto access diagnostic: {path} -> {user}")

        self._async_job(worker,done,"AUTO ACCESS DIAGNOSTIC...")

    def pick(self,e):
        p=filedialog.askdirectory()
        if p:e.delete(0,"end");e.insert(0,p)

    def _acl_target(self):
        path=self.apath.get().strip()
        user=self.acl_user.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("ACL / Folders","Select a valid file or folder first.")
            return None,None
        if not user:
            messagebox.showwarning("ACL / Folders","Choose a local user first.")
            return None,None
        safe_user=user.replace('"','')
        if safe_user.lower() in {"system","administrators","everyone","authenticated users","users","trustedinstaller"}:
            messagebox.showwarning("ACL / Folders","Choose a normal local user. Protected Windows principals cannot be selected.")
            return None,None
        return path,safe_user

    def _acl_scope(self):
        return "/T /C" if self.acl_recursive.get() else "/C"

    def _save_acl_backup_details(self, backup_path, target, selected_user, action, scope, icacls_output=""):
        """Write sidecar metadata for every user-visible ACL backup.
        The .txt backup remains a native icacls /save snapshot so ROLLBACK
        can consume it directly; metadata is stored separately and never
        contaminates the restore file.
        """
        try:
            bp=Path(backup_path)
            safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", selected_user or "unknown")
            stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            details={
                "backup_file": str(bp),
                "metadata_file": str(bp.with_suffix(".json")),
                "created_at": datetime.now().astimezone().isoformat(),
                "computer_name": os.environ.get("COMPUTERNAME") or platform.node(),
                "windows_account": ((os.environ.get("USERDOMAIN") + "\\" + os.environ.get("USERNAME")) if os.environ.get("USERDOMAIN") and os.environ.get("USERNAME") else (os.environ.get("USERNAME") or "unknown")),
                "selected_acl_user": selected_user or "unknown",
                "target": str(target),
                "action": action,
                "scope": scope,
                "recursive": bool(self.acl_recursive.get()),
                "backup_type": "icacls /save ACL snapshot",
                "restore_compatible": True,
                "notes": "Do not edit this .txt backup. Edit/view the .json metadata instead.",
                "icacls_result": icacls_output.strip()[-10000:] if icacls_output else ""
            }
            meta=bp.with_suffix(".json")
            meta.write_text(json.dumps(details,indent=2,ensure_ascii=False),encoding="utf-8")
            info=bp.with_suffix(".info.txt")
            info.write_text(
                "ZYNTRASEC // ACL BACKUP DETAILS\n"
                "="*72+"\n"
                f"BACKUP FILE      : {bp}\n"
                f"CREATED          : {details['created_at']}\n"
                f"COMPUTER         : {details['computer_name']}\n"
                f"WINDOWS ACCOUNT  : {details['windows_account']}\n"
                f"SELECTED USER    : {details['selected_acl_user']}\n"
                f"TARGET           : {details['target']}\n"
                f"ACTION           : {details['action']}\n"
                f"SCOPE            : {details['scope']}\n"
                f"RECURSIVE        : {details['recursive']}\n"
                "BACKUP FORMAT    : icacls /save (ROLLBACK compatible)\n"
                "\nICACLS RESULT\n"+"-"*72+"\n"+(icacls_output.strip()[-10000:] if icacls_output else "(no output)")+"\n",
                encoding="utf-8"
            )
            self.logit(f"ACL backup details: {meta}; info={info}")
            return meta,info
        except Exception as e:
            self.logit(f"ACL backup metadata warning: {e}")
            return None,None

    def _acl_icacls_success(self, rc, out):
        """Treat icacls output as successful when it reports zero failed files.
        Some icacls operations can return a non-zero code even though the requested
        ACL operation completed with 0 failed files; do not label that as FAILED.
        """
        text = out or ""
        low = text.lower()
        if rc == 0:
            return True
        m = re.search(r"successfully processed\s+(\d+)\s+files;\s+failed processing\s+(\d+)\s+files", low)
        if m and int(m.group(2)) == 0:
            return True
        # PowerShell Set-Acl actions may return a non-zero code because of
        # CLIXML progress records even though the operation completed.
        # Treat an explicit successful object count as success unless an
        # actual error is present.
        updated = re.search(r"updated\s+(\d+)\s+object(?:s)?\.?", low)
        error_markers = (
            "access is denied", "cannot find the path", "cannot find the file",
            "exception", "terminatingerror", "fullyqualifiederrorid",
            "categoryinfo :", "error:", "failed to"
        )
        if updated and int(updated.group(1)) >= 0 and not any(x in low for x in error_markers):
            return True
        return False

    def check_acl(self):
        path=self.apath.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("ACL / Folders","Select a valid file or folder first.");return
        self.output_show("ACL / FOLDERS","CHECK","Checking ACL...","RUNNING")
        def done(r):
            self.output_show("ACL / FOLDERS","CHECK",r[1] or "(no output)","SUCCESS" if self._acl_icacls_success(r[0],r[1]) else "FAILED")
            self.logit("ACL checked")
        self._async_job(lambda:run(f'icacls "{path}"',30),done,"CHECKING ACL...")

    def _resolve_local_sid(self,user):
        # Resolve the selected local account without nesting PowerShell inside
        # cmd.exe. This avoids quote/escaping failures with local usernames.
        try:
            account = f"{os.environ.get('COMPUTERNAME','')}\\{user.replace(chr(92), '')}"
            ps_script = (
                "$ErrorActionPreference='Stop';"
                f"$a=New-Object System.Security.Principal.NTAccount('{account.replace(chr(39), chr(39)*2)}');"
                "$s=$a.Translate([System.Security.Principal.SecurityIdentifier]);"
                "Write-Output $s.Value"
            )
            rc,out=ps(ps_script,30)
            if rc==0 and out.strip():
                return out.strip().splitlines()[-1].strip()
        except Exception:
            pass

        # Fallback: resolve from the actual ACL principal name, which is
        # reliable even when USERDOMAIN/COMPUTERNAME differs from the account.
        try:
            rc,out=run(f'icacls "{self.apath.get().strip()}"',30)
            target=(user or "").lower()
            for line in out.splitlines():
                if ":" not in line:
                    continue
                principal=line.split(":",1)[0].strip()
                if principal.lower().endswith("\\" + target) or principal.lower()==target:
                    ps_script=(
                        "$ErrorActionPreference='Stop';"
                        f"$a=New-Object System.Security.Principal.NTAccount('{principal.replace(chr(39), chr(39)*2)}');"
                        "$s=$a.Translate([System.Security.Principal.SecurityIdentifier]);"
                        "Write-Output $s.Value"
                    )
                    rc2,out2=ps(ps_script,30)
                    if rc2==0 and out2.strip():
                        return out2.strip().splitlines()[-1].strip()
        except Exception:
            pass
        return ""

    def check_acl_user(self):
        path,user=self._acl_target()
        if not path:return
        sid=self._resolve_local_sid(user)
        scope=self._acl_scope()
        root_rc,root=run(f'icacls "{path}"',30)
        if not sid:
            self.output_show(
                "ACL / FOLDERS","CHECK USER ACCESS",
                f"TARGET: {path}\nUSER: {user}\n\n"
                "SID: COULD NOT RESOLVE\n\n"
                "ROOT ACL\n"+"="*70+"\n"+(root or "(no ACL output)"),
                "FAILED"
            )
            self.logit(f"ACL user access SID resolution failed: {path} -> {user}")
            return
        rc,out=run(f'icacls "{path}" /findsid {sid} {scope}',60)
        text_out=(
            f"TARGET: {path}\nUSER: {user}\nSID: {sid}\n\n"
            f"USER-SPECIFIC ACE SEARCH\n{'='*70}\n{out or '(no matching ACE found)'}\n\n"
            f"ROOT ACL\n{'='*70}\n{root}"
        )
        root_low = (root or "").lower()
        user_present = (user.lower() in root_low) or (f"\\{user.lower()}" in root_low)
        status = "SUCCESS" if self._acl_icacls_success(root_rc, root) and user_present else ("REVIEW" if self._acl_icacls_success(root_rc, root) else "FAILED")
        text_out += f"\n\nRESULT: {'MATCHING USER ACE FOUND' if user_present else 'NO MATCHING USER ACE FOUND'}"
        self.output_show("ACL / FOLDERS","CHECK USER ACCESS",text_out,status)
        self.logit(f"ACL user access checked: {path} -> {user}")

    def acl_dry_run(self):
        path,user=self._acl_target()
        if not path:return
        rc,out=run(f'icacls "{path}"',30)
        # DRY RUN is read-only, but icacls can report a non-zero code while
        # still returning a complete ACL with zero failed files. Use the same
        # normalized success logic as the other ACL actions so this is not a
        # false FAILED status.
        if not self._acl_icacls_success(rc,out):
            self.output_show("ACL / FOLDERS","DRY RUN",out or "ACL read failed","FAILED");return

        rows=out.splitlines()
        broad=[]
        inherited=[]
        explicit=[]
        for line in rows:
            low=line.lower()
            for p in ("builtin\\users","nt authority\\authenticated users","everyone"):
                if p in low:
                    broad.append(line.strip())
                    if "(i)" in low:
                        inherited.append(line.strip())
                    else:
                        explicit.append(line.strip())

        scope="FOLDER + ALL SUBFOLDERS/FILES" if self.acl_recursive.get() else "THIS FOLDER ONLY"
        plan=[
            f"TARGET: {path}",
            f"USER: {user}",
            f"SCOPE: {scope}",
            "",
            "PLANNED CHANGE:",
            "  • Backup current ACL first",
            "  • Preserve SYSTEM",
            "  • Preserve BUILTIN\\Administrators",
            "  • Preserve unrelated explicit ACEs",
            "  • Remove broad Users / Authenticated Users / Everyone access only when required",
        ]

        if inherited:
            plan += [
                "",
                "INHERITED BROAD ACEs DETECTED:",
                *[f"  • {x}" for x in inherited],
                "",
                "Because these ACEs are inherited, a child-only change requires",
                "inheritance to be disabled with inherited ACEs copied first.",
                "The copied unrelated ACEs will then be preserved."
            ]
        elif explicit:
            plan += [
                "",
                "EXPLICIT BROAD ACEs DETECTED:",
                *[f"  • {x}" for x in explicit]
            ]
        else:
            plan += ["", "BROAD PRINCIPALS FOUND: (none detected)"]

        plan += ["", "NO CHANGES WERE MADE."]
        self.output_show("ACL / FOLDERS","DRY RUN","\n".join(plan),"SUCCESS")
        self.logit(f"ACL inheritance-aware dry run: {path} -> {user}")

    def acl_backup(self):
        path=self.apath.get().strip()
        user=self.acl_user.get().strip() or "unknown"
        if not path or not os.path.exists(path):
            messagebox.showwarning("ACL / Folders","Select a valid file or folder first.");return
        safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", user)
        p=self.backup_root/f"ZYNTRASEC_ACL_{safe_user}_{datetime.now():%Y%m%d_%H%M%S}.txt"
        scope="ALL SUBFOLDERS/FILES" if self.acl_recursive.get() else "THIS FOLDER ONLY"
        rc,out=run(f'icacls "{path}" /save "{p}" /t /c',timeout=600)
        self.logit(f"ACL backup: {p}")
        if self._acl_icacls_success(rc,out) and p.exists():
            meta,info=self._save_acl_backup_details(p,path,user,"BACKUP",scope,out)
            details=(f"ACL backup saved:\n{p}\n\n"
                     f"USER: {user}\nTARGET: {path}\nSCOPE: {scope}\n"
                     f"COMPUTER: {os.environ.get('COMPUTERNAME') or platform.node()}\n"
                     f"WINDOWS ACCOUNT: {os.environ.get('USERNAME') or 'unknown'}\n\n"
                     f"DETAILS JSON: {meta or 'metadata write failed'}\n"
                     f"DETAILS TXT: {info or 'metadata write failed'}\n\n"
                     f"{out.strip()}")
            self.output_show("ACL / FOLDERS","BACKUP",details,"SUCCESS")
            messagebox.showinfo("Backup complete",f"ACL backup saved:\n{p}\n\nDetails:\n{meta}")
        else:
            self.output_show("ACL / FOLDERS","BACKUP",out[-5000:],"FAILED")
            messagebox.showwarning("ACL backup",out[-3000:])

    def _apply_acl(self, action_name):
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator.");return
        path,user=self._acl_target()
        if not path:return

        recursive=self.acl_recursive.get()
        scope="ALL SUBFOLDERS/FILES" if recursive else "THIS FOLDER ONLY"

        # Recursive inheritance rewriting is intentionally not automatic:
        # it can alter permissions on many child objects. The safe default is
        # root-only. The user can still use the existing backup/verify tools.
        if recursive:
            if not messagebox.askyesno(
                "Recursive ACL change",
                "Recursive mode can change permissions on many files/folders.\n\n"
                "For safety, ZYNTRASEC will NOT break inheritance recursively.\n"
                "It will only apply the selected user grant/remove operation to the tree.\n\n"
                "Continue?"
            ):
                return

        # Read current root ACL and detect inherited broad ACEs.
        root_rc,root_acl=run(f'icacls "{path}"',30)
        if root_rc!=0:
            self.output_show("ACL / FOLDERS",action_name,root_acl or "Could not read ACL","FAILED")
            return

        low=root_acl.lower()
        inherited_broad = any(
            p in low and "(i)" in low
            for p in ("builtin\\users","nt authority\\authenticated users","everyone")
        )

        msg=(f"Target:\n{path}\n\n"
             f"Selected user: {user}\n"
             f"Scope: {scope}\n\n"
             "ZYNTRASEC will first create an ACL backup.\n"
             "SYSTEM and BUILTIN\\Administrators will be preserved.\n"
             "Unrelated explicit ACEs will be preserved.\n\n")

        if inherited_broad and not recursive:
            msg += (
                "Inherited broad access was detected (Users / Authenticated Users / Everyone).\n"
                "For THIS FOLDER ONLY, inheritance will be disabled with inherited ACEs COPIED,\n"
                "then only the broad principals will be removed.\n"
                "This does not change the parent folder.\n\n"
            )
        else:
            msg += (
                "Only broad access principals (Users, Authenticated Users, Everyone)\n"
                "will be targeted where present.\n\n"
            )

        msg += "Continue?"
        if not messagebox.askyesno(action_name,msg): return

        safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", user or "unknown")
        backup_path=self.backup_root/f"ZYNTRASEC_ACL_PRECHANGE_{safe_user}_{datetime.now():%Y%m%d_%H%M%S}.txt"
        brc,bout=run(f'icacls "{path}" /save "{backup_path}" /t /c',timeout=600)
        if not self._acl_icacls_success(brc,bout) or not backup_path.exists():
            self.output_show("ACL / FOLDERS",action_name,bout[-4000:] or "ACL backup failed","FAILED")
            messagebox.showerror("ACL backup failed",bout[-3000:] or "Could not create ACL backup.")
            return

        self._save_acl_backup_details(backup_path,path,user,action_name,scope,bout)

        scope_cmd="/T /C" if recursive else "/C"
        errors=[]
        actions=[]

        # For a non-recursive child-only change, copy inherited ACEs to explicit
        # entries before removing broad principals. This is what makes
        # BUILTIN\Users:(I)(RX) removable on the selected folder without
        # changing the parent's ACL.
        if inherited_broad and not recursive:
            rc,inherit_out=run(f'icacls "{path}" /inheritance:d',timeout=120)
            if rc!=0:
                errors.append("Disable inheritance/copy inherited ACEs: " + inherit_out[-1200:])
            else:
                actions.append("Inheritance disabled for target; inherited ACEs copied.")

        for principal in ("BUILTIN\\Users","NT AUTHORITY\\Authenticated Users","Everyone"):
            prc,pout=run(f'icacls "{path}" /remove "{principal}" {scope_cmd}',timeout=600)
            plow=(pout or "").lower()
            if self._acl_icacls_success(prc,pout) or "no mapping between account names and security ids" in plow or "not found" in plow or "no such file or directory" in plow:
                actions.append(f"Removed broad principal where present: {principal}")
            else:
                errors.append(f"{principal}: {pout[-700:]}")

        grc,gout=run(f'icacls "{path}" /grant "{user}":(OI)(CI)F {scope_cmd}',timeout=600)
        grant_ok=self._acl_icacls_success(grc,gout)
        if not grant_ok:
            errors.append(f"{user}: {gout[-1000:]}")
        else:
            actions.append(f"Granted {user}: Full Control")

        # Verify root ACL.
        vrc,verify=run(f'icacls "{path}"',30)
        vlow=verify.lower()

        # Parse the actual ACL principals instead of substring matching.
        # A target such as D:\PCYB contains the same text as the user name
        # "pcyb", which previously produced false status decisions.
        user_l=user.lower()
        computer_l=os.environ.get("COMPUTERNAME","").lower()
        user_ok=False
        for raw_line in (verify or "").splitlines():
            line=raw_line.strip()
            low_line=line.lower()
            # icacls may put the first ACE on the same line as the target path.
            candidates=[]
            if computer_l:
                candidates.append(f"{computer_l}\\{user_l}:")
            candidates.append(f"{user_l}:")
            if any(c in low_line for c in candidates):
                user_ok=True
                break

        system_ok=("nt authority\\system:" in vlow or "nt authority\\system" in vlow)
        admin_ok=("builtin\\administrators:" in vlow or "builtin\\administrators" in vlow)

        remaining_broad=[
            line.strip() for line in (verify or "").splitlines()
            if any(p in line.lower() for p in (
                "builtin\\users:","nt authority\\authenticated users:","everyone:"
            ))
        ]

        verify_ok=self._acl_icacls_success(vrc,verify)
        # LOCK TO USER is determined by the final readable ACL state. A
        # successful final state must not become FAILED merely because the
        # PowerShell/icacls process returned a non-zero code or emitted
        # progress/CLIXML text.
        final_acl_ok = verify_ok and user_ok and system_ok and admin_ok and not remaining_broad
        # Final readable ACL state is authoritative for LOCK TO USER.
        # Do not search for the literal phrase "failed processing" in successful
        # icacls output because it always contains "Failed processing 0 files".
        status = "SUCCESS" if final_acl_ok else ("REVIEW" if verify_ok else "FAILED")
        report=(
            f"ACTION: {action_name}\nTARGET: {path}\nUSER: {user}\nSCOPE: {scope}\n\n"
            f"Selected user: {'PRESENT' if user_ok else 'NOT FOUND'}\n"
            f"SYSTEM: {'PRESERVED' if system_ok else 'MISSING'}\n"
            f"Administrators: {'PRESERVED' if admin_ok else 'MISSING'}\n"
            f"Broad ACEs remaining on root: {len(remaining_broad)}\n"
            f"Grant command: {'SUCCESS' if grant_ok else 'NONZERO / FINAL ACL CHECK USED'}\n"
            f"Backup: {backup_path}\n\n"
            "ACTIONS:\n" + "\n".join(f"  • {a}" for a in actions)
        )
        if remaining_broad:
            report += "\n\nREMAINING BROAD ACEs:\n" + "\n".join(f"  • {x}" for x in remaining_broad)
        if errors:
            report += "\n\nWARNINGS:\n" + "\n".join(errors)

        self.output_show(
            "ACL / FOLDERS",action_name,
            report+"\n\nROOT ACL\n"+"-"*70+"\n"+verify,
            status
        )
        self.logit(f'ACL {action_name}: {path} -> {user}; inheritance-aware; backup={backup_path}')

        if status=="SUCCESS":
            messagebox.showinfo("ACL updated",report)
        else:
            messagebox.showwarning("ACL update / verification",report)

    def admins_only_acl(self):
        """Replace target DACL with SYSTEM + BUILTIN\\Administrators Full Control."""
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator."); return
        path=self.apath.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("ACL / Folders","Select a valid file or folder first."); return
        recursive=self.acl_recursive.get()
        scope="ALL SUBFOLDERS/FILES" if recursive else "THIS FOLDER ONLY"
        confirm=(f"ADMINISTRATORS ONLY\n\nTarget:\n{path}\n\nScope: {scope}\n\n"
                 "The target DACL will be rebuilt with ONLY:\n"
                 "  • BUILTIN\\Administrators = Full Control\n"
                 "  • NT AUTHORITY\\SYSTEM = Full Control\n\n"
                 "Other user/group access on the target will be removed.\n"
                 "Current ACL is backed up first.\n"
                 "Parent folder is NOT modified in non-recursive mode.\n\nContinue?")
        if not messagebox.askyesno("ADMINISTRATORS ONLY",confirm): return

        safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", user or "unknown")
        backup_path=self.backup_root/f"ZYNTRASEC_ACL_ADMIN_ONLY_PRECHANGE_{safe_user}_{datetime.now():%Y%m%d_%H%M%S}.txt"
        brc,bout=run(f'icacls "{path}" /save "{backup_path}" /t /c',timeout=600)
        if not self._acl_icacls_success(brc,bout) or not backup_path.exists():
            self.output_show("ACL / FOLDERS","ADMINISTRATORS ONLY",bout[-4000:] or "ACL backup failed","FAILED")
            messagebox.showerror("ACL backup failed",bout[-3000:] or "Could not create ACL backup.")
            return

        self._save_acl_backup_details(backup_path,path,user,"ADMINISTRATORS ONLY",scope,bout)

        ps = """param([string]$Target,[bool]$Recursive)
$ErrorActionPreference='Stop'
$items=@()
if($Recursive){
  $items += Get-Item -LiteralPath $Target -Force
  $items += Get-ChildItem -LiteralPath $Target -Recurse -Force -ErrorAction Stop
}else{
  $items += Get-Item -LiteralPath $Target -Force
}
foreach($item in $items){
  $acl=Get-Acl -LiteralPath $item.FullName
  $acl.SetAccessRuleProtection($true,$false)
  foreach($rule in @($acl.Access)){[void]$acl.RemoveAccessRuleSpecific($rule)}
  $inherit=[System.Security.AccessControl.InheritanceFlags]::None
  if($item.PSIsContainer){$inherit=[System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit}
  $prop=[System.Security.AccessControl.PropagationFlags]::None
  $allow=[System.Security.AccessControl.AccessControlType]::Allow
  $full=[System.Security.AccessControl.FileSystemRights]::FullControl
  [void]$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('SYSTEM',$full,$inherit,$prop,$allow)))
  [void]$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('BUILTIN\\Administrators',$full,$inherit,$prop,$allow)))
  Set-Acl -LiteralPath $item.FullName -AclObject $acl
}
Write-Output ("Updated {0} object(s)." -f $items.Count)
"""
        import base64
        target_b64=base64.b64encode(path.encode('utf-8')).decode('ascii')
        ps2=ps.replace('param([string]$Target,[bool]$Recursive)', "$Target=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+target_b64+"')); $Recursive="+('$true' if recursive else '$false'))
        enc=base64.b64encode(ps2.encode('utf-16le')).decode('ascii')
        rc,out=run(f'powershell.exe -NoProfile -EncodedCommand {enc}',timeout=900)
        verify_rc,verify=run(f'icacls "{path}"',30)
        low=verify.lower()
        sys_ok='nt authority\\system' in low
        adm_ok=('builtin\\administrators' in low)
        broad=[ln.strip() for ln in verify.splitlines() if any(x in ln.lower() for x in ('builtin\\users','nt authority\\authenticated users','everyone'))]
        status='SUCCESS' if self._acl_icacls_success(rc,out) and self._acl_icacls_success(verify_rc,verify) and sys_ok and adm_ok and not broad else ('REVIEW' if self._acl_icacls_success(rc,out) and self._acl_icacls_success(verify_rc,verify) else 'FAILED')
        report=(f"ACTION: ADMINISTRATORS ONLY\nTARGET: {path}\nSCOPE: {scope}\n\n"
                f"SYSTEM: {'PRESERVED' if sys_ok else 'MISSING'}\n"
                f"Administrators: {'PRESERVED' if adm_ok else 'MISSING'}\n"
                f"Broad ACEs remaining: {len(broad)}\n"
                f"Backup: {backup_path}\n\nRESULT:\n{out.strip() or '(no output)'}\n\nROOT ACL\n{'-'*70}\n{verify}")
        if broad: report += "\nBROAD ACCESS STILL PRESENT:\n"+"\n".join(broad)
        self.output_show("ACL / FOLDERS","ADMINISTRATORS ONLY",report,status)
        self.logit(f'ACL ADMINISTRATORS ONLY: {path}; backup={backup_path}')
        if status=='SUCCESS': messagebox.showinfo("ACL updated",report)
        else: messagebox.showwarning("ACL update / verification",report)

    def allow_only_acl(self):
        """Restrict the target to selected user + SYSTEM + Administrators without freezing Tkinter."""
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator."); return
        path,user=self._acl_target()
        if not path:return
        recursive=self.acl_recursive.get()
        scope="ALL SUBFOLDERS/FILES" if recursive else "THIS FOLDER ONLY"
        confirm=(f"ALLOW ONLY\n\nTarget:\n{path}\n\nSelected user: {user}\nScope: {scope}\n\n"
                 "The target DACL will be rebuilt with ONLY:\n"
                 f"  • {user} = Full Control\n"
                 "  • BUILTIN\\Administrators = Full Control\n"
                 "  • NT AUTHORITY\\SYSTEM = Full Control\n\n"
                 "All other target ACEs will be removed.\n"
                 "Parent folder is NOT modified in non-recursive mode.\n"
                 "Current ACL is backed up first.\n\nContinue?")
        if not messagebox.askyesno("ALLOW ONLY",confirm): return

        safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", user or "unknown")
        backup_path=self.backup_root/f"ZYNTRASEC_ACL_ALLOW_ONLY_PRECHANGE_{safe_user}_{datetime.now():%Y%m%d_%H%M%S}.txt"
        self.output_show("ACL / FOLDERS","ALLOW ONLY",
                         f"TARGET: {path}\nUSER: {user}\nSCOPE: {scope}\n\nStarting backup and ACL update...\nBACKUP MODE: {'RECURSIVE' if recursive else 'THIS FOLDER ONLY'}\nUI remains responsive while the operation runs.","RUNNING")

        def worker():
            # All potentially long filesystem/PowerShell work runs off the Tkinter UI thread.
            # Do not recursively scan 57k+ files when the user selected THIS FOLDER ONLY.
            # /T is used only for the explicit recursive mode.
            backup_flags = "/t /c" if recursive else "/c"
            brc,bout=run(f'icacls "{path}" /save "{backup_path}" {backup_flags}',timeout=600)
            backup_ok=self._acl_icacls_success(brc,bout) and backup_path.exists()
            if not backup_ok:
                return {"phase":"backup","brc":brc,"bout":bout,"backup":str(backup_path),"path":path,"user":user,"scope":scope}
            self._save_acl_backup_details(backup_path,path,user,"ALLOW ONLY",scope,bout)

            ps = """param([string]$Target,[string]$User,[bool]$Recursive)
$ErrorActionPreference='Stop'
$items=@()
if($Recursive){
  $items += Get-Item -LiteralPath $Target -Force
  $items += Get-ChildItem -LiteralPath $Target -Recurse -Force -ErrorAction Stop
}else{
  $items += Get-Item -LiteralPath $Target -Force
}
foreach($item in $items){
  $acl=Get-Acl -LiteralPath $item.FullName
  $acl.SetAccessRuleProtection($true,$false)
  foreach($rule in @($acl.Access)){[void]$acl.RemoveAccessRuleSpecific($rule)}
  $inherit=[System.Security.AccessControl.InheritanceFlags]::None
  if($item.PSIsContainer){$inherit=[System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit}
  $prop=[System.Security.AccessControl.PropagationFlags]::None
  $allow=[System.Security.AccessControl.AccessControlType]::Allow
  $full=[System.Security.AccessControl.FileSystemRights]::FullControl
  [void]$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($User,$full,$inherit,$prop,$allow)))
  [void]$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('SYSTEM',$full,$inherit,$prop,$allow)))
  [void]$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule('BUILTIN\\Administrators',$full,$inherit,$prop,$allow)))
  Set-Acl -LiteralPath $item.FullName -AclObject $acl
}
Write-Output ("Updated {0} object(s)." -f $items.Count)
"""
            import base64
            target_b64=base64.b64encode(path.encode('utf-8')).decode('ascii')
            user_b64=base64.b64encode(user.encode('utf-8')).decode('ascii')
            ps2=ps.replace('param([string]$Target,[string]$User,[bool]$Recursive)',
                "$Target=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+target_b64+"')); $User=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+user_b64+"')); $Recursive="+('$true' if recursive else '$false'))
            enc=base64.b64encode(ps2.encode('utf-16le')).decode('ascii')
            rc,out=run(f'powershell.exe -NoProfile -EncodedCommand {enc}',timeout=900)
            verify_rc,verify=run(f'icacls "{path}"',30)
            low=(verify or '').lower()
            user_ok=user.lower() in low
            sys_ok='nt authority\\system' in low
            adm_ok='builtin\\administrators' in low
            broad=[ln.strip() for ln in (verify or '').splitlines() if any(x in ln.lower() for x in ('builtin\\users','nt authority\\authenticated users','everyone'))]
            action_ok=self._acl_icacls_success(rc,out)
            verify_ok=self._acl_icacls_success(verify_rc,verify)
            status='SUCCESS' if action_ok and verify_ok and user_ok and sys_ok and adm_ok and not broad else ('REVIEW' if action_ok and verify_ok else 'FAILED')
            report=(f"ACTION: ALLOW ONLY\nTARGET: {path}\nUSER: {user}\nSCOPE: {scope}\n\n"
                    f"Selected user: {'PRESENT' if user_ok else 'NOT FOUND'}\n"
                    f"SYSTEM: {'PRESERVED' if sys_ok else 'MISSING'}\n"
                    f"Administrators: {'PRESERVED' if adm_ok else 'MISSING'}\n"
                    f"Broad ACEs remaining: {len(broad)}\n"
                    f"Backup: {backup_path}\n\nRESULT:\n{out.strip() or '(no output)'}\n\nROOT ACL\n{'-'*70}\n{verify}")
            if broad: report += "\nBROAD ACCESS STILL PRESENT:\n"+"\n".join(broad)
            return {"phase":"done","status":status,"report":report,"path":path,"user":user,"backup":str(backup_path)}

        def done(result):
            if result.get("phase")=="backup":
                bout=result.get("bout") or "ACL backup failed"
                self.output_show("ACL / FOLDERS","ALLOW ONLY",bout,"FAILED")
                messagebox.showerror("ACL backup failed",bout[-3000:])
                return
            status=result["status"]
            report=result["report"]
            self.output_show("ACL / FOLDERS","ALLOW ONLY",report,status)
            self.logit(f'ACL ALLOW ONLY: {result["path"]} -> {result["user"]}; backup={result["backup"]}')
            if status=='SUCCESS': messagebox.showinfo("ACL updated",report)
            else: messagebox.showwarning("ACL update / verification",report)

        self._async_job(worker,done,"ACL ALLOW ONLY...")

    def lock_acl_to_user(self):
        self._apply_acl("LOCK TO USER")

    def restore_user_access(self):
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator.");return

        path,user=self._acl_target()
        if not path:return

        # Backup first so the change can be rolled back.
        safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", user or "unknown")
        backup_path=self.backup_root/f"ZYNTRASEC_ACL_PRE_RESTORE_{safe_user}_{datetime.now():%Y%m%d_%H%M%S}.txt"
        brc,bout=run(f'icacls "{path}" /save "{backup_path}" /t /c',timeout=600)
        if not self._acl_icacls_success(brc,bout):
            self.output_show("ACL / FOLDERS","RESTORE USER ACCESS",bout[-5000:] or "ACL backup failed","FAILED")
            messagebox.showerror("ACL backup failed",bout[-3000:])
            return

        scope = "ALL SUBFOLDERS/FILES" if self.acl_recursive.get() else "THIS FOLDER ONLY"
        self._save_acl_backup_details(backup_path,path,user,"RESTORE USER ACCESS",scope,bout)

        level = tk.StringVar(value="M")
        dlg = tk.Toplevel(self)
        dlg.title("RESTORE USER ACCESS")
        dlg.configure(bg=BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False,False)

        tk.Label(
            dlg,text=f"User: {user}\nFolder: {path}\n\nChoose the permission to restore:",
            bg=BG,fg=TEXT,justify="left"
        ).pack(padx=18,pady=(16,8),anchor="w")

        for value,label in [
            ("RX","READ / EXECUTE"),
            ("M","MODIFY"),
            ("F","FULL CONTROL")
        ]:
            ttk.Radiobutton(dlg,text=label,variable=level,value=value).pack(
                padx=18,pady=3,anchor="w"
            )

        recursive = self.acl_recursive.get()
        scope_cmd = "/T /C" if recursive else "/C"

        def apply():
            dlg.destroy()
            perm=level.get()
            # Restore only the selected user's ACE. Do not reset inheritance,
            # remove unrelated principals, or change SYSTEM/Administrators.
            rc,out=run(
                f'icacls "{path}" /grant "{user}":({perm}) {scope_cmd}',
                timeout=600
            )

            verify_rc,verify=run(f'icacls "{path}"',30)
            low=verify.lower()
            user_ok=(user.lower() in low)
            system_ok=("nt authority\\system" in low)
            admin_ok=("builtin\\administrators" in low)

            status="SUCCESS" if self._acl_icacls_success(rc,out) and self._acl_icacls_success(verify_rc,verify) and user_ok and system_ok and admin_ok else ("REVIEW" if self._acl_icacls_success(rc,out) and self._acl_icacls_success(verify_rc,verify) else "FAILED")
            report=(
                f"USER ACCESS RESTORE\n"
                f"TARGET: {path}\n"
                f"USER: {user}\n"
                f"PERMISSION: {perm}\n"
                f"SCOPE: {'ALL SUBFOLDERS/FILES' if recursive else 'THIS FOLDER ONLY'}\n\n"
                f"Selected user: {'PRESENT' if user_ok else 'NOT FOUND'}\n"
                f"SYSTEM: {'PRESERVED' if system_ok else 'MISSING'}\n"
                f"Administrators: {'PRESERVED' if admin_ok else 'MISSING'}\n"
                f"Backup: {backup_path}\n\n"
                f"COMMAND OUTPUT\n{'-'*70}\n{out or '(no output)'}\n\n"
                f"ROOT ACL\n{'-'*70}\n{verify}"
            )
            self.output_show("ACL / FOLDERS","RESTORE USER ACCESS",report,status)
            self.logit(f"ACL restore user access: {path} -> {user} ({perm}); backup={backup_path}")

            if status=="SUCCESS":
                messagebox.showinfo(
                    "User access restored",
                    f"{user} permission restored: {perm}\n\n"
                    f"SYSTEM: PRESERVED\nAdministrators: PRESERVED\n\n"
                    f"Backup:\n{backup_path}"
                )
            else:
                messagebox.showwarning("Restore / verification",report[-5000:])

        ttk.Button(dlg,text="APPLY",command=apply).pack(side="left",padx=(18,6),pady=16)
        ttk.Button(dlg,text="CANCEL",command=dlg.destroy).pack(side="left",padx=6,pady=16)

    def remove_user_access(self):
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator.");return

        path,user=self._acl_target()
        if not path:return

        recursive=self.acl_recursive.get()
        scope_cmd="/T /C" if recursive else "/C"
        scope="ALL SUBFOLDERS/FILES" if recursive else "THIS FOLDER ONLY"

        # Backup before any ACL change.
        safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", user or "unknown")
        backup_path=self.backup_root/f"ZYNTRASEC_ACL_PRE_REMOVE_{safe_user}_{datetime.now():%Y%m%d_%H%M%S}.txt"
        brc,bout=run(f'icacls "{path}" /save "{backup_path}" /t /c',timeout=600)
        if not self._acl_icacls_success(brc,bout) or not backup_path.exists():
            self.output_show("ACL / FOLDERS","REMOVE USER ACCESS",bout[-5000:] or "ACL backup failed","FAILED")
            messagebox.showerror("ACL backup failed",bout[-3000:] or "Could not create ACL backup.")
            return

        self._save_acl_backup_details(backup_path,path,user,"REMOVE USER ACCESS",scope,bout)

        if not messagebox.askyesno(
            "REMOVE USER ACCESS",
            f"Folder:\n{path}\n\n"
            f"User: {user}\n"
            f"Scope: {scope}\n\n"
            "This removes the selected user's explicit ACE from the target.\n"
            "SYSTEM and BUILTIN\\Administrators are not changed.\n"
            "Other unrelated explicit ACEs are not changed.\n\n"
            "If the user still has access through Users/Authenticated Users,\n"
            "that group access is not automatically removed by this operation.\n\n"
            "Continue?"
        ):
            return

        rc,out=run(f'icacls "{path}" /remove "{user}" {scope_cmd}',timeout=600)

        verify_rc,verify=run(f'icacls "{path}"',30)
        low=verify.lower()
        # A principal may still appear through an inherited/group path; this
        # check is intentionally limited to the exact selected account name.
        direct_user_present=any(
            line.strip().lower().startswith(user.lower()+":")
            for line in verify.splitlines()
        )
        system_ok=("nt authority\\system" in low)
        admin_ok=("builtin\\administrators" in low)

        status="SUCCESS" if self._acl_icacls_success(rc,out) and self._acl_icacls_success(verify_rc,verify) and not direct_user_present and system_ok and admin_ok else ("REVIEW" if self._acl_icacls_success(rc,out) and self._acl_icacls_success(verify_rc,verify) else "FAILED")

        report=(
            f"REMOVE USER ACCESS\n"
            f"TARGET: {path}\n"
            f"USER: {user}\n"
            f"SCOPE: {scope}\n\n"
            f"Direct selected-user ACE: {'STILL PRESENT' if direct_user_present else 'REMOVED / NOT PRESENT'}\n"
            f"SYSTEM: {'PRESERVED' if system_ok else 'MISSING'}\n"
            f"Administrators: {'PRESERVED' if admin_ok else 'MISSING'}\n"
            f"Backup: {backup_path}\n\n"
            f"COMMAND OUTPUT\n{'-'*70}\n{out or '(no output)'}\n\n"
            f"ROOT ACL\n{'-'*70}\n{verify}"
        )

        self.output_show("ACL / FOLDERS","REMOVE USER ACCESS",report,status)
        self.logit(f"ACL remove user access: {path} -> {user}; backup={backup_path}")

        if status=="SUCCESS":
            messagebox.showinfo(
                "User access removed",
                f"Direct permission for {user} was removed.\n\n"
                "SYSTEM: PRESERVED\n"
                "Administrators: PRESERVED\n\n"
                f"Backup:\n{backup_path}\n\n"
                "Note: group-based access, if any, is separate."
            )
        else:
            messagebox.showwarning("Remove / verification",report[-5000:])

    def remove_direct_user_access(self):
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator.");return

        path,user=self._acl_target()
        if not path:return

        # Read the root ACL first and identify whether the selected account
        # has its own direct ACE. Group-based access is intentionally left alone.
        rc,acl=run(f'icacls "{path}"',30)
        if rc!=0:
            self.output_show("ACL / FOLDERS","REMOVE DIRECT USER ACCESS",
                             acl or "Could not read ACL","FAILED")
            return

        direct_lines=[]
        user_l=user.lower()
        qualified_user=f"{os.environ.get('COMPUTERNAME','')}\\{user}".lower()
        # icacls can print the drive/path and first ACE on the same line.
        # Do not split on the first colon because that is the drive letter.
        for line in acl.splitlines():
            low_line=line.lower()
            if f"{qualified_user}:" in low_line or f"{user_l}:" in low_line:
                direct_lines.append(line.strip())

        safe_user=re.sub(r"[^A-Za-z0-9._-]+", "_", user or "unknown")
        backup_path=self.backup_root/f"ZYNTRASEC_ACL_PRE_DIRECT_REMOVE_{safe_user}_{datetime.now():%Y%m%d_%H%M%S}.txt"
        brc,bout=run(f'icacls "{path}" /save "{backup_path}" /t /c',timeout=600)
        if not self._acl_icacls_success(brc,bout) or not backup_path.exists():
            self.output_show("ACL / FOLDERS","REMOVE DIRECT USER ACCESS",
                             bout[-5000:] or "ACL backup failed","FAILED")
            return

        self._save_acl_backup_details(backup_path,path,user,"REMOVE DIRECT USER ACCESS",scope,bout)

        if not direct_lines:
            self.output_show(
                "ACL / FOLDERS","REMOVE DIRECT USER ACCESS",
                f"TARGET: {path}\nUSER: {user}\n\n"
                "DIRECT USER ACE: NOT FOUND\n\n"
                "No direct permission was removed.\n"
                "The user may still have access through a group such as Users or "
                "Authenticated Users.\n\nROOT ACL\n"+"-"*70+"\n"+acl,
                "SUCCESS"
            )
            self.logit(f"Direct user ACE not found: {path} -> {user}")
            return

        if not messagebox.askyesno(
            "REMOVE DIRECT USER ACCESS",
            f"Target:\n{path}\n\n"
            f"User: {user}\n\n"
            "The following direct ACE will be removed:\n\n"
            + "\n".join(direct_lines) +
            "\n\nSYSTEM and Administrators will not be changed.\n"
            "Group permissions will NOT be removed.\n\nContinue?"
        ):
            return

        rc,out=run(f'icacls "{path}" /remove "{user}" /C',timeout=600)
        _,verify=run(f'icacls "{path}"',30)
        vlines=verify.splitlines()
        still_direct=[]
        user_l=user.lower()
        qualified_user=f"{os.environ.get('COMPUTERNAME','')}\\{user}".lower()
        for line in vlines:
            low_line=line.lower()
            if f"{qualified_user}:" in low_line or f"{user_l}:" in low_line:
                still_direct.append(line.strip())

        low=verify.lower()
        system_ok=("nt authority\\system" in low)
        admin_ok=("builtin\\administrators" in low)
        status="SUCCESS" if self._acl_icacls_success(rc,out) and not still_direct and system_ok and admin_ok else ("REVIEW" if self._acl_icacls_success(rc,out) else "FAILED")

        report=(
            f"TARGET: {path}\n"
            f"USER: {user}\n\n"
            f"Direct ACE before: FOUND\n"
            f"Direct ACE after: {'STILL PRESENT' if still_direct else 'REMOVED'}\n"
            f"SYSTEM: {'PRESERVED' if system_ok else 'MISSING'}\n"
            f"Administrators: {'PRESERVED' if admin_ok else 'MISSING'}\n"
            f"Backup: {backup_path}\n\n"
            "GROUP ACCESS WAS NOT MODIFIED.\n\n"
            "COMMAND OUTPUT\n"+"-"*70+"\n"+(out or "(no output)")+
            "\n\nROOT ACL\n"+"-"*70+"\n"+verify
        )

        self.output_show("ACL / FOLDERS","REMOVE DIRECT USER ACCESS",report,status)
        self.logit(f"Direct user ACE removed: {path} -> {user}; backup={backup_path}")

        if status=="SUCCESS":
            messagebox.showinfo(
                "Direct access removed",
                f"Direct ACL entry for {user} was removed.\n\n"
                "SYSTEM: PRESERVED\nAdministrators: PRESERVED\n"
                "Group permissions: NOT CHANGED\n\n"
                f"Backup:\n{backup_path}"
            )
        else:
            messagebox.showwarning("Remove / verification",report[-5000:])

    def verify_acl(self):
        path,user=self._acl_target()
        if not path:return
        rc,verify=run(f'icacls "{path}"',30)
        low=verify.lower()
        user_ok=(user.lower() in low)
        system_ok=("nt authority\\system" in low)
        admin_ok=("builtin\\administrators" in low)
        broad=[p for p in ("builtin\\users","nt authority\\authenticated users","everyone") if p in low]
        status="SUCCESS" if self._acl_icacls_success(rc,verify) and user_ok and system_ok and admin_ok else ("REVIEW" if self._acl_icacls_success(rc,verify) else "FAILED")
        report=(
            f"TARGET: {path}\nUSER: {user}\n\n"
            f"Selected user: {'PRESENT' if user_ok else 'NOT FOUND'}\n"
            f"SYSTEM: {'PRESENT' if system_ok else 'MISSING'}\n"
            f"Administrators: {'PRESENT' if admin_ok else 'MISSING'}\n"
            f"Broad principals on root: {', '.join(broad) if broad else '(none detected)'}\n\n"
            "ROOT ACL\n"+"-"*70+"\n"+verify
        )
        self.output_show("ACL / FOLDERS","VERIFY",report,status)
        self.logit(f"ACL verify: {path} -> {user}")

    def _select_acl_backup_with_details(self):
        """Show ACL backups with their sidecar metadata before rollback.
        Native .txt files remain untouched and rollback-compatible.
        """
        root=Path(self.backup_root)
        try:
            files=sorted(
                [x for x in root.glob("ZYNTRASEC_ACL_*.txt")
                 if x.is_file() and not x.name.lower().endswith(".info.txt")],
                key=lambda x: x.stat().st_mtime, reverse=True
            )
        except Exception:
            files=[]
        if not files:
            messagebox.showwarning("ACL / Folders","No ZYNTRASEC ACL backup files were found.")
            return None

        result={"path":None}
        dlg=tk.Toplevel(self)
        dlg.title("Select ZYNTRASEC ACL backup")
        dlg.configure(bg=BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.geometry("980x620")
        dlg.minsize(820,520)

        tk.Label(dlg,text="SELECT ACL BACKUP",bg=BG,fg=GREEN,
                 font=("Consolas",14,"bold")).pack(anchor="w",padx=14,pady=(12,4))
        tk.Label(dlg,text="Select a backup to see USER / TARGET / ACTION / SCOPE before rollback.",
                 bg=BG,fg=TEXT,font=("Consolas",9)).pack(anchor="w",padx=14,pady=(0,10))

        body=tk.Frame(dlg,bg=BG)
        body.pack(fill="both",expand=True,padx=14,pady=4)
        left=tk.Frame(body,bg=BG)
        left.pack(side="left",fill="both",expand=True)
        right=tk.Frame(body,bg=PANEL,highlightbackground=GREEN,highlightthickness=1,width=430)
        right.pack(side="right",fill="both",expand=False,padx=(10,0))
        right.pack_propagate(False)

        lb=tk.Listbox(left,bg="#020603",fg=TEXT,selectbackground="#064f2a",
                      selectforeground="#ffffff",font=("Consolas",9),
                      activestyle="none")
        sb=CyberScrollbar(left,orient="vertical",command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left",fill="both",expand=True)
        sb.pack(side="right",fill="y")

        details=tk.Text(right,bg=PANEL,fg=TEXT,insertbackground=TEXT,
                        font=("Consolas",9),wrap="word",relief="flat")
        details.pack(fill="both",expand=True,padx=10,pady=10)
        details.configure(state="disabled")

        def load_meta(bp):
            meta={}
            mp=bp.with_suffix(".json")
            try:
                if mp.exists():
                    meta=json.loads(mp.read_text(encoding="utf-8"))
            except Exception:
                meta={}
            try:
                st=bp.stat()
                size_mb=st.st_size/(1024*1024)
                modified=datetime.fromtimestamp(st.st_mtime).astimezone().strftime("%d-%m-%Y %I:%M:%S %p")
            except Exception:
                size_mb=0; modified="unknown"
            if not meta:
                # Older backups may not have sidecar metadata. Show safe fallback info.
                stem=bp.stem
                parts=stem.split("_")
                action="Metadata unavailable (older backup)"
                if "PRE" in parts and len(parts)>2:
                    try: action="PRE_"+parts[parts.index("PRE")+1]
                    except Exception: pass
                return {
                    "backup_file":str(bp),
                    "created_at":modified,
                    "computer_name":"Not saved in this older backup",
                    "windows_account":"Not saved in this older backup",
                    "selected_acl_user":"Not saved in this older backup",
                    "target":"Not saved in this older backup",
                    "action":action,
                    "scope":"Not saved in this older backup",
                    "recursive":"Unknown",
                    "backup_type":"icacls /save ACL snapshot",
                    "restore_compatible":"Unknown until icacls /restore",
                    "size":f"{size_mb:.1f} MB",
                    "modified":modified,
                    "metadata_file":"Not available"
                }
            meta["size"]=f"{size_mb:.1f} MB"
            meta["modified"]=modified
            return meta

        for bp in files:
            lb.insert("end",bp.name)

        def show_selected(event=None):
            sel=lb.curselection()
            if not sel:return
            bp=files[sel[0]]
            m=load_meta(bp)
            text=(
                "ZYNTRASEC // BACKUP DETAILS\n"
                + "="*46 + "\n"
                f"BACKUP FILE   : {bp.name}\n"
                f"ACTION        : {m.get('action','unknown')}\n"
                f"USER          : {m.get('selected_acl_user','unknown')}\n"
                f"TARGET        : {m.get('target','unknown')}\n"
                f"SCOPE         : {m.get('scope','unknown')}\n"
                f"RECURSIVE     : {m.get('recursive','unknown')}\n"
                f"COMPUTER      : {m.get('computer_name','unknown')}\n"
                f"WINDOWS USER  : {m.get('windows_account','unknown')}\n"
                f"CREATED       : {m.get('created_at','unknown')}\n"
                f"SIZE          : {m.get('size','unknown')}\n"
                f"FORMAT        : {m.get('backup_type','icacls /save')}\n"
                f"ROLLBACK      : {m.get('restore_compatible','unknown')}\n"
                f"METADATA      : {m.get('metadata_file','unknown')}\n"
            )
            details.configure(state="normal")
            details.delete("1.0","end")
            details.insert("1.0",text)
            details.configure(state="disabled")

        def choose():
            sel=lb.curselection()
            if not sel:
                messagebox.showwarning("Select backup","Select an ACL backup first.",parent=dlg)
                return
            result["path"]=str(files[sel[0]])
            dlg.destroy()

        lb.bind("<<ListboxSelect>>",show_selected)
        lb.bind("<Double-Button-1>",lambda e: choose())
        if files: lb.selection_set(0); show_selected()

        buttons=tk.Frame(dlg,bg=BG)
        buttons.pack(fill="x",padx=14,pady=(8,14))
        ttk.Button(buttons,text="SELECT BACKUP",command=choose).pack(side="left")
        ttk.Button(buttons,text="CANCEL",command=dlg.destroy).pack(side="left",padx=8)
        dlg.protocol("WM_DELETE_WINDOW",dlg.destroy)
        self.wait_window(dlg)
        return result["path"]

    def acl_rollback(self):
        if not is_admin():
            messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator.");return
        path=self.apath.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("ACL / Folders","Select the folder to restore first.");return

        backup=self._select_acl_backup_with_details()
        if not backup:return

        # Do not reject snapshots using drive-specific text matching.  icacls /save
        # snapshots can use different path representations depending on the target.
        # Let icacls /restore validate the snapshot itself.
        if not messagebox.askyesno(
            "ROLLBACK ACL",
            f"Restore ACLs from:\n{backup}\n\nto:\n{path}\n\n"
            "This restores the ACL snapshot captured by icacls /save.\nContinue?"
        ): return

        # icacls /save stores paths relative to the directory that contains the
        # saved root.  For example, saving D:\\PCYB can produce entries such as
        # PCYB\\... .  Passing D:\\PCYB directly to /restore makes icacls
        # resolve those entries as D:\\PCYB\\PCYB\\..., which causes
        # "The system cannot find the path specified".  Restore against the
        # parent directory of the original target instead.
        restore_root=os.path.dirname(os.path.normpath(path)) or (os.path.splitdrive(path)[0] + os.sep)
        # Avoid passing a quoted root ending in a backslash (e.g. "D:\") to
        # icacls. Use a harmless dot-qualified root instead ("D:\.") so the
        # command-line parser cannot treat the trailing slash as part of the quote.
        if restore_root.endswith('\\'):
            restore_root = restore_root + '.'
        rc,out=run(f'icacls "{restore_root}" /restore "{backup}" /C',timeout=600)
        ok=self._acl_icacls_success(rc,out)

        # Confirm the target ACL is readable after restore.  This is only a
        # verification step; it does not change permissions.
        vrc,verify=run(f'icacls "{path}"',30)
        verify_ok=self._acl_icacls_success(vrc,verify)
        final_ok=ok and verify_ok
        report=(
            f"BACKUP: {backup}\n"
            f"TARGET: {path}\n"
            f"RESTORE ROOT: {restore_root}\n\n"
            f"RESTORE RESULT: {'SUCCESS' if ok else 'FAILED'}\n"
            f"VERIFY RESULT: {'SUCCESS' if verify_ok else 'FAILED'}\n\n"
            "RESTORE OUTPUT\n"+'-'*70+'\n'+(out or '(no output)')+
            "\n\nTARGET ACL AFTER RESTORE\n"+'-'*70+'\n'+(verify or '(no output)')
        )
        self.output_show("ACL / FOLDERS","ROLLBACK",report,
                         "SUCCESS" if final_ok else ("REVIEW" if ok else "FAILED"))
        self.logit(f"ACL rollback: {path} <- {backup}; restore_root={restore_root}")
        if final_ok:
            messagebox.showinfo("Rollback complete",f"ACL backup restored successfully.\n\nTarget: {path}")
        else:
            messagebox.showwarning("Rollback failed",report[-5000:])

    def open_windows_security(self):
        """Open the installed Windows Security app without invoking the broken
        windowsdefender: URI handler.

        The URI can return exit code 0 even when Windows subsequently shows
        the "We can't open this windowsdefender link" shell dialog. Therefore
        the app is resolved through the installed AppX/Start Apps registration
        first, with ms-settings only as a last fallback.
        """
        # Preferred: resolve the actual installed Windows Security AppUserModelId.
        app_script = r'''$ErrorActionPreference='Stop'
$apps = @(Get-StartApps | Where-Object { $_.Name -match '^Windows Security$|Windows Security' })
if ($apps.Count -gt 0) {
    $id = $apps[0].AppID
    Start-Process -FilePath 'explorer.exe' -ArgumentList @('shell:AppsFolder\' + $id)
    Write-Output "APPID=$id"
    exit 0
}
$pkg = Get-AppxPackage -Name 'Microsoft.SecHealthUI' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pkg) {
    $family = $pkg.PackageFamilyName
    Start-Process -FilePath 'explorer.exe' -ArgumentList @('shell:AppsFolder\' + $family + '!SecHealthUI')
    Write-Output "PACKAGE=$family"
    exit 0
}
exit 2'''
        rc, out = ps(app_script, timeout=20)
        if rc == 0:
            self.output_show(
                "SECURITY CENTER", "OPEN WINDOWS SECURITY",
                "Windows Security app resolved and launch requested.\n" + out.strip(),
                "SUCCESS")
            return

        # Last resort: Settings URI. Never call windowsdefender: because that
        # handler is the one producing the shell popup seen on this PC.
        rc2, out2 = ps("Start-Process -FilePath 'ms-settings:windowsdefender'", timeout=20)
        if rc2 == 0:
            self.output_show(
                "SECURITY CENTER", "OPEN WINDOWS SECURITY",
                "Windows Security app registration was not found.\n"
                "Opened the Windows Security settings page as fallback.",
                "SUCCESS")
            return

        self.output_show(
            "SECURITY CENTER", "OPEN WINDOWS SECURITY",
            "Windows Security app could not be resolved.\n\n"
            + (out.strip() or "App lookup failed.")
            + "\n"
            + (out2.strip() or "Settings fallback failed."),
            "FAILED")

    def security(self):
        self.header("🛡 SECURITY CENTER", "Live Windows security status. Read-only checks, project-only Defender exclusion, and Windows Security access.")
        outer=tk.Frame(self.page,bg=BG); outer.pack(fill="both",expand=True,padx=8,pady=(4,8))
        status_frame=tk.Frame(outer,bg=PANEL,highlightthickness=1,highlightbackground="#146b38"); status_frame.pack(fill="x",pady=(0,8))
        tk.Label(status_frame,text="SECURITY STATUS",bg=PANEL,fg=GREEN,font=("Consolas",11,"bold")).pack(anchor="w",padx=14,pady=(10,2))
        tk.Label(status_frame,text="Read-only live checks • ZYNTRASEC does not disable Firewall, Defender, UAC or Memory Integrity",bg=PANEL,fg=MUTED,font=("Consolas",9)).pack(anchor="w",padx=14,pady=(0,10))
        cards=tk.Frame(status_frame,bg=PANEL); cards.pack(fill="x",padx=10,pady=(0,12))
        for c in range(2): cards.grid_columnconfigure(c,weight=1)
        card_widgets={}
        def make_card(row,col,name):
            f=tk.Frame(cards,bg="#06100a",highlightthickness=1,highlightbackground="#146b38"); f.grid(row=row,column=col,sticky="nsew",padx=5,pady=5)
            top=tk.Frame(f,bg="#06100a"); top.pack(fill="x",padx=12,pady=(10,2))
            tk.Label(top,text=name.upper(),bg="#06100a",fg=TEXT,font=("Consolas",10,"bold")).pack(side="left")
            dot=tk.Label(top,text="●",bg="#06100a",fg=MUTED,font=("Consolas",12,"bold")); dot.pack(side="right")
            state=tk.Label(f,text="CHECKING...",bg="#06100a",fg=MUTED,font=("Consolas",18,"bold")); state.pack(anchor="w",padx=12,pady=(3,0))
            detail=tk.Label(f,text="Waiting for status...",bg="#06100a",fg=MUTED,font=("Consolas",9)); detail.pack(anchor="w",padx=12,pady=(0,11))
            card_widgets[name]=(state,detail,dot)
        for row,col,name in [(0,0,"Firewall"),(0,1,"Defender RTP"),(1,0,"UAC"),(1,1,"Memory Integrity")]: make_card(row,col,name)
        action=tk.Frame(outer,bg=BG); action.pack(fill="x",pady=(0,7))
        refresh_btn=ttk.Button(action,text="REFRESH SECURITY STATUS"); refresh_btn.pack(side="left",padx=(0,7))
        auto_btn=ttk.Button(action,text="AUTO CHECK + OPEN WINDOWS SECURITY"); auto_btn.pack(side="left",padx=(0,7))
        excl=tk.Frame(outer,bg=PANEL,highlightthickness=1,highlightbackground="#146b38"); excl.pack(fill="x",pady=(0,7))
        tk.Label(excl,text="ZYNTRASEC PROJECT EXCLUSION",bg=PANEL,fg=GREEN,font=("Consolas",10,"bold")).pack(anchor="w",padx=12,pady=(8,2))
        tk.Label(excl,text="Choose only your own local development/build folder. Defender remains enabled globally.",bg=PANEL,fg=MUTED,font=("Consolas",8)).pack(anchor="w",padx=12,pady=(0,7))
        excl_status=tk.Label(excl,text="No project folder selected",bg=PANEL,fg=TEXT,font=("Consolas",8)); excl_status.pack(anchor="w",padx=12,pady=(0,7))
        excl_action=tk.Frame(excl,bg=PANEL); excl_action.pack(fill="x",padx=10,pady=(0,8))
        def choose_project_folder():
            if not is_admin(): messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator to manage a Defender exclusion."); return
            folder=filedialog.askdirectory(title="Choose ZYNTRASEC Project / Build Folder")
            if not folder:return
            if folder.startswith("\\"): messagebox.showwarning("Project Exclusion","Please choose a local Windows folder, not a network/UNC path."); return
            if not os.path.isdir(folder): messagebox.showerror("Project Exclusion","Selected folder is not accessible."); return
            esc=folder.replace("'","''"); self.output_show("SECURITY CENTER","PROJECT EXCLUSION","Adding Defender exclusion...","RUNNING")
            def work(): return (*((lambda r:(r[0],r[1]))(ps(f"Add-MpPreference -ExclusionPath '{esc}'",timeout=30))),folder)
            def done(r):
                rc,out,folder=r
                if rc==0: excl_status.config(text=f"EXCLUDED: {folder}",fg=GREEN); self.output_show("SECURITY CENTER","PROJECT EXCLUSION ADDED",f"Folder: {folder}\nDefender remains enabled globally.","SUCCESS")
                else: excl_status.config(text="Could not add exclusion",fg=RED); self.output_show("SECURITY CENTER","PROJECT EXCLUSION FAILED",out.strip() or "Administrator permission may be required.","ERROR")
            self._async_job(work,done,"ADDING EXCLUSION...")
        def remove_project_exclusion():
            if not is_admin(): messagebox.showwarning("Admin required","Run ZYNTRASEC as Administrator to manage a Defender exclusion."); return
            folder=filedialog.askdirectory(title="Choose Existing ZYNTRASEC Exclusion Folder to Remove")
            if not folder:return
            esc=folder.replace("'","''"); self.output_show("SECURITY CENTER","REMOVE EXCLUSION","Removing Defender exclusion...","RUNNING")
            def work(): return (*((lambda r:(r[0],r[1]))(ps(f"Remove-MpPreference -ExclusionPath '{esc}'",timeout=30))),folder)
            def done(r):
                rc,out,folder=r
                if rc==0: excl_status.config(text=f"EXCLUSION REMOVED: {folder}",fg=GREEN); self.output_show("SECURITY CENTER","PROJECT EXCLUSION REMOVED",f"Folder: {folder}","SUCCESS")
                else: excl_status.config(text="Could not remove exclusion",fg=RED); self.output_show("SECURITY CENTER","REMOVE EXCLUSION FAILED",out.strip() or "Administrator permission may be required.","ERROR")
            self._async_job(work,done,"REMOVING EXCLUSION...")
        ttk.Button(excl_action,text="CHOOSE FOLDER + ADD EXCLUSION",command=choose_project_folder).pack(side="left",padx=(0,7)); ttk.Button(excl_action,text="REMOVE EXCLUSION",command=remove_project_exclusion).pack(side="left")
        tk.Label(outer,text="● Live status only • ON = enabled • OFF = disabled • UNKNOWN = Windows did not report a reliable value",bg=BG,fg=TEXT,font=("Consolas",9)).pack(anchor="w",pady=(0,4))
        def set_card(name,state,detail):
            state_lbl,detail_lbl,dot=card_widgets[name]
            if state=="ON": state_lbl.config(text="ON",fg=GREEN); dot.config(fg=GREEN)
            elif state=="OFF": state_lbl.config(text="OFF",fg=RED); dot.config(fg=RED)
            else: state_lbl.config(text="UNKNOWN",fg=WARN); dot.config(fg=WARN)
            detail_lbl.config(text=detail)
        def refresh_table(open_security=False):
            if getattr(self,"_security_check_running",False): return
            self._security_check_running=True; refresh_btn.config(state="disabled"); auto_btn.config(state="disabled")
            for name in card_widgets: set_card(name,"UNKNOWN","Checking Windows status...")
            self.output_show("SECURITY CENTER","SECURITY STATUS","Reading Firewall, Defender RTP, UAC and Memory Integrity...","RUNNING")
            script=r"""$ErrorActionPreference='SilentlyContinue'
$fw=@(Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled)
$mp=Get-MpComputerStatus
$uac=(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System').EnableLUA
$hvciReg=(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity').Enabled
$dg=Get-CimInstance -Namespace 'root\Microsoft\Windows\DeviceGuard' -ClassName Win32_DeviceGuard
$hvciRunning=@($dg.SecurityServicesRunning) -contains 2
$hvciConfigured=($hvciReg -eq 1) -or $hvciRunning
[pscustomobject]@{ FirewallEnabledCount=@($fw | Where-Object {$_ -eq $true}).Count; FirewallProfileCount=@($fw).Count; DefenderRTP=[bool]$mp.RealTimeProtectionEnabled; UAC=[int]$uac; MemoryIntegrity=[bool]$hvciConfigured; MemoryIntegritySource=if($hvciRunning){'Device Guard: HVCI running'}elseif($hvciReg -eq 1){'Registry: HVCI enabled'}else{'HVCI not reported as enabled'} } | ConvertTo-Json -Compress"""
            def work():
                rc,out=ps(script,timeout=30)
                if rc!=0 or not out.strip(): return None,out.strip() or "Windows security query failed."
                try:return json.loads(out.strip().splitlines()[-1]),""
                except Exception as e:return None,f"Could not parse Windows security status: {e}\n{out.strip()}"
            def done(result):
                self._security_check_running=False; refresh_btn.config(state="normal"); auto_btn.config(state="normal")
                data,err=result
                if not data:
                    for name in card_widgets: set_card(name,"UNKNOWN","Status unavailable")
                    self.output_show("SECURITY CENTER","SECURITY STATUS",err,"ERROR")
                    if open_security:self.open_windows_security()
                    return
                fw_count=int(data.get("FirewallProfileCount",0) or 0); fw_on=int(data.get("FirewallEnabledCount",0) or 0)
                fw_state="ON" if fw_count>0 and fw_on==fw_count else ("OFF" if fw_count>0 else "UNKNOWN")
                set_card("Firewall",fw_state,f"{fw_on}/{fw_count} firewall profiles enabled" if fw_count else "Firewall profiles unavailable")
                d_state="ON" if bool(data.get("DefenderRTP")) else "OFF"; set_card("Defender RTP",d_state,"Real-time protection enabled" if d_state=="ON" else "Real-time protection disabled")
                uac_state="ON" if int(data.get("UAC",0) or 0)==1 else "OFF"; set_card("UAC",uac_state,"User Account Control enabled" if uac_state=="ON" else "User Account Control disabled")
                mi_state="ON" if bool(data.get("MemoryIntegrity")) else "OFF"; set_card("Memory Integrity",mi_state,str(data.get("MemoryIntegritySource") or "HVCI status reported"))
                summary=f"Firewall: {fw_state} | Defender RTP: {d_state} | UAC: {uac_state} | Memory Integrity: {mi_state}\nSCAN STATUS: SUCCESS | INSTALL/CHANGE ACTIONS: NONE"
                self.output_show("SECURITY CENTER","SECURITY STATUS",summary,"SUCCESS")
                if open_security:self.open_windows_security()
            self._async_job(work,done,"CHECKING SECURITY...")
        refresh_btn.config(command=refresh_table); auto_btn.config(command=lambda:refresh_table(True)); refresh_table()

    def clean_temp(self):
        self.output_show("PERFORMANCE","CLEAN USER TEMP","Cleaning user TEMP files...","RUNNING")
        temp=os.environ.get("TEMP") or os.environ.get("TMP")
        def work():
            if not temp or not os.path.isdir(temp): return "TEMP directory unavailable."
            removed=0; skipped=0
            for root,dirs,files in os.walk(temp, topdown=True):
                for name in files:
                    fp=os.path.join(root,name)
                    try: os.remove(fp); removed+=1
                    except OSError: skipped+=1
                for name in list(dirs):
                    dp=os.path.join(root,name)
                    try: shutil.rmtree(dp); removed+=1
                    except OSError: skipped+=1
            return f"TEMP: {temp}\nREMOVED: {removed}\nSKIPPED/IN USE: {skipped}"
        self._async_job(work,lambda text:self.output_show("PERFORMANCE","CLEAN USER TEMP",text,"SUCCESS"),"CLEANING USER TEMP...")

    def trim(self,drive):
        letter=str(drive).rstrip(":\\").upper()
        if not letter: return
        self.output_show("PERFORMANCE",f"TRIM {letter}:",f"Checking {letter}: for SSD/HDD before TRIM ...","RUNNING")
        def work():
            check_cmd = (
                f"$p=Get-Partition -DriveLetter '{letter}' -ErrorAction Stop | Select-Object -First 1; "
                f"$d=$p | Get-Disk -ErrorAction Stop; "
                f"Write-Output ('MEDIA_TYPE=' + [string]$d.MediaType); "
                f"Write-Output ('BUS_TYPE=' + [string]$d.BusType)"
            )
            rc,out=ps(check_cmd,30)
            if rc!=0:
                return rc, "DRIVE: %s:\nMEDIA TYPE: UNKNOWN\nRESULT: Could not identify the physical disk." % letter
            media="UNKNOWN"; bus="UNKNOWN"
            for line in out.splitlines():
                if line.upper().startswith("MEDIA_TYPE="): media=line.split("=",1)[1].strip() or "UNKNOWN"
                elif line.upper().startswith("BUS_TYPE="): bus=line.split("=",1)[1].strip() or "UNKNOWN"
            report=[f"DRIVE: {letter}:",f"MEDIA TYPE: {media}",f"BUS TYPE: {bus}"]
            if media.upper() == "SSD":
                rc2,out2=ps(f"Optimize-Volume -DriveLetter '{letter}' -ReTrim -ErrorAction Stop | Out-String",120)
                report.append("TRIM: EXECUTED")
                report.append(out2.strip() or "TRIM command completed.")
                return rc2,"\n".join(report)
            if media.upper() in ("HDD","UNSPECIFIED","UNKNOWN"):
                report.append("TRIM: NOT APPLICABLE")
                report.append("RESULT: No TRIM command was run because this drive is not confirmed as an SSD.")
                return 0,"\n".join(report)
            report.append("TRIM: NOT RUN")
            report.append("RESULT: Media type was not recognized as SSD.")
            return 0,"\n".join(report)
        def done(res):
            rc,out=res
            status="SUCCESS" if rc==0 and "TRIM: EXECUTED" in out else ("SUCCESS" if rc==0 else "REVIEW")
            self.output_show("PERFORMANCE",f"TRIM {letter}:",out,status)
        self._async_job(work,done,f"CHECKING {letter}: DRIVE TYPE...")

    def sfc(self):
        self.output_show("PERFORMANCE","SFC","Running SFC /scannow...","RUNNING")
        def work(): return run("sfc /scannow",300)
        def done(res):
            rc,out=res; self.output_show("PERFORMANCE","SFC",out.strip() or "No SFC result returned.","SUCCESS" if rc==0 else "REVIEW")
        self._async_job(work,done,"RUNNING SFC...")

    def dism(self):
        self.output_show("PERFORMANCE","DISM CHECK","Running DISM CheckHealth...","RUNNING")
        def work(): return run("DISM /Online /Cleanup-Image /CheckHealth",120)
        def done(res):
            rc,out=res; self.output_show("PERFORMANCE","DISM CHECK",out.strip() or "No DISM result returned.","SUCCESS" if rc==0 else "REVIEW")
        self._async_job(work,done,"RUNNING DISM CHECK...")

    def explorer(self):
        self.output_show("PERFORMANCE","RESTART EXPLORER","Restarting Windows Explorer...","RUNNING")
        def work():
            rc1,out1=run("taskkill /f /im explorer.exe",30)
            time.sleep(1)
            rc2,out2=run("start explorer.exe",30)
            return rc2, (out2.strip() or out1.strip() or "Explorer restart requested.")
        def done(res):
            rc,out=res; self.output_show("PERFORMANCE","RESTART EXPLORER",out,"SUCCESS" if rc==0 else "REVIEW")
        self._async_job(work,done,"RESTARTING EXPLORER...")

    def performance(self):
        self.header("⚡ PERFORMANCE","Live system monitoring + safe maintenance only.")
        # Live monitor panel
        mon=tk.Frame(self.page,bg=PANEL,highlightbackground="#146b38",highlightthickness=1)
        mon.pack(fill="x",padx=8,pady=(2,8))
        tk.Label(mon,text="LIVE SYSTEM MONITOR",bg=PANEL,fg=GREEN,font=("Consolas",12,"bold")).pack(anchor="w",padx=10,pady=(8,2))
        self._perf_vars={k:tk.StringVar(value="--") for k in ("CPU","RAM","DISK","GPU")}
        grid=tk.Frame(mon,bg=PANEL); grid.pack(fill="x",padx=8,pady=6)
        for col,k in enumerate(("CPU","RAM","DISK","GPU")):
            box=tk.Frame(grid,bg="#050a07",highlightbackground="#125c31",highlightthickness=1)
            box.grid(row=0,column=col,sticky="ew",padx=4); grid.columnconfigure(col,weight=1)
            tk.Label(box,text=k,bg="#050a07",fg=MUTED,font=("Consolas",9,"bold")).pack(anchor="w",padx=8,pady=(6,0))
            tk.Label(box,textvariable=self._perf_vars[k],bg="#050a07",fg=TEXT,font=("Consolas",12,"bold")).pack(anchor="w",padx=8,pady=(2,7))
        bar=tk.Frame(self.page,bg=BG); bar.pack(fill="x",padx=8,pady=2)
        ttk.Button(bar,text="🔄 REFRESH PERFORMANCE",command=self.refresh_performance).pack(side="left",padx=(0,5))
        ttk.Button(bar,text="📋 PERFORMANCE REPORT",command=self.performance_report).pack(side="left",padx=5)
        for txt,fn in [("CLEAN USER TEMP",self.clean_temp),("TRIM C:",lambda:self.trim("C:")),("TRIM D:",lambda:self.trim("D:")),
                       ("SFC",self.sfc),("DISM CHECK",self.dism),("HIGH PERFORMANCE",lambda:self.apply_power("High performance")),
                       ("RESTART EXPLORER",self.explorer)]:
            ttk.Button(bar,text=txt,command=fn).pack(side="left",padx=4)
        self._perf_monitor_running=True
        self.refresh_performance()

    def _get_perf_stats(self):
        cpu="UNKNOWN"; ram="UNKNOWN"; gpu="UNKNOWN"
        try:
            rc,out=ps("$c=(Get-Counter '\\Processor(_Total)\\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples.CookedValue; if($c -ne $null){[math]::Round($c,1)}",15)
            if rc==0 and out.strip(): cpu=f"{float(out.strip().splitlines()[-1]):.1f}%"
        except Exception: pass
        try:
            class M(ctypes.Structure):
                _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
            m=M(); m.dwLength=ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)); ram=f"{m.dwMemoryLoad}% ({human(m.ullTotalPhys-m.ullAvailPhys)} / {human(m.ullTotalPhys)})"
        except Exception: pass
        try:
            du=shutil.disk_usage(os.environ.get('SystemDrive','C:')+os.sep); used=du.total-du.free; disk=f"{used/du.total*100:.1f}% ({human(used)} / {human(du.total)})"
        except Exception: disk="UNKNOWN"
        try:
            rc,out=ps("(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Where-Object {$_.Name} | Select-Object -First 1 -ExpandProperty Name)",15)
            if rc==0 and out.strip(): gpu=out.strip().splitlines()[-1][:60]
        except Exception: pass
        return cpu,ram,disk,gpu

    def refresh_performance(self):
        if not hasattr(self,'_perf_vars'): return
        def work(): return self._get_perf_stats()
        def done(r):
            if not hasattr(self,'_perf_vars'): return
            try: cpu,ram,disk,gpu=r; self._perf_vars["CPU"].set(cpu); self._perf_vars["RAM"].set(ram); self._perf_vars["DISK"].set(disk); self._perf_vars["GPU"].set(gpu)
            except Exception: pass
            if getattr(self,'_perf_monitor_running',False): self._perf_after=self.after(2500,self.refresh_performance)
        self._async_job(work,done,"REFRESHING PERFORMANCE...")

    def performance_report(self):
        cpu,ram,disk,gpu=self._get_perf_stats()
        text=f"CPU USAGE       : {cpu}\nRAM USAGE       : {ram}\nSYSTEM DRIVE    : {disk}\nGPU             : {gpu}\n\nPOWER PLAN      : checked separately by Windows\nSFC / DISM      : manual operations only\nSTATUS          : PERFORMANCE REPORT READY"
        self.output_show("PERFORMANCE","PERFORMANCE REPORT",text,"SUCCESS")

    def startup(self):
        self.header("🚀 STARTUP","Read-only startup inventory.")
        toolbar=tk.Frame(self.page,bg=BG); toolbar.pack(fill="x",padx=8,pady=(2,4))
        ttk.Button(toolbar,text="🔄 REFRESH STARTUP",command=self._startup_refresh).pack(side="left",padx=(0,5))
        ttk.Button(toolbar,text="⚙ OPEN STARTUP SETTINGS",command=lambda:run("start ms-settings:startupapps")).pack(side="left",padx=5)

        self._startup_items={}
        self._startup_tree=ttk.Treeview(self.page,columns=("Name","Command","Location","User","Status"),show="headings",selectmode="browse")
        for col,title,w in (("Name","NAME",250),("Command","COMMAND",620),("Location","LOCATION",280),("User","USER",150),("Status","STATUS",120)):
            self._startup_tree.heading(col,text=title)
            self._startup_tree.column(col,width=w,anchor="w")
        self._startup_tree.pack(fill="both",expand=True,padx=8,pady=8)
        tk.Label(self.page,text="Disable creates a reversible backup in ProgramData\\ZYNTRASEC\\Backup. Remove requires confirmation and is intended for user-manageable startup entries.",bg=BG,fg=MUTED,font=("Consolas",9)).pack(anchor="w",padx=8,pady=(0,5))
        self._startup_refresh()

    def _startup_refresh(self):
        if not hasattr(self,"_startup_tree") or not self._startup_tree.winfo_exists(): return
        self.output_show("STARTUP","REFRESH","Reading Windows startup entries...","RUNNING")
        # Win32_StartupCommand lists configured startup commands, while Windows
        # Task Manager stores the actual enabled/disabled state separately in
        # StartupApproved. Read both so ZYNTRASEC matches Task Manager.
        script=r'''
$items=@(Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue |
  Select-Object Name,Command,Location,User |
  Sort-Object Name,Location)
$approved=@()
$sids=@()
try{$sids += [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value}catch{}
foreach($u in Get-CimInstance Win32_UserProfile -ErrorAction SilentlyContinue){
  if($u.SID -and $u.Loaded){$sids += [string]$u.SID}
}
$sids=@($sids | Where-Object {$_} | Select-Object -Unique)
$subPaths=@(
 'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run',
 'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32',
 'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder')
foreach($sid in $sids){
  foreach($sub in $subPaths){
    $root="Registry::HKEY_USERS\$sid\$sub"
    try{
      if(Test-Path -LiteralPath $root){
        $p=Get-ItemProperty -LiteralPath $root -ErrorAction SilentlyContinue
        foreach($prop in $p.PSObject.Properties){
          if($prop.Name -notlike 'PS*' -and $null -ne $prop.Value){
            $b=@($prop.Value); $state='UNKNOWN'
            if($b.Count -gt 0){
              if([byte]$b[0] -eq 3){$state='DISABLED'}
              elseif([byte]$b[0] -eq 2){$state='ENABLED'}
            }
            $approved += [pscustomobject]@{Name=[string]$prop.Name;State=$state;SID=$sid;Root=$root}
          }
        }
      }
    }catch{}
  }
}
[pscustomobject]@{Items=$items;Approved=$approved} | ConvertTo-Json -Compress -Depth 8
'''
        def done(res):
            rc,out=res
            if rc!=0:
                self.output_show("STARTUP","REFRESH",out.strip() or "Startup inventory failed.","ERROR"); return
            try:
                payload=json.loads(out.strip()) if out.strip() else {}
                data=payload.get("Items",[]) if isinstance(payload,dict) else payload
                approved=payload.get("Approved",[]) if isinstance(payload,dict) else []
                if isinstance(data,dict): data=[data]
                if isinstance(approved,dict): approved=[approved]
                state_entries=[]
                for a in approved:
                    if not isinstance(a,dict): continue
                    an=str(a.get("Name") or "").strip().lower()
                    st=str(a.get("State") or "UNKNOWN").upper()
                    if an: state_entries.append((an,st))

                def _startup_tokens(name,cmd):
                    import os,re
                    vals=[]
                    for raw in (name,cmd):
                        x=str(raw or "").strip().lower()
                        if not x: continue
                        vals.append(x)
                        for m in re.findall(r'[a-z0-9_.-]+\.exe', x): vals.append(m)
                        base=os.path.basename(x.strip('\"'))
                        if base: vals.append(base)
                    return set(vals)

                def _startup_status(name,cmd):
                    tokens=_startup_tokens(name,cmd)
                    matched=[]
                    for an,st in state_entries:
                        if tokens & _startup_tokens(an,""): matched.append(st)
                    if any(st=="DISABLED" for st in matched): return "DISABLED"
                    if any(st=="ENABLED" for st in matched): return "ENABLED"
                    return "UNKNOWN"
                for iid in self._startup_tree.get_children(): self._startup_tree.delete(iid)
                self._startup_items={}
                visible=[]
                for item in data:
                    name=str(item.get("Name") or "").strip()
                    cmd=str(item.get("Command") or "").strip()
                    loc=str(item.get("Location") or "").strip()
                    user=str(item.get("User") or "").strip()
                    if not name and not cmd: continue
                    status=_startup_status(name,cmd)
                    if status not in ("ENABLED","DISABLED"): status="ENABLED"
                    key=(name.lower(),cmd.lower(),loc.lower())
                    visible.append((item,key,status))
                try:
                    bp=self._startup_backup_file()
                    if bp.exists():
                        saved=json.loads(bp.read_text(encoding="utf-8"))
                        if isinstance(saved,dict): saved=[saved]
                        active_keys={(str(x.get("Name") or "").strip().lower(),str(x.get("Command") or "").strip().lower(),str(x.get("Location") or "").strip().lower()) for x in data if isinstance(x,dict)}
                        for rec in reversed(saved):
                            if not isinstance(rec,dict) or str(rec.get("Action") or "").upper()!="DISABLE": continue
                            name=str(rec.get("Name") or "").strip(); cmd=str(rec.get("Command") or "").strip(); loc=str(rec.get("Location") or rec.get("Path") or "").strip()
                            key=(name.lower(),cmd.lower(),loc.lower())
                            if not name and not cmd: continue
                            if key in active_keys: continue
                            visible.append((rec,key,"DISABLED")); active_keys.add(key)
                except Exception:
                    pass
                for idx,(item,key,status) in enumerate(visible):
                    name=str(item.get("Name") or "").strip()
                    cmd=str(item.get("Command") or "").strip()
                    loc=str(item.get("Location") or item.get("Path") or "").strip()
                    user=str(item.get("User") or "").strip()
                    iid=str(idx)
                    self._startup_items[iid]={"Name":name,"Command":cmd,"Location":loc,"User":user,"Status":status,"Record":item}
                    self._startup_tree.insert("","end",iid=iid,values=(name,cmd,loc,user,status))
                self.output_show("STARTUP","REFRESH",f"FOUND: {len(data)} STARTUP ENTRY(S)\nDISABLED: {sum(1 for x in visible if x[2]=='DISABLED')}\nSTATUS: INVENTORY READY","SUCCESS")
            except Exception as e:
                self.output_show("STARTUP","REFRESH",f"Could not parse startup inventory: {e}\n\nRaw output:\n{out[:3000]}","REVIEW")
        self._async_job(lambda:ps(script,30),done,"LOADING STARTUP...")

    def _startup_selected(self):
        if not hasattr(self,"_startup_tree"): return None
        sel=self._startup_tree.selection()
        if not sel:
            messagebox.showwarning("Startup","Select a startup entry first."); return None
        return self._startup_items.get(sel[0])

    def _startup_extract_path(self,command):
        import re
        cmd=os.path.expandvars(str(command or "").strip())
        if not cmd: return None
        m=re.match(r'^\s*"([^"]+)"',cmd)
        if m: candidate=m.group(1)
        else:
            m=re.match(r'^\s*([^\s]+)',cmd)
            candidate=m.group(1) if m else cmd
        candidate=candidate.strip('"')
        if os.path.exists(candidate): return os.path.abspath(candidate)
        return None

    def _startup_open_location(self):
        item=self._startup_selected()
        if not item:return
        path=self._startup_extract_path(item.get("Command"))
        if path:
            try:
                if os.path.isfile(path): run(f'explorer.exe /select,"{path}"',20)
                else: os.startfile(path)
                self.output_show("STARTUP","OPEN LOCATION",f"NAME: {item.get('Name')}\nPATH: {path}\nSTATUS: LOCATION OPENED","SUCCESS")
            except Exception as e: self.output_show("STARTUP","OPEN LOCATION",str(e),"ERROR")
            return
        loc=str(item.get("Location") or "")
        if loc.lower().startswith("hkey_") or "\\run" in loc.lower():
            try:
                run("regedit.exe",20)
                self.output_show("STARTUP","OPEN LOCATION",f"NAME: {item.get('Name')}\nREGISTRY LOCATION: {loc}\nSTATUS: REGISTRY EDITOR OPENED","SUCCESS")
            except Exception as e:self.output_show("STARTUP","OPEN LOCATION",str(e),"ERROR")
        else:
            self.output_show("STARTUP","OPEN LOCATION",f"NAME: {item.get('Name')}\nCOMMAND: {item.get('Command')}\nLOCATION: {loc}\nSTATUS: FILE LOCATION COULD NOT BE RESOLVED","REVIEW")

    def _startup_backup_file(self):
        p=self.backup_root/"startup_disabled.json"
        self.backup_root.mkdir(parents=True,exist_ok=True)
        return p

    def _startup_change(self,remove=False):
        item=self._startup_selected()
        if not item:return
        action="REMOVE" if remove else "DISABLE"
        name=item.get("Name") or "Unnamed startup entry"
        command=item.get("Command") or ""
        location=item.get("Location") or ""
        if remove:
            if not messagebox.askyesno("Confirm Startup Removal",f"Remove startup entry?\n\n{name}\n\nThis may affect automatic app startup."): return
        else:
            if not messagebox.askyesno("Confirm Startup Disable",f"Disable startup entry?\n\n{name}\n\nA backup will be stored so the entry can be restored manually."): return
        if not is_admin() and ("HKEY_LOCAL_MACHINE" in location.upper() or "ALL USERS" in location.upper()):
            messagebox.showwarning("Administrator required","This startup entry is machine-wide. Run ZYNTRASEC as Administrator."); return
        if action=="DISABLE" and str(item.get("Status") or "").upper()=="DISABLED":
            messagebox.showinfo("Startup", "This startup entry is already DISABLED in Windows.")
            return
        if action=="REMOVE" and str(item.get("Status") or "").upper()=="DISABLED":
            messagebox.showinfo("Startup", "Select an ENABLED startup entry to remove it.")
            return
        self.output_show("STARTUP",action,f"TARGET: {name}\nLOCATION: {location}\nACTION: {action}...","RUNNING")
        # PowerShell single-quoted literals are used here. JSON-style \"...\"
        # escaping is not valid PowerShell string escaping and breaks commands
        # containing paths such as C:\Program Files\... .
        def ps_quote(value):
            return "'" + str(value or "").replace("'", "''") + "'"
        safe_name=ps_quote(name); safe_cmd=ps_quote(command); safe_loc=ps_quote(location)
        backup_path=str(self._startup_backup_file()).replace("'","''")
        script=fr'''
$name={safe_name}; $cmd={safe_cmd}; $loc={safe_loc}; $backup='{backup_path}'
$record=[ordered]@{{Name=$name;Command=$cmd;Location=$loc;Time=(Get-Date).ToString('o');Action='{action}'}}
$done=$false; $detail=''
$existing=@()
if(Test-Path $backup){{ try{{ $existing=@(Get-Content -Raw -LiteralPath $backup | ConvertFrom-Json) }}catch{{ $existing=@() }} }}
if($existing -isnot [System.Array]){{ $existing=@($existing) }}
$regRoots=@('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce')
foreach($root in $regRoots){{
  try{{ if(Test-Path $root){{ $p=Get-ItemProperty -LiteralPath $root -ErrorAction SilentlyContinue; $prop=$p.PSObject.Properties | Where-Object {{ $_.Name -eq $name }} | Select-Object -First 1; if($prop){{
      $record.Path=$root; $record.Value=[string]$prop.Value; $existing += [pscustomobject]$record
      Remove-ItemProperty -LiteralPath $root -Name $name -ErrorAction Stop; $done=$true; $detail="{action.lower()} registry value: $root\\$name"; break
  }}}}}}catch{{ $detail=$_.Exception.Message }}
}}
if(-not $done){{
  $path=$null
  if($cmd -match '^\s*"([^"]+)"'){{ $path=$Matches[1] }} elseif($cmd -match '^\s*([^\s]+)'){{ $path=$Matches[1] }}
  if($path){{ $path=[Environment]::ExpandEnvironmentVariables($path) }}
  if($path -and (Test-Path -LiteralPath $path)){{
    $record.Path=$path; $record.Value=''
    if('{action}' -eq 'REMOVE'){{ Remove-Item -LiteralPath $path -Force -ErrorAction Stop; $done=$true; $detail="Removed startup file: $path" }}
    else{{ $new="$path.disabled"; Rename-Item -LiteralPath $path -NewName ([IO.Path]::GetFileName($new)) -Force -ErrorAction Stop; $record.DisabledPath=$new; $done=$true; $detail="Disabled startup file: $path -> $new" }}
    $existing += [pscustomobject]$record
  }}
}}
if($done){{ $existing | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $backup -Encoding UTF8; Write-Output "OK|$detail" }} else {{ Write-Output "FAIL|No matching startup registry value or startup file was found for the selected entry." }}
'''
        def done(res):
            rc,out=res; text=out.strip() or "No result returned."
            ok=rc==0 and text.startswith("OK|")
            self.output_show("STARTUP",action,text.replace("OK|","",1).replace("FAIL|","",1),"SUCCESS" if ok else "REVIEW")
            if ok:self._startup_refresh()
        self._async_job(lambda:ps(script,30),done,f"{action} STARTUP...")

    def _startup_enable(self):
        item=self._startup_selected()
        if not item:return
        if str(item.get("Status") or "").upper()!="DISABLED":
            messagebox.showinfo("Startup", "Select a DISABLED startup entry first.")
            return
        rec=item.get("Record") or item
        name=str(rec.get("Name") or "Unnamed startup entry")
        command=str(rec.get("Command") or "")
        location=str(rec.get("Location") or rec.get("Path") or "")
        if not messagebox.askyesno("Confirm Startup Enable",f"Enable startup entry?\n\n{name}\n\nThe original backup will be restored."): return
        if not is_admin() and ("HKEY_LOCAL_MACHINE" in location.upper() or location.upper().startswith("HKLM:")):
            messagebox.showwarning("Administrator required","This startup entry is machine-wide. Run ZYNTRASEC as Administrator.")
            return
        self.output_show("STARTUP","ENABLE",f"TARGET: {name}\nLOCATION: {location}\nACTION: ENABLE...","RUNNING")
        def ps_quote(value):
            return "'" + str(value or "").replace("'", "''") + "'"
        safe_name=ps_quote(name); safe_cmd=ps_quote(command); safe_loc=ps_quote(location)
        backup_path=str(self._startup_backup_file()).replace("'","''")
        script=fr'''
$name={safe_name}; $cmd={safe_cmd}; $loc={safe_loc}; $backup='{backup_path}'
$done=$false; $detail=''
$existing=@()
if(Test-Path -LiteralPath $backup){{ try{{ $existing=@(Get-Content -Raw -LiteralPath $backup | ConvertFrom-Json) }}catch{{ $existing=@() }} }}
if($existing -isnot [System.Array]){{ $existing=@($existing) }}
$target=$null
foreach($r in $existing){{ if([string]$r.Name -eq $name -and [string]$r.Action -eq 'DISABLE' -and (([string]$r.Location -eq $loc) -or [string]$r.Path -eq $loc)){{ $target=$r; break }} }}
if(-not $target){{ foreach($r in $existing){{ if([string]$r.Name -eq $name -and [string]$r.Action -eq 'DISABLE'){{ $target=$r; break }} }} }}
try{{
  if($target -and [string]$target.Path -match '^(HKCU:|HKLM:|HKEY_)'){{
    $regPath=[string]$target.Path
    if($regPath -match '^HKEY_CURRENT_USER'){{$regPath=$regPath -replace '^HKEY_CURRENT_USER','HKCU:'}}
    if($regPath -match '^HKEY_LOCAL_MACHINE'){{$regPath=$regPath -replace '^HKEY_LOCAL_MACHINE','HKLM:'}}
    if(-not (Test-Path -LiteralPath $regPath)){{ New-Item -Path $regPath -Force | Out-Null }}
    $value=[string]$target.Value
    if([string]::IsNullOrWhiteSpace($value)){{ $value=$cmd }}
    New-ItemProperty -LiteralPath $regPath -Name $name -Value $value -PropertyType String -Force -ErrorAction Stop | Out-Null
    $done=$true; $detail="Enabled registry value: $regPath\$name"
  }}
  elseif($target -and [string]$target.DisabledPath -and (Test-Path -LiteralPath ([string]$target.DisabledPath))){{
    Rename-Item -LiteralPath ([string]$target.DisabledPath) -NewName ([IO.Path]::GetFileName([string]$target.Path)) -Force -ErrorAction Stop
    $done=$true; $detail="Enabled startup file: $([string]$target.Path)"
  }}
  elseif($target -and [string]$target.Path -and (Test-Path -LiteralPath ([string]$target.Path))){{ $done=$true; $detail="Startup file already enabled: $([string]$target.Path)" }}
}}catch{{ $detail=$_.Exception.Message }}
if($done){{
  $keep=@()
  foreach($r in $existing){{ if(-not ([string]$r.Name -eq $name -and [string]$r.Action -eq 'DISABLE' -and (([string]$r.Path -eq [string]$target.Path) -or ([string]$r.Location -eq [string]$target.Location)))){{ $keep += $r }} }}
  if($keep.Count -eq 0){{ Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue }} else {{ $keep | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $backup -Encoding UTF8 }}
  Write-Output "OK|$detail"
}} else {{ Write-Output "FAIL|$detail" }}
'''
        def done(res):
            rc,out=res; text=out.strip() or "No result returned."
            ok=rc==0 and text.startswith("OK|")
            self.output_show("STARTUP","ENABLE",text.replace("OK|","",1).replace("FAIL|","",1),"SUCCESS" if ok else "REVIEW")
            if ok:self._startup_refresh()
        self._async_job(lambda:ps(script,30),done,"ENABLING STARTUP...")

    def _startup_disable(self): self._startup_change(False)
    def _startup_remove(self): self._startup_change(True)

    def _health_refresh(self):
        self.output_show("WINDOWS HEALTH","REFRESH STATUS","Collecting read-only health information...","RUNNING")
        def work():
            parts=[]
            rc,out=run("DISM /Online /Cleanup-Image /CheckHealth",90)
            parts.append("SYSTEM IMAGE\n" + (out.strip() or "No DISM result returned."))
            rc,out=run("sfc /verifyonly",180)
            parts.append("SYSTEM FILES (VERIFY ONLY)\n" + (out.strip() or "No SFC result returned."))
            rc,out=ps("Get-PhysicalDisk -ErrorAction SilentlyContinue | Select-Object FriendlyName,MediaType,HealthStatus,OperationalStatus,Size | Format-Table -AutoSize | Out-String",30)
            parts.append("PHYSICAL DISKS\n" + (out.strip() or "Physical disk health unavailable."))
            rc,out=ps("$svc=Get-Service wuauserv -ErrorAction SilentlyContinue; if($svc){'Windows Update Service: '+$svc.Status}else{'Windows Update Service: UNKNOWN'}; Get-HotFix -ErrorAction SilentlyContinue | Sort-Object InstalledOn -Descending | Select-Object -First 3 HotFixID,InstalledOn | Format-Table -AutoSize | Out-String",30)
            parts.append("WINDOWS UPDATE / RECENT HOTFIXES\n" + (out.strip() or "No update information returned."))
            return "\n\n".join(parts)
        self._async_job(work,lambda text:self.output_show("WINDOWS HEALTH","REFRESH STATUS",text,"SUCCESS"),"CHECKING WINDOWS HEALTH...")

    def _health_report(self):
        self.output_show("WINDOWS HEALTH","HEALTH REPORT","Generating read-only health report...","RUNNING")
        def work():
            parts=[]
            rc,out=ps("Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,LastBootUpTime | Format-List | Out-String",20)
            parts.append("OS\n"+out.strip())
            rc,out=ps("Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}},@{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}} | Format-Table -AutoSize | Out-String",20)
            parts.append("STORAGE\n"+out.strip())
            rc,out=ps("Get-Service wuauserv,WinDefend,MpsSvc -ErrorAction SilentlyContinue | Select-Object Name,Status,StartType | Format-Table -AutoSize | Out-String",20)
            parts.append("CORE SERVICES\n"+out.strip())
            return "\n\n".join(parts)
        self._async_job(work,lambda text:self.output_show("WINDOWS HEALTH","HEALTH REPORT",text,"SUCCESS"),"BUILDING HEALTH REPORT...")

    def _disk_health(self):
        self.output_show("WINDOWS HEALTH","DISK HEALTH","Checking physical disk health...","RUNNING")
        def work():
            rc,out=ps("Get-PhysicalDisk -ErrorAction SilentlyContinue | Select-Object FriendlyName,MediaType,HealthStatus,OperationalStatus,@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}} | Format-Table -AutoSize | Out-String",30)
            return out.strip() or "Physical disk health information is unavailable on this system."
        self._async_job(work,lambda text:self.output_show("WINDOWS HEALTH","DISK HEALTH",text,"SUCCESS"),"CHECKING DISK HEALTH...")

    def _windows_update_status(self):
        self.output_show("WINDOWS HEALTH","WINDOWS UPDATE STATUS","Checking Windows Update service and recent updates...","RUNNING")
        def work():
            rc,out=ps("$svc=Get-Service wuauserv -ErrorAction SilentlyContinue; $a=if($svc){$svc.Status}else{'UNKNOWN'}; 'Windows Update Service: '+$a; ''; Get-HotFix -ErrorAction SilentlyContinue | Sort-Object InstalledOn -Descending | Select-Object -First 5 HotFixID,InstalledOn,Description | Format-Table -AutoSize | Out-String",30)
            return out.strip() or "No Windows Update information returned."
        self._async_job(work,lambda text:self.output_show("WINDOWS HEALTH","WINDOWS UPDATE STATUS",text,"SUCCESS"),"CHECKING WINDOWS UPDATE...")

    def windows_health(self):
        self.header("🩺 WINDOWS HEALTH","Read-only health checks plus optional administrator repair commands.")
        toolbar=tk.Frame(self.page,bg=BG); toolbar.pack(fill="x",padx=8,pady=(2,4))
        for txt,fn in [("🔄 REFRESH HEALTH STATUS",self._health_refresh),("📊 HEALTH REPORT",self._health_report),("💾 DISK HEALTH",self._disk_health),("🪟 WINDOWS UPDATE STATUS",self._windows_update_status)]:
            ttk.Button(toolbar,text=txt,command=fn).pack(side="left",padx=(0,5))
        toolbar2=tk.Frame(self.page,bg=BG); toolbar2.pack(fill="x",padx=8,pady=(0,4))
        ttk.Button(toolbar2,text="RUN SFC",command=self.sfc).pack(side="left",padx=(0,5))
        ttk.Button(toolbar2,text="RUN DISM CHECK",command=self.dism).pack(side="left",padx=5)
        ttk.Button(toolbar2,text="OPEN WINDOWS RECOVERY",command=lambda:run("start ms-settings:recovery")).pack(side="left",padx=5)
        tk.Label(self.page,text="SFC/DISM repair actions run only when explicitly started. Health refresh/report checks are read-only.",bg=BG,fg=MUTED,font=("Consolas",9)).pack(anchor="w",padx=8,pady=(0,5))
        self.output_show("WINDOWS HEALTH","READY",
                         "Read-only health checks are available.\n"
                         "No repair command is started automatically from this page.")

    def power_setup(self):
        self.header("⚡ POWER","Review power mode, active plan and battery status.")
        ttk.Button(self.page,text="CHECK POWER STATUS",command=self._power_status).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="HIGH PERFORMANCE",command=lambda:self.apply_power("High performance")).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="OPEN POWER SETTINGS",command=lambda:run("start ms-settings:powersleep")).pack(anchor="w",padx=8,pady=4)
        self.output_show("POWER","READY","Power settings are reviewable here; changing the plan requires explicit action.")

    def _power_status(self):
        self.output_show("POWER","STATUS","Reading power status...","RUNNING")
        def work():
            parts=[]
            rc,o=run("powercfg /getactivescheme",20)
            parts.append("ACTIVE POWER SCHEME\n"+o.strip())
            rc,o=ps("Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object Name,BatteryStatus,EstimatedChargeRemaining,EstimatedRunTime | Format-List | Out-String",20)
            parts.append("BATTERY\n"+(o.strip() if o.strip() else "No battery information returned."))
            return "\n\n".join(parts)
        self._async_job(work,lambda text:self.output_show("POWER","STATUS",text,"SUCCESS"),"CHECKING POWER...")

    def privacy_setup(self):
        self.header("🔒 PRIVACY","Review common Windows privacy permissions without disabling them automatically.")
        ttk.Button(self.page,text="CHECK PRIVACY STATUS",command=self._privacy_status).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="OPEN PRIVACY SETTINGS",command=lambda:run("start ms-settings:privacy")).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="CAMERA SETTINGS",command=lambda:run("start ms-settings:privacy-webcam")).pack(anchor="w",padx=8,pady=4)
        ttk.Button(self.page,text="MICROPHONE SETTINGS",command=lambda:run("start ms-settings:privacy-microphone")).pack(anchor="w",padx=8,pady=4)
        self.output_show("PRIVACY","READY","Privacy permissions are review-only here. No camera, microphone, location or diagnostic permission is disabled automatically.")

    def _privacy_status(self):
        self.output_show("PRIVACY","STATUS","Reading privacy-related settings...","RUNNING")
        def work():
            script = "$paths=@('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\camera','HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\microphone','HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location'); foreach($p in $paths){$n=Split-Path $p -Leaf;$v=Get-ItemProperty $p -ErrorAction SilentlyContinue; [pscustomobject]@{Area=$n;Value=if($v){$v.Value}else{'NOT SET'}}} | Format-Table -AutoSize | Out-String"
            rc,o=ps(script,30)
            return o.strip() if o.strip() else "No privacy registry status returned. Use OPEN PRIVACY SETTINGS for the authoritative Windows UI."
        self._async_job(work,lambda text:self.output_show("PRIVACY","STATUS",text,"SUCCESS"),"CHECKING PRIVACY...")

    def final_system_check(self):
        self.output_show("FINAL SYSTEM CHECK","START","Running quick final verification...","RUNNING")
        def work():
            lines=[]
            checks=[
                ("WINDOWS", "(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | Format-List | Out-String)"),
                ("IDENTITY", "whoami"),
                ("FIREWALL", "(Get-NetFirewallProfile | Where-Object Enabled -eq $false).Count"),
                ("DEFENDER RTP", "(Get-MpComputerStatus -ErrorAction SilentlyContinue).RealTimeProtectionEnabled"),
                ("UAC", "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System').EnableLUA"),
                ("ACTIVE POWER", "powercfg /getactivescheme"),
            ]
            for label,cmd in checks:
                if cmd in ("whoami","powercfg /getactivescheme"):
                    rc,o=run(cmd,20)
                else:
                    rc,o=ps(cmd,20)
                lines.append(f"[{label}]\n{o.strip() if o.strip() else 'NO OUTPUT'}")
            for d in ("C:\\","D:\\"):
                try:
                    u=shutil.disk_usage(d)
                    lines.append(f"[{d} SPACE]\nFREE: {human(u.free)}\nTOTAL: {human(u.total)}")
                except Exception as e:
                    lines.append(f"[{d} SPACE]\nCHECK FAILED: {e}")
            return "\n\n".join(lines)
        self._async_job(work,lambda text:self.output_show("FINAL SYSTEM CHECK","COMPLETE",text,"SUCCESS"),"FINAL CHECK...")

    def storage(self):
        self.header("💾 STORAGE CENTER","Drive capacity, profile analysis, large-file discovery and safe cleanup preview.")
        bar=tk.Frame(self.page,bg=BG); bar.pack(fill="x",padx=8,pady=(0,6))
        ttk.Button(bar,text="REFRESH STORAGE",command=self.storage_refresh).pack(side="left",padx=(0,6))
        ttk.Button(bar,text="SCAN USER PROFILE",command=self.profile_scan).pack(side="left",padx=6)
        ttk.Button(bar,text="ANALYZE DISKS",command=self.storage_analyze).pack(side="left",padx=6)
        ttk.Button(bar,text="LARGE FILES",command=self.storage_large_files).pack(side="left",padx=6)
        ttk.Button(bar,text="CLEANUP CENTER",command=self.storage_cleanup).pack(side="left",padx=6)
        ttk.Button(bar,text="DISK HEALTH",command=self.storage_disk_health).pack(side="left",padx=6)
        self.output_show("STORAGE", "READY", "Click REFRESH STORAGE for drive overview or use the analysis tools below.")
        self.storage_refresh()

    def storage_refresh(self):
        self.output_show("STORAGE", "REFRESH STORAGE", "Collecting fixed-drive capacity...", "RUNNING")
        def work():
            rc,out=ps("Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | Select-Object DeviceID,VolumeName,FileSystem,@{N='TotalGB';E={[math]::Round($_.Size/1GB,1)}},@{N='UsedGB';E={[math]::Round(($_.Size-$_.FreeSpace)/1GB,1)}},@{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}},@{N='UsagePct';E={if($_.Size){[math]::Round((($_.Size-$_.FreeSpace)/$_.Size)*100,1)}else{0}}} | Format-Table -AutoSize | Out-String",30)
            return out.strip() or "No fixed drives detected."
        self._async_job(work,lambda text:self.output_show("STORAGE","REFRESH STORAGE",text,"SUCCESS"),"SCANNING DRIVES...")

    def storage_analyze(self):
        self.output_show("STORAGE", "ANALYZE DISKS", "Analyzing physical disks and logical volumes...", "RUNNING")
        def work():
            parts=[]
            rc,out=ps("Get-PhysicalDisk -ErrorAction SilentlyContinue | Select-Object FriendlyName,MediaType,BusType,HealthStatus,OperationalStatus,@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}} | Format-Table -AutoSize | Out-String",30)
            parts.append("PHYSICAL DISKS\n"+(out.strip() or "Physical disk information unavailable."))
            rc,out=ps("Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | Select-Object DeviceID,VolumeName,FileSystem,@{N='TotalGB';E={[math]::Round($_.Size/1GB,1)}},@{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}} | Format-Table -AutoSize | Out-String",30)
            parts.append("LOGICAL VOLUMES\n"+(out.strip() or "No logical volumes found."))
            return "\n\n".join(parts)
        self._async_job(work,lambda text:self.output_show("STORAGE","ANALYZE DISKS",text,"SUCCESS"),"ANALYZING DISKS...")

    def storage_large_files(self):
        self.output_show("STORAGE", "LARGE FILES", "Scanning the current user profile for the largest files...", "RUNNING")
        root=Path.home()
        def work():
            found=[]
            roots=[root/"Downloads",root/"Documents",root/"Desktop",root/"Pictures",root/"Videos",root/"AppData"]
            for base in roots:
                if not base.exists(): continue
                try:
                    for x in base.rglob("*"):
                        try:
                            if x.is_file(): found.append((x.stat().st_size,str(x)))
                        except (OSError,PermissionError): pass
                except (OSError,PermissionError): pass
            found.sort(reverse=True,key=lambda z:z[0])
            if not found: return "No files found in the scanned profile folders."
            return "\n".join(f"{human(size):>12}  {path}" for size,path in found[:30])
        self._async_job(work,lambda text:self.output_show("STORAGE","LARGE FILES",text,"COMPLETE"),"SCANNING LARGE FILES...")

    def storage_cleanup(self):
        self.output_show("STORAGE", "CLEANUP CENTER", "Building a safe cleanup preview. Nothing will be deleted automatically...", "RUNNING")
        def work():
            candidates=[("User TEMP",Path(os.environ.get("TEMP",str(Path.home()/"AppData/Local/Temp")))),
                        ("Windows TEMP",Path(os.environ.get("WINDIR",r"C:\\Windows"))/"Temp"),
                        ("Downloads",Path.home()/"Downloads")]
            lines=[]
            for label,path in candidates:
                total=0; count=0
                if path.exists():
                    try:
                        for x in path.rglob("*"):
                            try:
                                if x.is_file(): total+=x.stat().st_size; count+=1
                            except (OSError,PermissionError): pass
                    except (OSError,PermissionError): pass
                lines.append(f"{label:<18} {human(total):>12}  FILES: {count}")
            lines.append("")
            lines.append("PREVIEW ONLY: no files were deleted.")
            return "\n".join(lines)
        self._async_job(work,lambda text:self.output_show("STORAGE","CLEANUP CENTER",text,"COMPLETE"),"BUILDING CLEANUP PREVIEW...")

    def storage_disk_health(self):
        self.output_show("STORAGE", "DISK HEALTH", "Checking physical disk health...", "RUNNING")
        def work():
            rc,out=ps("Get-PhysicalDisk -ErrorAction SilentlyContinue | Select-Object FriendlyName,MediaType,BusType,HealthStatus,OperationalStatus,@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}} | Format-Table -AutoSize | Out-String",30)
            return out.strip() or "Physical disk health information is unavailable on this system."
        self._async_job(work,lambda text:self.output_show("STORAGE","DISK HEALTH",text,"SUCCESS"),"CHECKING DISK HEALTH...")

    def profile_scan(self):
        self.output_show("STORAGE", "USER PROFILE SCAN", "SCANNING USER PROFILE...", "RUNNING")
        names=["AppData","Downloads",".android",".gradle",".nuget",".jdks","Documents","Pictures","Videos","Desktop","Music"]
        def work():
            result=[]
            for name in names:
                p=Path.home()/name
                if not p.exists():continue
                total=0
                for x in p.rglob("*"):
                    try:
                        if x.is_file():total+=x.stat().st_size
                    except:pass
                result.append((name,human(total)))
            return result
        def done(result):
            text="\n".join(f"{name:<20} {size}" for name,size in result)
            self.output_show("STORAGE", "USER PROFILE SCAN", text, "COMPLETE")
        self._async_job(work,done,"SCANNING PROFILE...")

    def network(self):
        self.header("🌐 NETWORK","Read-only network status and safe diagnostics.")
        bar=tk.Frame(self.page,bg=BG); bar.pack(fill="x",padx=8,pady=(0,6))
        buttons=[
            ("REFRESH NETWORK", self.network_refresh),
            ("IPCONFIG", lambda:self._network_cmd("ipconfig /all","IPCONFIG")),
            ("PING TEST", self.network_ping),
            ("DNS TEST", self.network_dns_test),
            ("TRACERT", self.network_tracert),
            ("DNS CACHE", lambda:self._network_cmd("ipconfig /displaydns","DNS CACHE")),
            ("ACTIVE CONNECTIONS", self.network_connections),
            ("NETWORK REPORT", self.network_report),
            ("OPEN NETWORK SETTINGS", lambda:run("start ms-settings:network-status")),
        ]
        for label,fn in buttons:
            ttk.Button(bar,text=label,command=fn).pack(side="left",padx=(0,6),pady=2)
        self.output_show("NETWORK", "READY", "Read-only diagnostics ready. No adapter configuration is changed automatically.")

    def _network_cmd(self,cmd,action):
        self.output_show("NETWORK", action, "Running diagnostic...", "RUNNING")
        def done(r):
            text=(r[1] or "").strip()
            self.output_show("NETWORK", action, text or "No output returned.", "SUCCESS" if r[0]==0 else "FAILED")
        self._async_job(lambda:run(cmd,45),done,action)

    def network_refresh(self):
        self.output_show("NETWORK", "REFRESH NETWORK", "Collecting adapters, IP, gateway, DNS and link status...", "RUNNING")
        script=r'''
$items=@()
Get-NetAdapter -ErrorAction SilentlyContinue | ForEach-Object {
  $a=$_
  $c=Get-NetIPConfiguration -InterfaceIndex $a.ifIndex -ErrorAction SilentlyContinue
  $items += [pscustomobject]@{
    Adapter=$a.Name
    Status=$a.Status
    LinkSpeed=$a.LinkSpeed
    MAC=$a.MacAddress
    IPv4=(($c.IPv4Address.IPAddress) -join ', ')
    Gateway=(($c.IPv4DefaultGateway.NextHop) -join ', ')
    DNS=(($c.DNSServer.ServerAddresses) -join ', ')
  }
}
$items | Format-Table -AutoSize | Out-String -Width 240
'''
        def done(r):
            text=r[1].strip() if r[1] else "No network adapters reported."
            self.output_show("NETWORK","REFRESH NETWORK",text,"SUCCESS" if r[0]==0 else "FAILED")
        self._async_job(lambda:ps(script,30),done,"REFRESH NETWORK")

    def network_ping(self):
        self._network_cmd("ping -n 4 1.1.1.1","PING TEST")

    def network_dns_test(self):
        self._network_cmd("nslookup example.com","DNS TEST")

    def network_tracert(self):
        self._network_cmd("tracert -d -h 12 1.1.1.1","TRACERT")

    def network_connections(self):
        self._network_cmd("netstat -ano","ACTIVE CONNECTIONS")

    def network_report(self):
        self.output_show("NETWORK", "NETWORK REPORT", "Building consolidated network report...", "RUNNING")
        script=r'''
Write-Output '=== NETWORK ADAPTERS ==='
Get-NetAdapter -ErrorAction SilentlyContinue | Select-Object Name,Status,LinkSpeed,MacAddress,InterfaceDescription | Format-Table -AutoSize | Out-String -Width 220
Write-Output '=== IP CONFIGURATION ==='
Get-NetIPConfiguration -ErrorAction SilentlyContinue | Select-Object InterfaceAlias,IPv4Address,IPv4DefaultGateway,DNSServer | Format-List | Out-String -Width 220
Write-Output '=== ACTIVE CONNECTIONS (SUMMARY) ==='
Get-NetTCPConnection -ErrorAction SilentlyContinue | Group-Object State | Sort-Object Name | ForEach-Object { '{0}: {1}' -f $_.Name,$_.Count }
'''
        def done(r):
            text=r[1].strip() if r[1] else "Network report unavailable."
            self.output_show("NETWORK","NETWORK REPORT",text,"SUCCESS" if r[0]==0 else "FAILED")
        self._async_job(lambda:ps(script,45),done,"NETWORK REPORT")

    def theme(self):
        self.header("🎨 THEME / TERMINAL","Optional visual customization.")
        for x,u in [("WINDOWS TERMINAL","wt"),("PERSONALIZATION","start ms-settings:personalization"),("LOCK SCREEN","start ms-settings:lockscreen"),("CURSOR","start ms-settings:easeofaccess-mousepointer")]:
            ttk.Button(self.page,text=x,command=lambda z=u:run(z)).pack(anchor="w",padx=8,pady=5)

    def backup(self):
        self.header("💾 BACKUP / ROLLBACK","Create configuration backups before major changes.")
        ttk.Button(self.page,text="CREATE CONFIG BACKUP",command=self.make_backup).pack(anchor="w",padx=8,pady=6)
        ttk.Button(self.page,text="OPEN ZYNTRASEC DATA",command=lambda:run(f'explorer "{self.data_root}"')).pack(anchor="w",padx=8,pady=6)
    def make_backup(self):
        d=self.backup_root/f"ZYNTRASEC_Backup_{datetime.now():%Y%m%d_%H%M%S}"
        def work():
            d.mkdir(parents=True,exist_ok=True)
            run(f'reg export "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies" "{d}\\HKCU_Policies.reg" /y',60)
            run(f'reg export "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows" "{d}\\HKLM_Policies.reg" /y',60)
            run(f'gpresult /h "{d}\\gpresult.html" /f',60)
            try:
                if self.policy_apps_file.exists():(d/"policy_custom_apps.json").write_text(self.policy_apps_file.read_text(encoding="utf-8"),encoding="utf-8")
            except Exception:pass
            (d/"README.txt").write_text("ZYNTRASEC backup. Review before restoring.",encoding="utf-8")
            return d
        self._async_job(work,lambda d:(self.logit(f"Backup created: {d}"),messagebox.showinfo("Backup complete",str(d))),"CREATING BACKUP...")

    def safe_baseline(self):
        if not is_admin():messagebox.showwarning("Admin required","Run as Administrator.");return
        if not messagebox.askyesno("SAFE BASELINE","Create backup, run DISM/SFC, TRIM and refresh Explorer?"):return
        self.make_backup();self.dism();self.sfc();self.trim("C:");self.trim("D:");self.explorer();self.logit("SAFE BASELINE COMPLETE")

    def report(self):
        self.header("▤ REPORT","Complete system, hardware, storage, network, security, startup, software, components, health, backup and baseline report.")
        bar=tk.Frame(self.page,bg=BG); bar.pack(fill="x",padx=8,pady=8)
        ttk.Button(bar,text="📋 GENERATE COMPLETE REPORT",command=self.gen_report).pack(side="left",padx=(0,6))
        ttk.Button(bar,text="🔄 REFRESH REPORT",command=lambda:self.output_show("REPORT","READY","Ready to generate a fresh complete report.","SUCCESS")).pack(side="left",padx=6)
        ttk.Button(bar,text="📂 OPEN REPORT FOLDER",command=lambda:run(f'explorer "{self.log_root}"')).pack(side="left",padx=6)
        self.output_show("REPORT","READY","Generate Complete Report creates TXT + JSON copies under ProgramData\\ZYNTRASEC\\Logs.")

    def gen_report(self):
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        txt=self.log_root/f"ZYNTRASEC_Complete_Report_{stamp}.txt"
        jsn=self.log_root/f"ZYNTRASEC_Complete_Report_{stamp}.json"
        script=r'''
$ErrorActionPreference='SilentlyContinue'
$os=Get-CimInstance Win32_OperatingSystem
$cs=Get-CimInstance Win32_ComputerSystem
$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed
$bios=Get-CimInstance Win32_BIOS | Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate
$mb=Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer,Product,SerialNumber
$ram=@(Get-CimInstance Win32_PhysicalMemory | ForEach-Object {[pscustomobject]@{Bank=$_.BankLabel;CapacityGB=[math]::Round($_.Capacity/1GB,1);SpeedMHz=$_.Speed;Manufacturer=$_.Manufacturer;PartNumber=$_.PartNumber}})
$gpu=@(Get-CimInstance Win32_VideoController | ForEach-Object {[pscustomobject]@{Name=$_.Name;DriverVersion=$_.DriverVersion;VRAMGB=if($_.AdapterRAM){[math]::Round($_.AdapterRAM/1GB,1)}else{$null}}})
$disks=@(Get-PhysicalDisk | ForEach-Object {[pscustomobject]@{Name=$_.FriendlyName;MediaType=[string]$_.MediaType;BusType=[string]$_.BusType;Health=[string]$_.HealthStatus;SizeGB=if($_.Size){[math]::Round($_.Size/1GB,1)}else{$null}}})
$vols=@(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {[pscustomobject]@{Drive=$_.DeviceID;FileSystem=$_.FileSystem;SizeGB=[math]::Round($_.Size/1GB,1);FreeGB=[math]::Round($_.FreeSpace/1GB,1);UsedGB=[math]::Round(($_.Size-$_.FreeSpace)/1GB,1)}})
$nets=@(Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" | ForEach-Object {[pscustomobject]@{Description=$_.Description;MAC=$_.MACAddress;IP=$_.IPAddress;Gateway=$_.DefaultIPGateway;DNS=$_.DNSServerSearchOrder}})
$apps=@(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' | Where-Object {$_.DisplayName} | ForEach-Object {[pscustomobject]@{Name=$_.DisplayName;Version=$_.DisplayVersion;Publisher=$_.Publisher;InstallDate=$_.InstallDate}})
$startup=@(Get-CimInstance Win32_StartupCommand | ForEach-Object {[pscustomobject]@{Name=$_.Name;Command=$_.Command;Location=$_.Location;User=$_.User}})
$features=@(Get-WindowsOptionalFeature -Online | Where-Object {$_.State -ne 'Disabled'} | Select-Object FeatureName,State)
$bad=@(Get-PnpDevice -PresentOnly | Where-Object {$_.Status -ne 'OK'} | Select-Object Class,FriendlyName,Status,ProblemCode)
$firewall=@(Get-NetFirewallProfile | Select-Object Name,Enabled)
$defender=try { Get-MpComputerStatus | Select-Object AMServiceEnabled,AntivirusEnabled,RealTimeProtectionEnabled,AntispywareEnabled } catch {$null}
$uac=try { (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System').EnableLUA } catch {$null}
$restore=@(Get-ComputerRestorePoint | Select-Object CreationTime,Description,RestorePointType,SequenceNumber)
$updates=@(Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 20 HotFixID,InstalledOn,Description)
$obj=[ordered]@{
 GeneratedAt=(Get-Date).ToString('o'); Computer=$env:COMPUTERNAME; User=$env:USERNAME;
 Admin=([bool]([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator));
 System=[ordered]@{Windows=$os.Caption;Version=$os.Version;Build=$os.BuildNumber;Architecture=$os.OSArchitecture;InstallDate=$os.InstallDate;LastBoot=$os.LastBootUpTime;Manufacturer=$cs.Manufacturer;Model=$cs.Model;RAMGB=[math]::Round($cs.TotalPhysicalMemory/1GB,1);CPU=$cpu;BIOS=$bios;Motherboard=$mb};
 RAMModules=$ram; GPU=$gpu; PhysicalDisks=$disks; Volumes=$vols; Network=$nets;
 Software=[ordered]@{Count=$apps.Count;Items=$apps}; Startup=[ordered]@{Count=$startup.Count;Items=$startup}; WindowsComponents=$features;
 DeviceProblems=[ordered]@{Count=$bad.Count;Items=$bad}; Security=[ordered]@{Firewall=$firewall;Defender=$defender;UAC=$uac};
 Health=[ordered]@{RecentHotFixes=$updates}; Backup=[ordered]@{RestorePoints=$restore}
}
$obj | ConvertTo-Json -Depth 7 -Compress
'''
        def work():
            rc,out=ps(script,120)
            if rc!=0 or not out.strip(): raise RuntimeError(out.strip() or "Unable to build complete report.")
            data=json.loads(out.strip())
            pretty=json.dumps(data,indent=2,ensure_ascii=False)
            sysd=data.get('System') or {}
            sections=[
                "ZYNTRASEC // COMPLETE SYSTEM REPORT", "="*78,
                f"Generated : {data.get('GeneratedAt','')}", f"Computer  : {data.get('Computer','')}",
                f"User      : {data.get('User','')}", f"Admin     : {data.get('Admin')}", "",
                "[SYSTEM]", f"Windows       : {sysd.get('Windows','')}",
                f"Version/Build : {sysd.get('Version','')} / {sysd.get('Build','')}",
                f"Architecture  : {sysd.get('Architecture','')}",
                f"Model         : {sysd.get('Manufacturer','')} {sysd.get('Model','')}",
                f"RAM           : {sysd.get('RAMGB','')} GB", f"Last Boot     : {sysd.get('LastBoot','')}", "",
                "[CPU]", json.dumps(sysd.get('CPU') or {},indent=2,ensure_ascii=False), "",
                "[MOTHERBOARD]", json.dumps(sysd.get('Motherboard') or {},indent=2,ensure_ascii=False), "",
                "[BIOS]", json.dumps(sysd.get('BIOS') or {},indent=2,ensure_ascii=False), "",
                "[RAM MODULES]", json.dumps(data.get('RAMModules') or [],indent=2,ensure_ascii=False), "",
                "[GPU]", json.dumps(data.get('GPU') or [],indent=2,ensure_ascii=False), "",
                "[PHYSICAL DISKS]", json.dumps(data.get('PhysicalDisks') or [],indent=2,ensure_ascii=False), "",
                "[VOLUMES]", json.dumps(data.get('Volumes') or [],indent=2,ensure_ascii=False), "",
                "[NETWORK]", json.dumps(data.get('Network') or [],indent=2,ensure_ascii=False), "",
                "[SOFTWARE]", f"Total Apps: {(data.get('Software') or {}).get('Count',0)}",
                json.dumps((data.get('Software') or {}).get('Items') or [],indent=2,ensure_ascii=False), "",
                "[STARTUP]", f"Total Entries: {(data.get('Startup') or {}).get('Count',0)}",
                json.dumps((data.get('Startup') or {}).get('Items') or [],indent=2,ensure_ascii=False), "",
                "[WINDOWS COMPONENTS]", json.dumps(data.get('WindowsComponents') or [],indent=2,ensure_ascii=False), "",
                "[DEVICE PROBLEMS]", f"Count: {(data.get('DeviceProblems') or {}).get('Count',0)}",
                json.dumps((data.get('DeviceProblems') or {}).get('Items') or [],indent=2,ensure_ascii=False), "",
                "[SECURITY]", json.dumps(data.get('Security') or {},indent=2,ensure_ascii=False), "",
                "[HEALTH / RECENT HOTFIXES]", json.dumps((data.get('Health') or {}).get('RecentHotFixes') or [],indent=2,ensure_ascii=False), "",
                "[BACKUP / RESTORE POINTS]", json.dumps((data.get('Backup') or {}).get('RestorePoints') or [],indent=2,ensure_ascii=False), "",
                "[JSON COPY]", str(jsn), ""
            ]
            text="\n".join(sections)
            txt.write_text(text,encoding='utf-8')
            jsn.write_text(pretty,encoding='utf-8')
            return txt,jsn,text
        def done(r):
            t,j,text=r
            self.output_show("REPORT","GENERATE COMPLETE REPORT",text,"COMPLETE")
            self.logit(f"Complete report saved: {t}")
            self.logit(f"JSON report saved: {j}")
            messagebox.showinfo("ZYNTRASEC Report",f"TXT:\n{t}\n\nJSON:\n{j}")
        self._async_job(work,done,"GENERATING COMPLETE REPORT...")

if __name__=="__main__":
    if sys.platform!="win32":raise SystemExit("Windows only")
    App().mainloop()
