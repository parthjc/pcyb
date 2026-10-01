import subprocess
import sys
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import os,re,winreg,subprocess,csv,datetime,shutil,json,threading,queue


class ZyntrasecTooltip:
    """Lightweight bilingual hover help for ZYNTRASEC controls."""
    def __init__(self, widget, title, body, use_text=None, delay=500):
        self.widget=widget; self.title=title; self.body=body; self.use_text=use_text
        self.delay=delay; self.after_id=None; self.tip=None
        widget.bind('<Enter>', self._enter, add='+')
        widget.bind('<Leave>', self._leave, add='+')
        widget.bind('<ButtonPress>', self._leave, add='+')
    def _enter(self, _=None):
        self._leave()
        self.after_id=self.widget.after(self.delay, self.show)
    def _leave(self, _=None):
        if self.after_id:
            try:self.widget.after_cancel(self.after_id)
            except Exception:pass
            self.after_id=None
        self.hide()
    def show(self):
        self.after_id=None
        if not self.widget.winfo_exists(): return
        self.hide()
        x=self.widget.winfo_rootx()+12; y=self.widget.winfo_rooty()+self.widget.winfo_height()+6
        self.tip=tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True); self.tip.attributes('-topmost',True)
        frm=tk.Frame(self.tip,bg='#061006',highlightthickness=1,highlightbackground=GREEN)
        frm.pack()
        tk.Label(frm,text=self.title,bg='#061006',fg=GREEN,font=('Consolas',10,'bold'),anchor='w').pack(fill='x',padx=10,pady=(7,2))
        tk.Label(frm,text=self.body,bg='#061006',fg='#d7f7d7',font=('Consolas',9),justify='left',anchor='w',wraplength=560).pack(fill='x',padx=10,pady=(0,7))
        self.tip.update_idletasks()
        sw=self.tip.winfo_screenwidth(); sh=self.tip.winfo_screenheight()
        w=self.tip.winfo_width(); h=self.tip.winfo_height()
        x=min(x,max(5,sw-w-5)); y=min(y,max(5,sh-h-5))
        self.tip.geometry(f'+{x}+{y}')
    def hide(self):
        if self.tip:
            try:self.tip.destroy()
            except Exception:pass
            self.tip=None

TOOLTIP_HELP = {
    '⟳ SCAN': ('SCAN WINDOWS', 'Windows startup, services, scheduled tasks, processes અને related sources scan કરે છે.\nWhen to use: system માં automatically શું start થાય છે તે check કરવું હોય ત્યારે.'),
    'DETAILS / WHY': ('DETAILS / WHY', 'Selected item વિશે full details અને risk reason બતાવે છે.\nWhen to use: કોઈ item કેમ flagged છે તે સમજવું હોય ત્યારે.'),
    'WHAT HAPPENS?': ('WHAT HAPPENS?', 'Selected action કરવાથી Windows માં શું અસર થઈ શકે તે સમજાવે છે.\nWhen to use: RUN, DISABLE અથવા REMOVE પહેલાં effect સમજવો હોય ત્યારે.'),
    'RUN': ('RUN', 'Selected program/task/service ને start કરવાનો પ્રયાસ કરે છે.\nWhen to use: કોઈ item manually launch કરવો હોય ત્યારે.'),
    'STOP': ('STOP', 'Selected running process/service ને stop કરવાનો પ્રયાસ કરે છે.\nWhen to use: કોઈ active item બંધ કરવું હોય ત્યારે.'),
    'DISABLE': ('DISABLE', 'Item ને delete કર્યા વગર temporarily disable કરે છે.\nWhen to use: કોઈ startup/service જરૂરી છે કે નહીં તે test કરવું હોય ત્યારે.'),
    'ENABLE': ('ENABLE', 'Previously disabled item ને ફરીથી enable કરે છે.\nWhen to use: disabled startup/service/task પાછું ચાલુ કરવું હોય ત્યારે.'),
    'REMOVE': ('REMOVE', 'Selected item ને remove કરવાનો પ્રયાસ કરે છે અને supported cases માં backup પણ રાખે છે.\nWhen to use: unwanted અથવા broken item દૂર કરવું હોય ત્યારે.\nRisk: CAUTION — remove પહેલાં DETAILS અને backup check કરો.'),
    'PERMANENT DELETE': ('PERMANENT DELETE', 'Selected non-protected executable/file ને કાયમી રીતે delete કરવાનો પ્રયાસ કરે છે.\nWhen to use: program/file ખરેખર permanently કાઢવો હોય ત્યારે.\nRisk: HIGH — આ action undo/restore વગર હોઈ શકે છે.'),
    'OPEN LOCATION': ('OPEN LOCATION', 'Selected file/folder નું Windows location Explorer માં ખોલે છે.\nWhen to use: actual file ક્યાં છે તે તપાસવું હોય ત્યારે.'),
    'BACKUP': ('BACKUP', 'Selected configuration/item ની backup copy બનાવે છે.\nWhen to use: change અથવા removal પહેલાં rollback માટે.'),
    'BASELINE': ('BASELINE', 'હાલની Windows state ને comparison baseline તરીકે save કરે છે.\nWhen to use: પછી શું બદલાયું તે શોધવું હોય ત્યારે.'),
    'CHANGES': ('CHANGES', 'Current state અને saved baseline વચ્ચેના changes બતાવે છે.\nWhen to use: startup/service/task માં શું બદલાયું તે જોવા.'),
    'RESTORE': ('RESTORE CENTER', 'ZYNTRASEC backups માંથી supported configuration restore કરવાની જગ્યા ખોલે છે.\nWhen to use: અગાઉ backup કરેલી state પાછી લાવવી હોય ત્યારે.'),
    'BOOT CAPTURE': ('BOOT CAPTURE', 'Boot/startup દરમિયાન process information capture કરે છે.\nWhen to use: Windows startup સમયે શું launch થાય છે તે investigate કરવું હોય ત્યારે.'),
    'INSTALL BOOT CAPTURE': ('INSTALL BOOT CAPTURE', 'Boot capture માટે required monitoring setup install કરે છે.\nWhen to use: future startup evidence capture કરવું હોય ત્યારે.'),
    'ALL-IN-ONE FORENSICS': ('ALL-IN-ONE FORENSICS', 'Windows startup-related sources નું deeper combined scan કરે છે.\nWhen to use: startup issue નું broad investigation કરવું હોય ત્યારે.'),
    'EVENT SCAN 7D': ('EVENT SCAN 7D', 'છેલ્લા 7 દિવસના Windows Event Logs scan કરે છે.\nWhen to use: recent errors, warnings અથવા system events શોધવા.'),
    'ENABLE 4688': ('ENABLE 4688', 'Windows Process Creation auditing (Event ID 4688) enable કરવાનો પ્રયાસ કરે છે.\nWhen to use: future process-start events માટે વધુ audit data જોઈએ ત્યારે.'),
    'LAUNCH SOURCE SCAN': ('LAUNCH SOURCE SCAN', 'Common Windows launch locations scan કરે છે, જેમ કે Run keys, Startup folders, Tasks, Services અને Winlogon.\nWhen to use: કોઈ program Windows સાથે ક્યાંથી auto-start થાય છે તે શોધવા.'),
    'INTELLIGENCE HUB': ('INTELLIGENCE HUB', 'Search, health, broken items, duplicates, process tree, timeline અને dependency analysis આપે છે.\nWhen to use: overall system investigation માટે.'),
    '↻ REFRESH WINDOWS STATE': ('REFRESH WINDOWS STATE', 'Windows state ફરીથી scan કરીને ZYNTRASEC tables update કરે છે.\nWhen to use: change/remove/disable પછી latest result જોવા.'),
    'FILTER': ('FILTER', 'Event Log filters apply કરે છે અને matching events જ બતાવે છે.\nWhen to use: મોટી Event Log list માં specific events શોધવા.'),
    'CLEAR': ('CLEAR FILTERS', 'Event Log filters reset કરે છે અને full event list પાછી બતાવે છે.\nWhen to use: બધા filters દૂર કરવા.'),
    'SEARCH': ('SEARCH', 'Intelligence Hub ના current results માં keyword/text શોધે છે.\nWhen to use: name, path, provider અથવા અન્ય text ઝડપથી શોધવા.'),
    'HEALTH': ('HEALTH', 'Tracked items, broken/missing, unsigned અને changed items નું summary બતાવે છે.\nWhen to use: overall Windows state નો quick review.'),
    'BROKEN / MISSING': ('BROKEN / MISSING', 'જે tracked entries નું target/path missing અથવા unavailable લાગે છે તે બતાવે છે.\nWhen to use: orphaned અથવા broken entries શોધવા.'),
    'DUPLICATES': ('DUPLICATES', 'Repeated/similar tracked entries શોધે છે.\nWhen to use: duplicate startup/configuration entries તપાસવા.'),
    'PROCESS TREE': ('PROCESS TREE', 'Parent process → child process relationship બતાવે છે.\nWhen to use: કયા process એ બીજો process launch કર્યો તે સમજવા.'),
    'TIMELINE': ('TIMELINE', 'Startup અને Event Log information ને time order માં બતાવે છે.\nWhen to use: event sequence સમજવા.'),
    'SERVICE DEPENDENCIES': ('SERVICE DEPENDENCIES', 'Windows services ની required/dependent services બતાવે છે.\nWhen to use: service stop/disable કરતાં પહેલાં dependencies સમજવા.'),
    'SAFE REMOVE PREVIEW': ('SAFE REMOVE PREVIEW', 'Remove કર્યા વગર selected item માટે proposed removal preview બતાવે છે.\nWhen to use: action પહેલાં review કરવું હોય ત્યારે.'),
    'RESTORE CENTER': ('RESTORE CENTER', 'Available ZYNTRASEC backups જોવા અને restore workflow ખોલવા માટે.\nWhen to use: previous configuration પાછી લાવવી હોય ત્યારે.'),
    'REFRESH MAIN DATA': ('REFRESH MAIN DATA', 'Main ZYNTRASEC scan ફરીથી ચલાવે છે અને current tables update કરે છે.\nWhen to use: latest Windows state જોઈએ ત્યારે.'),
}

def _tooltip_for_text(text):
    t=' '.join(str(text or '').split())
    if t in TOOLTIP_HELP: return TOOLTIP_HELP[t]
    if t in ('SEARCH >>','SEARCH'): return TOOLTIP_HELP['SEARCH']
    if t in ('Provider','Event ID','Search'): return (t.upper(), f'Event Logs માં {t} પ્રમાણે filter/search કરવા માટેનું field.\nWhen to use: specific Windows event શોધતી વખતે.')
    detailed = {
        'GLOBAL FILTERS': ('GLOBAL FILTERS', 'Risk, Company અને Signature પ્રમાણે આખી ZYNTRASEC list ને narrow કરે છે.\nWhen to use: મોટી list માં ચોક્કસ પ્રકારના items જોવા.\nEffect: માત્ર matching rows દેખાશે; Windows setting બદલાતી નથી.'),
        'RISK': ('RISK FILTER', 'LOW / MEDIUM / HIGH / VERY HIGH review-priority પ્રમાણે rows filter કરે છે.\nWhen to use: review માટે specific risk level જોવા.\nNote: Risk label malware verdict નથી.'),
        'COMPANY': ('COMPANY FILTER', 'Microsoft / 3rd Party / Unknown company પ્રમાણે rows filter કરે છે.\nWhen to use: known Microsoft items અને third-party items અલગ જોવા.'),
        'SIGNATURE': ('SIGNATURE FILTER', 'Valid / Not Signed / Invalid / Unknown digital-signature state પ્રમાણે rows filter કરે છે.\nWhen to use: executable trust/signature status review કરવા.'),
        'EVENT LOG FILTER': ('EVENT LOG FILTER', 'Windows Event Logs ને Level, Log, Provider, Event ID અને Search પ્રમાણે filter કરે છે.\nWhen to use: specific error, warning અથવા event શોધવા.'),
        'CLEAR': ('CLEAR FILTERS', 'હાલના Event Log filters reset કરે છે.\nWhen to use: બધા filters દૂર કરીને full list પાછી જોવા.\nEffect: data delete થતો નથી.'),
        'SEARCH EVERYTHING': ('SEARCH EVERYTHING', 'ZYNTRASEC ના current scanned data માં name, path, company અને related text શોધે છે.\nWhen to use: કોઈ program/file/service/task ઝડપથી શોધવા.'),
        'BACKUP / RESTORE CENTER': ('BACKUP / RESTORE CENTER', 'Backups બનાવવા અને અગાઉની supported configuration restore કરવા માટેનું center.\nWhen to use: change/remove પહેલાં safety copy રાખવી અથવા rollback કરવું.'),
        'BASELINE DELTA // NEW • CHANGED • REMOVED': ('BASELINE DELTA', 'Saved baseline સાથે હાલની Windows state compare કરે છે અને NEW / CHANGED / REMOVED entries બતાવે છે.\nWhen to use: સમય સાથે શું બદલાયું તે શોધવા.'),
        'OPEN SELECTED BACKUP': ('OPEN SELECTED BACKUP', 'Selected backup file/folder ને Windows માં open કરે છે.\nWhen to use: backup inspect અથવા manually review કરવા.'),
        'REFRESH MAIN DATA': ('REFRESH MAIN DATA', 'Main Windows scan ફરીથી ચલાવે છે.\nWhen to use: Disable, Enable, Remove અથવા અન્ય change પછી latest state જોવા.'),
        'SEARCH >>': ('SEARCH', 'Intelligence Hub માં keyword search શરૂ કરે છે.\nWhen to use: કોઈ item, path, provider અથવા company શોધવા.'),
        '0': ('COUNT / LIMIT', '0 સામાન્ય રીતે ALL અથવા no-limit mode દર્શાવે છે જ્યાં તે option લાગુ પડે છે.\nWhen to use: available બધા matching results જોવા.'),
        'RISK:': ('RISK LEGEND', 'LOW, MEDIUM, HIGH અને VERY HIGH rows ની review priority સમજાવે છે.\nImportant: આ malware verdict નથી.'),
        'FAST RISK REVIEW • NOT A MALWARE VERDICT': ('RISK REVIEW NOTICE', 'ZYNTRASEC fast indicators પરથી review priority આપે છે.\nImportant: HIGH/VERY HIGH એટલે malware સાબિત થયું એવું નથી.'),
    }
    if t in detailed: return detailed[t]
    if t in ('LOW','MEDIUM','HIGH','VERY HIGH'):
        return (t, f'{t} review-priority filter.\nWhen to use: આ level ના matching items જ જોવા.\nEffect: માત્ર display filter બદલાય છે; Windows configuration બદલાતી નથી.')
    if t in ('ALL',):
        return ('ALL', 'બધા matching results બતાવે છે.\nWhen to use: કોઈ category filter લાગુ ન કરવો હોય ત્યારે.')
    if t in ('VALID','NOT SIGNED','INVALID','UNKNOWN'):
        return (t, f'Digital signature state: {t}.\nWhen to use: executable signature status પ્રમાણે entries review કરવા.')
    if t in ('MICROSOFT','3RD PARTY'):
        return (t, f'Company category: {t}.\nWhen to use: publisher પ્રમાણે Windows items અલગ જોવા.')
    return None

APP="ZYNTRASEC // WINDOWS CONTROL NODE V46 // FULL ADMIN"
BG="#030603"; PANEL="#071007"; GREEN="#39ff14"; DIM="#82b982"; AMBER="#ffd54a"; RED="#ff5252"; PURPLE="#ff62d6"


# ZYNTRASEC V44 — ALWAYS ADMIN / UAC SELF-ELEVATION
# Uses normal Windows UAC; no UAC bypass.

def _zyntrasec_hidden_kwargs(kwargs):
    """Keep helper processes invisible on Windows (no console window)."""
    if os.name == "nt":
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kwargs.setdefault("startupinfo", si)
            kwargs.setdefault("creationflags", getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000))
        except Exception:
            pass
    return kwargs

def _zyntrasec_run(*args, **kwargs):
    return subprocess.run(*args, **_zyntrasec_hidden_kwargs(kwargs))

def _zyntrasec_check_output(*args, **kwargs):
    return subprocess.check_output(*args, **_zyntrasec_hidden_kwargs(kwargs))

def _zyntrasec_popen(*args, **kwargs):
    hidden = kwargs.pop("hidden", True)
    return subprocess.Popen(*args, **(_zyntrasec_hidden_kwargs(kwargs) if hidden else kwargs))

def _zyntrasec_powershell_admin(script_text, wait=True):
    """Run PowerShell with Administrator verb. UAC is handled by Windows."""
    import tempfile
    ps_path = None
    try:
        fd, ps_path = tempfile.mkstemp(prefix="ZYNTRASEC_", suffix=".ps1")
        import os as _os
        with _os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(script_text)
        args = f'-NoProfile -ExecutionPolicy Bypass -File "{ps_path}"'
        return _zyntrasec_run(
            ["powershell.exe", "-NoProfile", "-Command",
             f'Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList \'{args}\' {"-Wait" if wait else ""}'],
            capture_output=True, text=True
        )
    finally:
        if ps_path:
            try:
                import os as _os
                _os.remove(ps_path)
            except Exception:
                pass

def _zyntrasec_is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def _zyntrasec_relaunch_as_admin():
    try:
        params = subprocess.list2cmdline(sys.argv)
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, os.getcwd(), 1
        )
        return rc > 32
    except Exception:
        return False

def _zyntrasec_require_admin():
    if _zyntrasec_is_admin():
        return True
    if _zyntrasec_relaunch_as_admin():
        raise SystemExit(0)
    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            "ZYNTRASEC requires Administrator permission. Please choose Yes in the UAC prompt.",
            "ZYNTRASEC - Administrator Required",
            0x10
        )
    except Exception:
        pass
    raise SystemExit(1)

def cmd(args,timeout=10):
    try:return _zyntrasec_run(args,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)
    except:return None

def ps(s,timeout=10): return cmd(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",s],timeout)

def exe_from(s):
    s=str(s or "").strip()
    m=re.search(r'([A-Za-z]:\\[^"\r\n]*?\.(?:exe|com|bat|cmd|ps1|vbs|js|dll))',s,re.I)
    if m:return m.group(1)
    if s.startswith('"'):
        z=s.find('"',1)
        if z>0:return s[1:z]
    return s.split()[0] if s else ""

def fast_risk(x):
    """Fast heuristic review score. It is NOT a malware verdict."""
    text=(str(x.get("target",""))+" "+str(x.get("name",""))+" "+str(x.get("source",""))).lower()
    p=os.path.normcase(x.get("exe") or exe_from(x.get("target","")))
    windir=os.path.normcase(os.environ.get("WINDIR",r"C:\Windows"))
    pf=os.path.normcase(os.environ.get("ProgramFiles",r"C:\Program Files"))
    pf86=os.path.normcase(os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))
    appdata=os.path.normcase(os.environ.get("APPDATA",""))
    localapp=os.path.normcase(os.environ.get("LOCALAPPDATA",""))
    tmp=os.path.normcase(os.environ.get("TEMP",""))
    score=0; reasons=[]
    if p.startswith(windir+os.sep):
        score-=2; reasons.append("Windows system path")
    elif p.startswith(pf+os.sep) or p.startswith(pf86+os.sep):
        score-=1; reasons.append("Program Files path")
    if appdata and p.startswith(appdata): score+=2;reasons.append("User AppData path")
    if localapp and p.startswith(localapp): score+=2;reasons.append("User LocalAppData path")
    if tmp and p.startswith(tmp): score+=3;reasons.append("TEMP path")
    if any(z in text for z in ("powershell","-enc","-encodedcommand","wscript","cscript","mshta")):
        score+=3;reasons.append("Script/interpreter command")
    if any(z in text for z in ("javascript:","frombase64string","downloadstring","invoke-expression")):
        score+=3;reasons.append("Obfuscation/download indicator")
    if any(z in text for z in ("\\downloads\\","\\desktop\\")):
        score+=2;reasons.append("User-writable location")
    if x.get("source") in ("Registry Run","User Startup","All Users Startup","Task Scheduler","Winlogon"):
        score+=1;reasons.append("Persistence mechanism")
    if x.get("service"):
        # Services are not inherently dangerous; automatic service is only a persistence mechanism.
        score+=0;reasons.append("Automatic service")
    if p.lower().endswith((".bat",".cmd",".ps1",".vbs",".js",".hta")):
        score+=2;reasons.append("Script file")
    if score<=-1: level="LOW"; label="LOW / SYSTEM"; color=GREEN
    elif score<=1: level="LOW"; label="LOW"; color=GREEN
    elif score<=3: level="MEDIUM"; label="MEDIUM"; color=AMBER
    elif score<=5: level="HIGH"; label="HIGH"; color=RED
    else: level="VERY HIGH"; label="VERY HIGH"; color=PURPLE
    if not reasons: reasons=["No strong fast-risk indicators found"]
    return level,label,"; ".join(reasons),score

def recommendation(x):
    name=str(x.get("name","")).lower()
    source=str(x.get("source","")).lower()
    target=str(x.get("target",""))
    path=os.path.normcase(os.path.expandvars(x.get("exe") or exe_from(target)))
    windir=os.path.normcase(os.environ.get("WINDIR",r"C:\Windows"))
    pf=os.path.normcase(os.environ.get("ProgramFiles",r"C:\Program Files"))
    pf86=os.path.normcase(os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))

    # Never call core Windows components "safe to remove".
    if path.startswith(windir+os.sep) or source=="windows service":
        core_names=("rpc","dcom","winmgmt","eventlog","plug and play","dhcp","dns","bits",
                    "crypt","defender","security","lsm","wininit","winlogon","services",
                    "audioendpointbuilder","audiosrv","brokerinfrastructure","camsvc")
        if any(k in name for k in core_names):
            return ("DO NOT REMOVE","CORE WINDOWS / REQUIRED","Removing or disabling can affect Windows, networking, security, audio, login, or updates.")
        return ("CAUTION","WINDOWS SERVICE","Disable/remove only after confirming what depends on this service.")

    # Common third-party updater/background services.
    third_party_optional=("brave","bonjour","adobe","google update","edge update",
                          "onedrive","nvidia geforce experience","nahimic")
    if any(k in name or k in path for k in third_party_optional):
        return ("OPTIONAL","THIRD-PARTY","Usually optional background/update functionality; disable first and test the related app before removing.")

    # Startup entries in user-writable locations are removable only after backup.
    if source in ("registry run","user startup","all users startup","task scheduler"):
        if path.startswith(pf+os.sep) or path.startswith(pf86+os.sep):
            return ("REVIEW","THIRD-PARTY STARTUP","Disable first. If the related app is unused, removal generally affects that app's auto-start/update behavior, not Windows itself.")
        return ("CAUTION","STARTUP ENTRY","Backup first and disable before removing; effect depends on the application.")

    if source=="process":
        return ("RUNNING ONLY","PROCESS","Stopping ends the current process; it does not remove the program or change Windows startup configuration.")

    return ("REVIEW","UNKNOWN","Identify the publisher and signature before disabling or removing.")

def file_signature(path):
    if not path or not os.path.isfile(path): return ("Unknown","Unknown")
    try:
        r=ps("(Get-AuthenticodeSignature -LiteralPath '"+path.replace("'","''")+"').Status",8)
        return (r.stdout.strip() or "Unknown","checked")
    except:return ("Unknown","error")

def company(path):
    if not path or not os.path.isfile(path):return "Unknown"
    p=os.path.normcase(path);w=os.path.normcase(os.environ.get("WINDIR",r"C:\Windows"))
    if p.startswith(w+os.sep):return "Microsoft Corporation"
    try:
        r=ps("(Get-Item -LiteralPath '"+path.replace("'","''")+"').VersionInfo.CompanyName",8)
        return r.stdout.strip() or "Unknown"
    except:return "Unknown"

class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title(APP);self.geometry("1600x900");self.minsize(1150,650);self.configure(bg=BG)
        self.startup=[];self.tasks=[];self.services=[];self.processes=[];self.winlogon=[];self.current=[];self.q=queue.Queue();self.scanning=False
        self.baseline_file=os.path.join("backup","baseline.json");self.changes={}
        self.build();self.after(150,self.scan);self.after(100,self.poll)

    def style(self):
        s=ttk.Style(self);s.theme_use("clam")
        s.configure("Treeview",background=PANEL,foreground=GREEN,fieldbackground=PANEL,rowheight=28,font=("Consolas",9))
        s.configure("Treeview.Heading",background="#102010",foreground=GREEN,font=("Consolas",9,"bold"))
        s.map("Treeview",background=[("selected","#164916")],foreground=[("selected","#fff")])
        s.configure("TButton",background="#0d1d0d",foreground=GREEN,font=("Consolas",9,"bold"),padding=7)
        s.configure("TNotebook",background=BG);s.configure("TNotebook.Tab",background="#0a150a",foreground=GREEN,font=("Consolas",9,"bold"),padding=(12,8))
        s.map("TNotebook.Tab",background=[("selected","#163016")])

    def build(self):
        self.style()
        h=tk.Frame(self,bg=BG);h.pack(fill="x",padx=14,pady=(10,4))
        tk.Label(h,text=APP,bg=BG,fg=GREEN,font=("Consolas",18,"bold")).pack(side="left")
        tk.Label(h,text="FAST RISK REVIEW • NOT A MALWARE VERDICT",bg=BG,fg=DIM,font=("Consolas",9,"bold")).pack(side="left",padx=20)
        self.state=tk.Label(h,text="● READY",bg=BG,fg=GREEN,font=("Consolas",10));self.state.pack(side="right")
        cards=tk.Frame(self,bg="#061006");cards.pack(fill="x",padx=14,pady=4)
        self.cards=[]
        for title in ("AUTO START","STARTUP TASKS","AUTO SERVICES","PROCESSES","HIGH+ REVIEW","CHANGES","3RD PARTY"):
            f=tk.Frame(cards,bg="#0a150a",highlightthickness=1,highlightbackground="#183318");f.pack(side="left",expand=True,fill="x",padx=3,pady=3)
            tk.Label(f,text=title,bg="#0a150a",fg=DIM,font=("Consolas",8,"bold")).pack()
            l=tk.Label(f,text="0",bg="#0a150a",fg=GREEN,font=("Consolas",15,"bold"));l.pack();self.cards.append(l)
        bar=tk.Frame(self,bg=BG);bar.pack(fill="x",padx=14,pady=4)
        for t,c in [("⟳ SCAN",self.scan),("DETAILS / WHY",self.details),("WHAT HAPPENS?",self.what_happens),("RUN",self.run_now),("STOP",self.stop_now),("DISABLE",self.disable),("ENABLE",self.enable),("REMOVE",self.remove),("PERMANENT DELETE",self.permanent_delete),("OPEN LOCATION",self.open_location),("BACKUP",self.backup),("BASELINE",self.set_baseline),("CHANGES",self.show_changes),("RESTORE",self.restore_center)]:
            ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        tk.Label(bar,text="SEARCH >>",bg=BG,fg=DIM,font=("Consolas",9,"bold")).pack(side="right")
        self.risk_filter=""; self.company_filter=""; self.signature_filter=""; self.startup_issues=[]; self.boot_events=[]; self.event_logs=[]; self.launch_sources=[]; self.capture_seconds=30; self.boot_log_file=os.path.join(os.path.dirname(os.path.abspath(__file__)),"backup","boot_capture.jsonl");
        self.search=tk.StringVar();self.search.trace_add("write",lambda *a:self.populate())
        tk.Entry(bar,textvariable=self.search,bg="#010201",fg=GREEN,insertbackground=GREEN,font=("Consolas",10),relief="flat",width=28).pack(side="right",padx=5)
        legend=tk.Frame(self,bg=BG)
        legend.pack(fill="x",padx=14,pady=(0,3))
        tk.Label(legend,text="RISK:",bg=BG,fg=DIM,font=("Consolas",9,"bold")).pack(side="left",padx=(4,8))
        for txt,color in [("LOW","#39ff14"),("MEDIUM","#ffd54a"),("HIGH","#ff8a00"),("VERY HIGH","#ff3b30")]:
            tk.Label(legend,text="■ "+txt,bg=BG,fg=color,font=("Consolas",9,"bold")).pack(side="left",padx=8)
        tk.Label(legend,text="  Row color = review priority • not a malware verdict",bg=BG,fg=DIM,font=("Consolas",9)).pack(side="left",padx=10)
        # Modern section divider / live status strip
        status_strip=tk.Frame(self,bg="#020702",highlightthickness=1,highlightbackground="#173617")
        status_strip.pack(fill="x",padx=14,pady=(0,5))
        tk.Button(bar,text="BOOT CAPTURE",command=self.run_full_startup_audit,bg="#081408",fg="#54d6ff",activebackground="#174817",activeforeground="#ffffff",relief="flat",font=("Consolas",9,"bold"),padx=10).pack(side="left",padx=3)
        tk.Button(bar,text="INSTALL BOOT CAPTURE",command=self.install_boot_capture,bg="#081408",fg="#ffd54a",activebackground="#174817",activeforeground="#ffffff",relief="flat",font=("Consolas",9,"bold"),padx=10).pack(side="left",padx=3)
        tk.Button(bar,text="ALL-IN-ONE FORENSICS",command=lambda: threading.Thread(target=self.scan_all_windows_startup_forensics,daemon=True).start(),bg="#081408",fg="#ff4d4d",activebackground="#174817",activeforeground="#ffffff",relief="flat",font=("Consolas",9,"bold"),padx=10).pack(side="left",padx=3)
        tk.Button(bar,text="EVENT SCAN 7D",command=lambda: threading.Thread(target=self.scan_event_logs,args=(168,),daemon=True).start(),bg="#081408",fg="#54d6ff",activebackground="#174817",activeforeground="#ffffff",relief="flat",font=("Consolas",9,"bold"),padx=10).pack(side="left",padx=3)
        tk.Button(bar,text="ENABLE 4688",command=self.enable_process_creation_audit,bg="#081408",fg="#ffd54a",activebackground="#174817",activeforeground="#ffffff",relief="flat",font=("Consolas",9,"bold"),padx=10).pack(side="left",padx=3)
        tk.Button(bar,text="LAUNCH SOURCE SCAN",command=lambda: threading.Thread(target=self.scan_launch_sources,daemon=True).start(),bg="#081408",fg="#ff4d4d",activebackground="#174817",activeforeground="#ffffff",relief="flat",font=("Consolas",9,"bold"),padx=10).pack(side="left",padx=3)
        tk.Button(bar,text="INTELLIGENCE HUB",command=self.open_intelligence_hub,bg="#081408",fg="#b66cff",activebackground="#174817",activeforeground="#ffffff",relief="flat",font=("Consolas",9,"bold"),padx=10).pack(side="left",padx=3)
        refresh_row=tk.Frame(self,bg=BG)
        refresh_row.pack(fill="x",padx=18,pady=(2,2))
        tk.Button(refresh_row,text="↻ REFRESH WINDOWS STATE",command=self.refresh_all,
                  bg="#0b180b",fg="#39ff14",activebackground="#174817",
                  activeforeground="#ffffff",relief="solid",bd=1,
                  font=("Consolas",10,"bold"),padx=14,pady=3).pack(side="left")
        tk.Label(refresh_row,text="  Re-scan current startup/services/tasks/processes and verify removals",
                 bg=BG,fg="#7fcf7f",font=("Consolas",9)).pack(side="left",padx=8)
        global_filters_box=tk.Frame(self,bg="#061006",highlightthickness=1,highlightbackground="#214021")
        global_filters_box.pack(fill="x",padx=14,pady=(1,3))
        tk.Label(global_filters_box,text="GLOBAL FILTERS",bg="#061006",fg=GREEN,font=("Consolas",8,"bold")).pack(side="left",padx=(8,4))

        quick=tk.Frame(global_filters_box,bg="#061006");quick.pack(side="left",padx=2,pady=2)
        tk.Label(quick,text="RISK",bg="#061006",fg=DIM,font=("Consolas",8,"bold")).pack(side="left",padx=3)
        self.filter_buttons={}
        for label,val,color in [("ALL","",GREEN),("LOW","LOW","#39ff14"),("MEDIUM","MEDIUM","#ffd54a"),("HIGH","HIGH","#ff8a00"),("VERY HIGH","VERY HIGH","#ff3b30")]:
            b=tk.Button(quick,text=label,bg="#081408",fg=color,activebackground="#153815",activeforeground="#ffffff",relief="flat",bd=0,font=("Consolas",8,"bold"),padx=9,pady=2,command=lambda v=val:self.set_risk_filter(v))
            b.pack(side="left",padx=1);self.filter_buttons[val]=b

        company_row=tk.Frame(global_filters_box,bg="#061006");company_row.pack(side="left",padx=5,pady=2)
        tk.Label(company_row,text="COMPANY",bg="#061006",fg=DIM,font=("Consolas",8,"bold")).pack(side="left",padx=3)
        self.company_buttons={}
        for label,val,color in [("ALL","",GREEN),("MICROSOFT","MICROSOFT","#54d6ff"),("3RD PARTY","3RD PARTY","#7dff7d"),("UNKNOWN","UNKNOWN","#bdbdbd")]:
            b=tk.Button(company_row,text=label,bg="#081408",fg=color,activebackground="#174817",activeforeground="#ffffff",relief="flat",bd=0,font=("Consolas",8,"bold"),padx=8,pady=2,command=lambda v=val:self.set_company_filter(v))
            b.pack(side="left",padx=1);self.company_buttons[val]=b

        signature_row=tk.Frame(global_filters_box,bg="#061006");signature_row.pack(side="left",padx=5,pady=2)
        tk.Label(signature_row,text="SIGNATURE",bg="#061006",fg=DIM,font=("Consolas",8,"bold")).pack(side="left",padx=3)
        self.signature_buttons={}
        for label,val,color in [("ALL","",GREEN),("VALID","VALID","#39ff14"),("NOT SIGNED","NOTSIGNED","#ffd54a"),("INVALID","INVALID","#ff3b30"),("UNKNOWN","UNKNOWN","#bdbdbd")]:
            b=tk.Button(signature_row,text=label,bg="#081408",fg=color,activebackground="#174817",activeforeground="#ffffff",relief="flat",bd=0,font=("Consolas",8,"bold"),padx=8,pady=2,command=lambda v=val:self.set_signature_filter(v))
            b.pack(side="left",padx=1);self.signature_buttons[val]=b

        self.live_status=tk.Label(status_strip,text="● SYSTEM READY",bg="#020702",fg=GREEN,font=("Consolas",9,"bold"))
        self.live_status.pack(side="left",padx=10,pady=5)
        self.selection_status=tk.Label(status_strip,text="NO ITEM SELECTED",bg="#020702",fg=DIM,font=("Consolas",9))
        self.selection_status.pack(side="right",padx=10,pady=5)
        self.nb=ttk.Notebook(self);self.nb.pack(fill="both",expand=True,padx=14,pady=5)
        self.tabs={}
        for name in ["AUTO START","STARTUP APPS","SERVICES","TASK SCHEDULER","PROCESSES","REGISTRY RUN","STARTUP FOLDERS","WINLOGON","STARTUP ISSUES","LAUNCH SOURCES","BOOT CAPTURE","EVENT LOGS"]:
            fr=tk.Frame(self.nb,bg=BG);self.nb.add(fr,text=" "+name+" ");self.tabs[name]=fr
        self.make_tables();self.load_boot_log()
        try:
            with open(os.path.join("backup","launch_sources.json"),"r",encoding="utf-8") as f: self.launch_sources=json.load(f)
        except Exception: pass
        self.nb.bind("<<NotebookTabChanged>>",self.on_tab_changed)
        # Responsive details pane: selecting a row updates it instantly.
        details_box=tk.Frame(self,bg="#061006",highlightthickness=1,highlightbackground="#214021")
        details_box.pack(fill="x",padx=14,pady=(0,4))
        top=tk.Frame(details_box,bg="#061006");top.pack(fill="x")
        tk.Label(top,text="SELECTED ITEM // FULL DETAILS",bg="#061006",fg=GREEN,font=("Consolas",9,"bold")).pack(side="left",padx=8,pady=4)
        self.detail_status=tk.Label(top,text="NO ITEM SELECTED",bg="#061006",fg=DIM,font=("Consolas",9,"bold"));self.detail_status.pack(side="right",padx=8)
        self.detail_text=tk.Text(details_box,height=8,bg="#020502",fg=GREEN,insertbackground=GREEN,
                                 font=("Consolas",9),relief="flat",wrap="none")
        self.detail_text.pack(fill="x",padx=6,pady=(0,6))
        self.detail_text.configure(state="disabled")
        self.progress=ttk.Progressbar(self,mode="indeterminate");self.progress.pack(fill="x",padx=14,pady=(0,4))
        footer=tk.Label(self,text="F5 SCAN   •   ENTER DETAILS   •   ESC CLEAR SEARCH   •   DOUBLE-CLICK ROW FOR FULL DETAILS",
                        bg=BG,fg=DIM,font=("Consolas",8),anchor="w")
        footer.pack(fill="x",padx=16,pady=(0,6))
        tk.Label(self,text="LOW / MEDIUM / HIGH / VERY HIGH = review priority from fast indicators. A label is NOT proof that a file is malware.",bg="#020402",fg=DIM,font=("Consolas",9),anchor="w").pack(fill="x",side="bottom")
        self.after(200, self.install_hover_help)


    def install_hover_help(self):
        # Attach bilingual help to every visible interactive control.
        seen=set()
        def walk(w):
            try:
                txt=w.cget('text')
            except Exception: txt=''
            help_pair=_tooltip_for_text(txt)
            if not help_pair:
                try:
                    cls=w.winfo_class()
                    if cls in ('TCombobox','Combobox'):
                        vals=list(w.cget('values'))
                        label = vals[0] if vals else 'SELECT OPTION'
                        help_pair=(label, 'આ dropdown નો option select કરીને display/filter/action mode બદલો.\nWhen to use: જરૂરી category અથવા state પસંદ કરવી હોય ત્યારે.\nEffect: સામાન્ય રીતે માત્ર view/filter બદલાય છે, જ્યાં action explicitly બતાવેલ ન હોય.')
                    elif cls in ('Entry','TEntry'):
                        help_pair=('TEXT FIELD', 'અહીં keyword, Provider, Event ID અથવા અન્ય search/filter text લખી શકાય છે.\nWhen to use: specific item/event શોધવા.\nEffect: Search/Filter ચલાવ્યા પછી matching results દેખાશે.')
                except Exception:
                    pass
            if help_pair and str(w) not in seen:
                seen.add(str(w)); ZyntrasecTooltip(w,help_pair[0],help_pair[1])
            for child in w.winfo_children(): walk(child)
        walk(self)
        # Notebook tabs are virtual elements, so handle them separately.
        self.nb.bind('<Motion>', self._tooltip_tab_motion, add='+')
        self.nb.bind('<Leave>', self._tooltip_tab_leave, add='+')
        self._tab_tip=None; self._tab_after=None

    def _tooltip_tab_motion(self, ev):
        try: idx=self.nb.index('@%d,%d' % (ev.x,ev.y))
        except Exception: return
        try: name=self.nb.tab(idx,'text').strip()
        except Exception: return
        if self._tab_after:
            try:self.after_cancel(self._tab_after)
            except Exception:pass
        self._tab_after=self.after(500, lambda n=name: self._show_tab_tip(n,ev.x_root,ev.y_root))

    def _show_tab_tip(self,name,x,y):
        self._hide_tab_tip()
        descriptions={
          'AUTO START':'WHAT IT DOES: Common Windows automatic-start locations ની combined list.\nWHEN TO USE: Windows boot/sign-in વખતે શું launch થાય છે તે જોવા.\nEFFECT: View-only scan; action button વાપરો ત્યારે જ setting બદલાય.\nRISK: Review priority only.',
          'STARTUP APPS':'WHAT IT DOES: Task Manager જેવી Startup Apps inventory, including enabled/disabled state.\nWHEN TO USE: Sign-in સમયે કઈ apps launch થઈ શકે તે જોવા અને Enable/Disable કરવા.\nEFFECT: Startup state બદલાઈ શકે છે.\nRISK: CAUTION — essential apps disable કરતાં પહેલાં Details જુઓ.',
          'SERVICES':'WHAT IT DOES: Windows Services, state, startup mode, path અને dependencies બતાવે છે.\nWHEN TO USE: Background services તપાસવા.\nEFFECT: Disable/Enable/Stop/Remove actions service configuration બદલી શકે.\nRISK: CAUTION — system services પર ખાસ ધ્યાન.',
          'TASK SCHEDULER':'WHAT IT DOES: Scheduled Tasks અને તેમના triggers/actions બતાવે છે.\nWHEN TO USE: Time/event/logon પર auto-run થતી વસ્તુ શોધવા.\nEFFECT: Enable/Disable/Run actions task state બદલી શકે.',
          'PROCESSES':'WHAT IT DOES: હાલના running processes અને executable paths બતાવે છે.\nWHEN TO USE: Active program અથવા process relationship તપાસવા.\nEFFECT: Stop action running process બંધ કરી શકે.',
          'REGISTRY RUN':'WHAT IT DOES: Registry Run/RunOnce startup entries બતાવે છે.\nWHEN TO USE: Registry મારફતે auto-start શોધવા.\nEFFECT: Remove/disable action registry startup configuration બદલી શકે.',
          'STARTUP FOLDERS':'WHAT IT DOES: Windows Startup folders માં programs/shortcuts શોધે છે.\nWHEN TO USE: Folder-based auto-start entries તપાસવા.\nEFFECT: Removal/disable supported entries પર અસર કરી શકે.',
          'WINLOGON':'WHAT IT DOES: Shell/Userinit જેવી Winlogon startup settings બતાવે છે.\nWHEN TO USE: Logon startup configuration investigate કરવા.\nEFFECT: Changes Windows logon behavior પર અસર કરી શકે.\nRISK: HIGH CAUTION.',
          'STARTUP ISSUES':'WHAT IT DOES: Missing/broken targets અને startup review signals બતાવે છે.\nWHEN TO USE: Broken startup entries શોધવા.\nEFFECT: Normally diagnostic view; action અલગથી પસંદ કરવો પડે.',
          'LAUNCH SOURCES':'WHAT IT DOES: Run keys, Startup folders, Tasks, Services અને Winlogon જેવા launch sources જોડીને બતાવે છે.\nWHEN TO USE: કોઈ program auto-start ક્યાંથી થાય છે તે trace કરવા.',
          'BOOT CAPTURE':'WHAT IT DOES: Boot/startup process observations capture કરે છે.\nWHEN TO USE: Windows startup સમયે શું launch થાય છે તે investigate કરવા.\nEFFECT: Monitoring/capture data બનાવે છે.',
          'EVENT LOGS':'WHAT IT DOES: Windows Event Viewer-style events અને message/details બતાવે છે.\nWHEN TO USE: Errors, warnings, crashes અથવા system activity તપાસવા.\nEFFECT: Filters માત્ર display બદલે છે; logs delete થતા નથી.'}
        body=descriptions.get(name)
        if not body:return
        self._tab_tip=tk.Toplevel(self);self._tab_tip.wm_overrideredirect(True);self._tab_tip.attributes('-topmost',True)
        f=tk.Frame(self._tab_tip,bg='#061006',highlightthickness=1,highlightbackground=GREEN);f.pack()
        tk.Label(f,text=name,bg='#061006',fg=GREEN,font=('Consolas',10,'bold')).pack(anchor='w',padx=10,pady=(7,2))
        tk.Label(f,text=body,bg='#061006',fg='#d7f7d7',font=('Consolas',9),justify='left',wraplength=520).pack(anchor='w',padx=10,pady=(0,7))
        self._tab_tip.update_idletasks();w=self._tab_tip.winfo_width();h=self._tab_tip.winfo_height()
        sw=self._tab_tip.winfo_screenwidth();sh=self._tab_tip.winfo_screenheight();x=min(x+8,sw-w-5);y=min(y+18,sh-h-5)
        self._tab_tip.geometry(f'+{max(5,x)}+{max(5,y)}')

    def _tooltip_tab_leave(self, _=None):
        if self._tab_after:
            try:self.after_cancel(self._tab_after)
            except Exception:pass
            self._tab_after=None
        self._hide_tab_tip()

    def _hide_tab_tip(self):
        if getattr(self,'_tab_tip',None):
            try:self._tab_tip.destroy()
            except Exception:pass
            self._tab_tip=None

    def make_tables(self):
        self.make_generic("AUTO START",("WHEN","SOURCE","NAME","PATH / COMMAND","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT","STATUS"),(100,120,180,330,170,100,100,100,260,260,90))
        self.make_generic("STARTUP APPS",("STATUS","NAME","LOCATION","COMMAND / PATH","USER","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT"),(95,190,300,430,150,180,100,100,100,250,250,230))
        self.make_generic("SERVICES",("START","SERVICE","DISPLAY","STATE","PATH","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT"),(80,150,210,85,320,170,100,100,100,240,260))
        self.make_generic("TASK SCHEDULER",("TRIGGER","TASK","PATH","ACTION","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT","STATE"),(110,190,180,320,180,100,100,100,250,170,230,90))
        self.make_generic("PROCESSES",("PID","PROCESS","PATH","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT","STATUS"),(70,180,360,180,100,100,100,250,170,240,90))
        self.make_generic("REGISTRY RUN",("HIVE","VALUE","COMMAND","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT"),(90,180,380,180,100,100,100,250,170,230))
        self.make_generic("STARTUP FOLDERS",("SCOPE","NAME","PATH","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT"),(120,190,380,180,100,100,100,250,170,230))
        self.make_generic("WINLOGON",("LOCATION","VALUE","COMMAND","COMPANY","TYPE","SIGNATURE","RISK","WHY","RECOMMENDATION","IMPACT"),(100,180,380,180,100,100,100,250,170,230))
        self.make_generic("STARTUP ISSUES",("LAUNCH SOURCE","EXACT ENTRY","NAME","TARGET / COMMAND","ISSUE","MISSING PATH","RISK","RECOMMENDATION"),(150,300,190,420,220,380,100,340))
        self.make_generic("BOOT CAPTURE",("TIME","PID","PROCESS","PATH","PUBLISHER","SOURCE","STATUS"),(100,80,190,420,180,180,140))
        self.make_generic("LAUNCH SOURCES",("SOURCE TYPE","LOCATION / NAME","COMMAND","TARGET","STATUS","DETAILS"),(170,420,500,500,150,650))
        self.make_generic("EVENT LOGS",("TIME","LOG","EVENT ID","LEVEL","PROVIDER","MESSAGE","PROCESS / TASK","MATCH"),(150,180,90,100,220,650,320,180))

    def make_generic(self,name,cols,widths):
        fr=tk.Frame(self.tabs[name],bg=BG);fr.pack(fill="both",expand=True,padx=4,pady=4)
        if name=="EVENT LOGS":
            ef=tk.Frame(fr,bg=BG)
            ef.pack(fill="x",pady=(0,4))
            tk.Label(ef,text="EVENT LOG FILTER",bg=BG,fg=GREEN,font=("Consolas",9,"bold")).pack(side="left",padx=(2,6))
            self.event_level_filter=tk.StringVar(value="ALL")
            self.event_log_filter=tk.StringVar(value="ALL")
            self.event_provider_filter=tk.StringVar(value="")
            self.event_id_filter=tk.StringVar(value="")
            self.event_text_filter=tk.StringVar(value="")

            def _event_apply(*_):
                self.populate()

            lm=tk.OptionMenu(ef,self.event_level_filter,"ALL","Information","Warning","Error","Critical",command=lambda *_:_event_apply())
            lm.config(bg="#081408",fg=GREEN,activebackground=GREEN,activeforeground="black",highlightthickness=0,font=("Consolas",9))
            lm["menu"].config(bg="#081408",fg=GREEN,font=("Consolas",9))
            lm.pack(side="left",padx=2)

            logm=tk.OptionMenu(ef,self.event_log_filter,"ALL","System","Application","Security","Setup",command=lambda *_:_event_apply())
            logm.config(bg="#081408",fg=GREEN,activebackground=GREEN,activeforeground="black",highlightthickness=0,font=("Consolas",9))
            logm["menu"].config(bg="#081408",fg=GREEN,font=("Consolas",9))
            logm.pack(side="left",padx=2)

            for var,label,width in ((self.event_provider_filter,"Provider",16),(self.event_id_filter,"Event ID",9),(self.event_text_filter,"Search",24)):
                e=tk.Entry(ef,textvariable=var,width=width,bg="black",fg=GREEN,insertbackground=GREEN,relief="solid",bd=1,font=("Consolas",9))
                e.pack(side="left",padx=2)
                e.insert(0,label)
                e.bind("<FocusIn>",lambda ev,w=e,l=label: w.delete(0,"end") if w.get()==l else None)
                e.bind("<Return>",lambda *_:_event_apply())

            tk.Button(ef,text="FILTER",command=_event_apply,bg="#081408",fg=GREEN,activebackground=GREEN,activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=3)
            tk.Button(ef,text="CLEAR",command=lambda:(self.event_level_filter.set("ALL"),self.event_log_filter.set("ALL"),self.event_provider_filter.set(""),self.event_id_filter.set(""),self.event_text_filter.set(""),self.populate()),bg="#081408",fg=GREEN,activebackground=GREEN,activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=2)
        tr=ttk.Treeview(fr,columns=cols,show="headings");self.tabs[name].tree=tr
        for c,w in zip(cols,widths):tr.heading(c,text=c);tr.column(c,width=w,anchor="w")
        tr.tag_configure("low", foreground="#39ff14")
        tr.tag_configure("medium", foreground="#ffd54a")
        tr.tag_configure("high", foreground="#ff8a00")
        tr.tag_configure("veryhigh", foreground="#ff3b30")
        tr.tag_configure("system", foreground="#54d6ff")
        tr.pack(fill="both",expand=True)
        # Horizontal scrolling keeps full paths/commands accessible on smaller screens.
        hx=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview);hx.pack(fill="x")
        tr.configure(xscrollcommand=hx.set)
        tr.bind("<<TreeviewSelect>>",lambda e:self.update_details())
        tr.bind("<Double-1>",lambda e:self.details())

    def refresh_all(self):
        """Force a fresh Windows-state scan and rebuild every visible table."""
        try:
            self.status("REFRESHING // RECHECKING WINDOWS STATE")
        except Exception:
            pass
        # Clear cached launch-source diagnostics so removed items disappear immediately.
        self.launch_sources=[]
        self.event_logs=[]
        try:
            for tab in self.tabs.values():
                tr=tab.tree
                for iid in tr.get_children():
                    tr.delete(iid)
        except Exception:
            pass
        threading.Thread(target=self.scan, daemon=True).start()

    def scan(self):
        if self.scanning:return
        self.scanning=True;self.state.config(text="● FAST SCAN...",fg=AMBER);self.progress.start(8); self.live_status.config(text="● SCANNING...",fg="#ffd54a")
        threading.Thread(target=self.worker,daemon=True).start()

    def worker(self):
        try:
            startup=self.registry()+self.folders()
            startup_apps,new_startup_apps=self.task_manager_startup_apps(startup)
            startup += new_startup_apps
            tasks=self.login_tasks()
            services=self.auto_services()
            procs=self.process_list()
            winlogon=self.winlogon_data()
            allx=startup+tasks+services+procs+winlogon

            # Fast local risk score first.
            for x in allx:
                x["risk"],x["risk_label"],x["risk_reason"],x["risk_score"]=fast_risk(x)

            # Resolve Company + Type + Authenticode in one batched PowerShell call.
            paths=[];seen=set()
            for x in allx:
                p=os.path.expandvars(x.get("exe") or exe_from(x.get("target","")))
                if p:
                    k=os.path.normcase(p)
                    if k not in seen:
                        seen.add(k);paths.append(p)

            intel={}
            if paths:
                payload=json.dumps(paths)
                script = "$paths = '" + payload.replace("'", "''") + "' | ConvertFrom-Json; "
                script += "$out = foreach($p in $paths){ "
                script += "$company='Unknown'; $sig='Unknown'; "
                script += "try { if(Test-Path -LiteralPath $p){ "
                script += "$item=Get-Item -LiteralPath $p -ErrorAction Stop; "
                script += "if($item.VersionInfo.CompanyName){$company=$item.VersionInfo.CompanyName}; "
                script += "$sig=(Get-AuthenticodeSignature -LiteralPath $p -ErrorAction SilentlyContinue).Status "
                script += "} else {$sig='Missing'} } catch {}; "
                script += "[PSCustomObject]@{Path=$p;Company=$company;Signature=$sig} }; "
                script += "$out | ConvertTo-Json -Compress"
                r=ps(script,30)
                if r and r.stdout.strip():
                    try:
                        rows=json.loads(r.stdout)
                        if isinstance(rows,dict): rows=[rows]
                        for z in rows:
                            intel[os.path.normcase(str(z.get("Path","")))] = (
                                str(z.get("Company","Unknown") or "Unknown"),
                                str(z.get("Signature","Unknown") or "Unknown")
                            )
                    except Exception:
                        pass

            for x in allx:
                p=os.path.expandvars(x.get("exe") or exe_from(x.get("target","")))
                c,sig=intel.get(os.path.normcase(p),("Unknown","Unknown"))
                if not c or c=="Unknown":
                    np=os.path.normcase(p);w=os.path.normcase(os.environ.get("WINDIR",r"C:\Windows"))
                    if np.startswith(w+os.sep): c="Microsoft Corporation"
                x["company"]=c
                x["signature"]=sig
                x["type"]="MICROSOFT" if "microsoft" in c.lower() else ("3RD PARTY" if c!="Unknown" else "UNKNOWN")

            current_all=startup+tasks+services+procs+winlogon
            self.changes=self.compare_baseline(current_all)
            self.q.put(("done",startup,startup_apps,tasks,services,procs,winlogon))
        except Exception as e:
            self.q.put(("error",f"{type(e).__name__}: {e}"))

    def poll(self):
        try:
            m=self.q.get_nowait()
            if m[0]=="error":
                self.scanning=False;self.progress.stop(); self.live_status.config(text="● SCAN COMPLETE",fg=GREEN);self.state.config(text="● SCAN ERROR",fg=RED);messagebox.showerror(APP,m[1])
            else:
                _,self.startup,self.startup_apps,self.tasks,self.services,self.processes,self.winlogon=m
                self.scanning=False;self.progress.stop(); self.live_status.config(text="● SCAN COMPLETE",fg=GREEN);self.state.config(text="● FAST SCAN COMPLETE",fg=GREEN)
                allx=self.startup+self.tasks+self.services+self.processes+self.winlogon
                high=sum(1 for x in allx if x["risk_score"]>=4)
                self.cards[0].config(text=len(self.startup));self.cards[1].config(text=len(self.tasks));self.cards[2].config(text=len(self.services));self.cards[3].config(text=len(self.processes));self.cards[4].config(text=high)
                self.cards[5].config(text=sum(1 for v in self.changes.values() if v!="UNCHANGED"))
                self.cards[6].config(text=sum(1 for x in allx if str(x.get("type","")).upper()=="3RD PARTY"))
                self.scan_startup_issues()
                self.populate()
        except queue.Empty:pass
        self.after(100,self.poll)

    def registry(self):
        out=[];specs=[(winreg.HKEY_CURRENT_USER,"HKCU",r"Software\Microsoft\Windows\CurrentVersion\Run","User Login"),(winreg.HKEY_CURRENT_USER,"HKCU",r"Software\Microsoft\Windows\CurrentVersion\RunOnce","User Login Once"),(winreg.HKEY_LOCAL_MACHINE,"HKLM",r"Software\Microsoft\Windows\CurrentVersion\Run","All Users Login"),(winreg.HKEY_LOCAL_MACHINE,"HKLM",r"Software\Microsoft\Windows\CurrentVersion\RunOnce","All Users Login Once")]
        for root,hive,key,when in specs:
            try:
                with winreg.OpenKey(root,key,0,winreg.KEY_READ) as k:
                    for i in range(winreg.QueryInfoKey(k)[1]):
                        try:
                            n,v,_=winreg.EnumValue(k,i);out.append(self.item(when,"Registry Run",n,str(v),hive=hive,key=key,root=root))
                        except:pass
            except:pass
        return out

    def folders(self):
        out=[]
        for label,folder,when in [("User Startup",os.path.join(os.environ.get("APPDATA",""),r"Microsoft\Windows\Start Menu\Programs\Startup"),"User Login"),("All Users Startup",os.path.join(os.environ.get("PROGRAMDATA",""),r"Microsoft\Windows\Start Menu\Programs\Startup"),"All Users Login")]:
            if os.path.isdir(folder):
                for n in os.listdir(folder):out.append(self.item(when,label,n,os.path.join(folder,n),scope=label))
        return out

    def _startup_approved_state(self, name, location="", root_hint=None):
        """Read Windows StartupApproved state used by Task Manager.
        02 = enabled, 03 = disabled. If no approval record exists, treat it as enabled.
        """
        candidates=[]
        loc=str(location or "").lower()
        if "startupfolder" in loc or "startup folder" in loc:
            candidates=[(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"),
                        (winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder")]
        elif "run32" in loc:
            candidates=[(winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"),
                        (winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run")]
        else:
            candidates=[(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
                        (winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
                        (winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32")]
        wanted=str(name or "").strip().lower()
        for root,key in candidates:
            try:
                with winreg.OpenKey(root,key,0,winreg.KEY_READ) as k:
                    for i in range(winreg.QueryInfoKey(k)[1]):
                        try:
                            n,v,_=winreg.EnumValue(k,i)
                            if str(n).strip().lower()==wanted and isinstance(v,(bytes,bytearray)) and len(v)>=4:
                                return "Disabled" if v[0]==3 else "Enabled"
                        except Exception:
                            pass
            except Exception:
                pass
        return "Enabled"

    def task_manager_startup_apps(self, existing):
        r"""Build a reliable Startup Apps inventory similar to Windows Task Manager.
        Uses Win32_StartupCommand plus the StartupApproved registry and direct Run/RunOnce
        enumeration. This fallback is important because some Windows builds expose fewer
        entries through Win32_StartupCommand than Task Manager does.
        """
        tm_all=[]
        by_key={}
        by_name={}

        def norm(v):
            return os.path.normcase(os.path.expandvars(str(v or '').strip()))

        def add_or_update(name, command='', location='', user='', hive='', approved_hive='', status=None, source='Task Manager Startup App', note=''):
            name=str(name or '').strip(); command=str(command or '').strip(); location=str(location or '').strip()
            if not name and not command: return None
            key=(name.lower(), norm(command))
            existing_item=by_key.get(key) or by_name.get(name.lower())
            if existing_item is None:
                # Reuse an existing Registry Run / Startup Folder object where possible.
                for x in existing:
                    xn=str(x.get('name','')).strip().lower(); xt=norm(x.get('target',''))
                    if xn==name.lower() and (not command or not xt or xt==norm(command)):
                        existing_item=x; break
                    if command and xt==norm(command):
                        existing_item=x; break
            if existing_item is None:
                existing_item=self.item('User Login',source,name,command,status=status or 'Enabled',
                                        task_manager=True,startup_source=location,startup_user=user)
                tm_all.append(existing_item)
            else:
                if existing_item not in tm_all: tm_all.append(existing_item)
                existing_item['task_manager']=True
                if command and not existing_item.get('target'): existing_item['target']=command
                existing_item['startup_source']=location or existing_item.get('startup_source','')
                existing_item['startup_user']=user or existing_item.get('startup_user','')
                if status: existing_item['status']=status
            if approved_hive: existing_item['startup_approved_hive']=approved_hive
            if status: existing_item['task_manager_status']=status
            if note: existing_item['note']=note
            by_key[(str(existing_item.get('name','')).strip().lower(),norm(existing_item.get('target','')))] = existing_item
            by_name[str(existing_item.get('name','')).strip().lower()] = existing_item
            return existing_item

        # Existing common startup entries are always represented in this tab.
        for x in existing:
            src=str(x.get('source','')).lower()
            if src in ('registry run','user startup','all users startup'):
                st=self._startup_approved_state(x.get('name',''),x.get('key',x.get('source','')),x.get('root'))
                x['task_manager']=True; x['task_manager_status']=st; x['status']=st
                x['startup_source']=x.get('key',x.get('source',''))
                if str(x.get('hive','')).upper() in ('HKCU','HKLM'): x['startup_approved_hive']=str(x.get('hive')).upper()
                tm_all.append(x)
                by_name[str(x.get('name','')).strip().lower()]=x
                by_key[(str(x.get('name','')).strip().lower(),norm(x.get('target','')))] = x

        # Primary source: Win32_StartupCommand.
        r=ps("Get-CimInstance Win32_StartupCommand | Select Name,Command,Location,User | ConvertTo-Csv -NoTypeInformation",20)
        if r and r.returncode==0 and r.stdout:
            try:
                rows=list(csv.reader(r.stdout.splitlines()))
                for row in rows[1:]:
                    if len(row)<4: continue
                    name,command,location,user=[str(v or '') for v in row[:4]]
                    if not name and not command: continue
                    st=self._startup_approved_state(name,location)
                    hive='HKLM' if ('HKLM' in location.upper() or 'HKEY_LOCAL_MACHINE' in location.upper()) else 'HKCU'
                    add_or_update(name,command,location,user,hive,hive,st)
            except Exception:
                pass

        # Direct registry fallback: enumerate Run/RunOnce and map StartupApproved state.
        specs=[
            (winreg.HKEY_CURRENT_USER,r'Software\\Microsoft\\Windows\\CurrentVersion\\Run','HKCU'),
            (winreg.HKEY_CURRENT_USER,r'Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce','HKCU'),
            (winreg.HKEY_LOCAL_MACHINE,r'Software\\Microsoft\\Windows\\CurrentVersion\\Run','HKLM'),
            (winreg.HKEY_LOCAL_MACHINE,r'Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce','HKLM'),
        ]
        for root,key,hive in specs:
            try:
                with winreg.OpenKey(root,key,0,winreg.KEY_READ) as k:
                    for i in range(winreg.QueryInfoKey(k)[1]):
                        try:
                            n,v,_=winreg.EnumValue(k,i)
                            st=self._startup_approved_state(n,key)
                            add_or_update(n,str(v),f'{hive}\\{key}',hive,hive,hive,st)
                        except Exception: pass
            except Exception: pass

        # Direct Startup-folder fallback.
        for hive,folder in [
            ('HKCU',os.path.join(os.environ.get('APPDATA',''),r'Microsoft\\Windows\\Start Menu\\Programs\\Startup')),
            ('HKLM',os.path.join(os.environ.get('PROGRAMDATA',''),r'Microsoft\\Windows\\Start Menu\\Programs\\Startup'))]:
            try:
                if os.path.isdir(folder):
                    for n in os.listdir(folder):
                        target=os.path.join(folder,n)
                        st=self._startup_approved_state(n,'StartupFolder')
                        add_or_update(n,target,'StartupFolder',hive,hive,hive,st)
            except Exception: pass

        # Also surface orphaned StartupApproved records so disabled Task Manager entries
        # remain visible even when Windows no longer exposes their original command.
        approved_specs=[
            (winreg.HKEY_CURRENT_USER,r'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run','HKCU'),
            (winreg.HKEY_LOCAL_MACHINE,r'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run','HKLM'),
            (winreg.HKEY_LOCAL_MACHINE,r'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run32','HKLM'),
            (winreg.HKEY_CURRENT_USER,r'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\StartupFolder','HKCU'),
            (winreg.HKEY_LOCAL_MACHINE,r'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\StartupFolder','HKLM')]
        for root,key,hive in approved_specs:
            try:
                with winreg.OpenKey(root,key,0,winreg.KEY_READ) as k:
                    for i in range(winreg.QueryInfoKey(k)[1]):
                        try:
                            name,val,_=winreg.EnumValue(k,i)
                            if not name or not isinstance(val,(bytes,bytearray)) or len(val)<1: continue
                            st='Disabled' if val[0]==3 else 'Enabled'
                            if str(name).strip().lower() in by_name:
                                by_name[str(name).strip().lower()]['task_manager_status']=st
                                by_name[str(name).strip().lower()]['status']=st
                                continue
                            add_or_update(name,'',key,hive,hive,hive,st,
                                          note='StartupApproved entry; original command/path may be unavailable.')
                        except Exception: pass
            except Exception: pass

        # Deduplicate while preserving order.
        unique=[]; seen_ids=set()
        for x in tm_all:
            ident=id(x)
            if ident in seen_ids: continue
            seen_ids.add(ident)
            x['task_manager']=True
            x['task_manager_status']=x.get('task_manager_status',x.get('status','Enabled'))
            x['status']=x['task_manager_status']
            unique.append(x)
        # Return no extra startup rows; the main startup list already contains Registry/Folder entries.
        return unique, []

    def login_tasks(self):
        r=ps("""Get-ScheduledTask | ForEach-Object {$t=$_;$types=($t.Triggers|ForEach-Object{$_.TriggerType})-join ',';if($types-match 'Logon|Boot|Startup'){$a=($t.Actions|ForEach-Object{($_.Execute+' '+$_.Arguments).Trim()})-join ' | ';[PSCustomObject]@{Name=$t.TaskName;Path=$t.TaskPath;Trigger=$types;State=$t.State;Action=$a}}} | ConvertTo-Csv -NoTypeInformation""",15);out=[]
        if not r:return out
        rows=list(csv.reader(r.stdout.splitlines()))
        if rows:
            for row in rows[1:]:
                d=dict(zip(rows[0],row))
                out.append(self.item(d.get("Trigger",""),"Task Scheduler",d.get("Name",""),d.get("Action",""),taskpath=d.get("Path",""),status=d.get("State","")))
        return out

    def auto_services(self):
        r=ps("""Get-CimInstance Win32_Service | Where-Object {$_.StartMode -in @('Auto','Boot','System')} | Select Name,DisplayName,State,StartMode,PathName | ConvertTo-Csv -NoTypeInformation""",15);out=[]
        if not r:return out
        rows=list(csv.reader(r.stdout.splitlines()))
        for row in rows[1:]:
            if len(row)>=5:
                out.append(self.item(row[3],"Windows Service",row[0],row[4],display=row[1],state=row[2],service=True))
        return out

    def process_list(self):
        r=ps("""Get-Process | ForEach-Object {$p=$_;$path='';try{$path=$p.Path}catch{};[PSCustomObject]@{PID=$p.Id;Name=$p.ProcessName;Path=$path}} | ConvertTo-Csv -NoTypeInformation""",15);out=[]
        if not r:return out
        rows=list(csv.reader(r.stdout.splitlines()))
        for row in rows[1:]:
            if len(row)>=3:
                out.append(self.item("Running","Process",row[1],row[2],pid=row[0],status="Running"))
        return out

    def winlogon_data(self):
        out=[]
        specs=[("HKLM",winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon"),("HKCU",winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon")]
        for hive,root,key in specs:
            try:
                with winreg.OpenKey(root,key,0,winreg.KEY_READ) as k:
                    for i in range(winreg.QueryInfoKey(k)[1]):
                        try:
                            n,v,_=winreg.EnumValue(k,i)
                            if n in ("Shell","Userinit","AppSetup","Notify","GinaDLL"):out.append(self.item("Logon","Winlogon",n,str(v),hive=hive,key=key,root=root))
                        except:pass
            except:pass
        return out

    def item(self,when,source,name,target,**kw):
        d=dict(when=when,source=source,name=name,target=target,exe=exe_from(target),company="Not checked",type="UNKNOWN",signature="Unknown",risk="LOW",risk_label="LOW",risk_reason="",risk_score=0,status=kw.get("status","Enabled"));d.update(kw);return d

    def active(self):
        tab=self.nb.tab(self.nb.select(),"text").strip();q=self.search.get().lower()
        pools={"AUTO START":self.startup+self.tasks,"STARTUP APPS":self.startup_apps,"SERVICES":self.services,"TASK SCHEDULER":self.tasks,"PROCESSES":self.processes,"REGISTRY RUN":[x for x in self.startup if x["source"]=="Registry Run"],"STARTUP FOLDERS":[x for x in self.startup if x["source"] in ("User Startup","All Users Startup")],"WINLOGON":self.winlogon}
        if tab=="STARTUP ISSUES":
            data=self.startup_issues
        elif tab=="BOOT CAPTURE":
            data=self.boot_events
        elif tab=="EVENT LOGS":
            data=self.event_logs
        elif tab=="LAUNCH SOURCES":
            data=self.launch_sources
        else:
            data=[x for x in pools.get(tab,[]) if not q or q in json.dumps(x,default=str).lower()]
        if getattr(self,"risk_filter",""):
            rf=self.risk_filter
            data=[x for x in data if rf in str(x.get("risk_label",x.get("risk",""))).upper()]
        if getattr(self,"company_filter",""):
            cf=self.company_filter
            data=[x for x in data if str(x.get("type","Unknown")).strip().upper()==cf]
        if getattr(self,"signature_filter",""):
            sf=self.signature_filter
            def sig_bucket(v):
                z=str(v if v is not None else "UNKNOWN").strip().upper()
                if z in ("VALID","VALIDATED","TRUSTED"): return "VALID"
                if z in ("NOTSIGNED","NOT SIGNED","NOT_SIGNED","UNSIGNED","2"): return "NOTSIGNED"
                if z in ("INVALID","HASHMISMATCH","NOTTRUSTED","UNKNOWNERROR","ERROR"): return "INVALID"
                return "UNKNOWN"
            data=[x for x in data if sig_bucket(x.get("signature","Unknown"))==sf]
        return data,self.tabs[tab].tree

    def load_boot_log(self):
        self.boot_events=[]
        try:
            if os.path.isfile(self.boot_log_file):
                with open(self.boot_log_file,"r",encoding="utf-8",errors="ignore") as f:
                    for line in f:
                        try:
                            x=json.loads(line)
                            if isinstance(x,dict): self.boot_events.append(x)
                        except Exception:
                            pass
        except Exception:
            pass

    def on_tab_changed(self, event=None):
        self.populate()
        try:
            tab=self.current_tab()
            if tab=="LAUNCH SOURCES" and not self.launch_sources:
                threading.Thread(target=self.scan_launch_sources,daemon=True).start()
            elif tab=="EVENT LOGS" and not self.event_logs:
                try: self.live_status.config(text="● EVENT LOGS LOADING // LAST 7 DAYS...", fg=AMBER)
                except Exception: pass
                threading.Thread(target=self.scan_event_logs,args=(168,),daemon=True).start()
        except Exception:
            pass

    def scan_launch_sources(self):
        rows=[]
        keys=("ultron_native","native_ultron","zyntrasec","python.exe")
        def add(kind,loc,cmd="",target="",status="",details=""):
            blob=" ".join(map(str,(loc,cmd,target,details))).lower()
            if any(k in blob for k in keys):
                rows.append({"source_type":kind,"location":loc,"command":cmd,"target":target,
                             "status":status or ("MISSING TARGET" if target and not os.path.exists(target) else "FOUND"),
                             "details":details})
        reg_keys=[
            (winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\RunOnce")]
        for hive,path in reg_keys:
            try:
                k=winreg.OpenKey(hive,path)
                for i in range(winreg.QueryInfoKey(k)[1]):
                    n,v,_=winreg.EnumValue(k,i); cmd=str(v)
                    m=re.search(r'(?i)([A-Z]:\\[^"\\r\\n]*?(?:\.py|\.exe|\.bat|\.cmd|\.ps1))',cmd)
                    target=m.group(1) if m else ""
                    add("REGISTRY",f"{path}\\{n}",cmd,target,"MISSING TARGET" if target and not os.path.exists(target) else "FOUND","Run/RunOnce")
                winreg.CloseKey(k)
            except Exception: pass

        task_ps='Get-ScheduledTask | ForEach-Object {$t=$_; foreach($a in $t.Actions){[pscustomobject]@{TaskName=$t.TaskName;TaskPath=$t.TaskPath;Execute=[string]$a.Execute;Arguments=[string]$a.Arguments}}} | ConvertTo-Json -Compress'
        try:
            raw=_zyntrasec_check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",task_ps],text=True,stderr=subprocess.DEVNULL,timeout=45).strip()
            if raw:
                obj=json.loads(raw); obj=[obj] if isinstance(obj,dict) else obj
                for x in obj:
                    cmd=(str(x.get("Execute",""))+" "+str(x.get("Arguments",""))).strip()
                    add("SCHEDULED TASK",str(x.get("TaskPath",""))+str(x.get("TaskName","")),cmd,str(x.get("Execute","")),"COMMAND","Task Scheduler action")
        except Exception: pass

        svc_ps='Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode,PathName | ConvertTo-Json -Compress'
        try:
            raw=_zyntrasec_check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",svc_ps],text=True,stderr=subprocess.DEVNULL,timeout=45).strip()
            if raw:
                obj=json.loads(raw); obj=[obj] if isinstance(obj,dict) else obj
                for x in obj:
                    rows.append({"source_type":"SERVICES","location":f'{x.get("Name","")} | {x.get("DisplayName","")}',
                                 "command":str(x.get("PathName","")),"target":"","status":"COMMAND",
                                 "details":f"State={x.get('State','')}; StartMode={x.get('StartMode','')}",
                                 "source":"SERVICE","name":str(x.get("Name","")),"display_name":str(x.get("DisplayName","")),
                                 "path":str(x.get("PathName",""))}) if any(k in str(x.get("Name","")).lower()+" "+str(x.get("DisplayName","")).lower()+" "+str(x.get("PathName","")).lower() for k in keys) else None
        except Exception: pass

        dirs=[os.path.join(os.environ.get("APPDATA",""),r"Microsoft\Windows\Start Menu\Programs\Startup"),
              os.path.join(os.environ.get("ProgramData",r"C:\ProgramData"),r"Microsoft\Windows\Start Menu\Programs\Startup")]
        for d in dirs:
            if os.path.isdir(d):
                for root,_,files in os.walk(d):
                    for fn in files:
                        p=os.path.join(root,fn)
                        if fn.lower().endswith(".lnk"):
                            try:
                                q="$s=(New-Object -ComObject WScript.Shell).CreateShortcut(%s); [pscustomobject]@{Target=$s.TargetPath;Arguments=$s.Arguments} | ConvertTo-Json -Compress" % json.dumps(p)
                                raw=_zyntrasec_check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",q],text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
                                z=json.loads(raw) if raw else {}; target=str(z.get("Target","")); cmd=(target+" "+str(z.get("Arguments",""))).strip()
                                add("STARTUP SHORTCUT",p,cmd,target,"FOUND" if target and os.path.exists(target) else "MISSING TARGET","Startup .lnk")
                            except Exception: pass
                        else: add("STARTUP FILE",p,p,p,"FOUND","Startup folder")

        try:
            k=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon")
            for n in ("Shell","Userinit"):
                try:
                    v,_=winreg.QueryValueEx(k,n); add("WINLOGON",f"HKLM\\...\\Winlogon\\{n}",str(v),"","CONFIGURED","Winlogon")
                except Exception: pass
            winreg.CloseKey(k)
        except Exception: pass

        self.launch_sources=rows
        try:
            os.makedirs("backup",exist_ok=True)
            with open(os.path.join("backup","launch_sources.json"),"w",encoding="utf-8") as f: json.dump(rows,f,ensure_ascii=False,indent=2)
        except Exception: pass
        self.populate()

    def scan_event_logs(self, hours=168):
        events=[]
        ps = '$start=(Get-Date).AddHours(-168)\n$logs=@("Security","System","Microsoft-Windows-TaskScheduler/Operational","Application")\n$terms=@("python.exe","python ","ultron_native","zyntrasec","startup","command line","new process","service","task","failed","terminated","crash","error")\n$out=@()\nforeach($log in $logs){\n try {\n  Get-WinEvent -FilterHashtable @{LogName=$log; StartTime=$start} -MaxEvents 2500 -ErrorAction Stop |\n   ForEach-Object {\n    $m=[string]$_.Message\n    $low=$m.ToLowerInvariant()\n    $hit=$false\n    foreach($t in $terms){if($low.Contains($t)){$hit=$true;break}}\n    if($hit -or $_.Id -in @(4688,7036,7045,106,140,141,142,6005,6006,6008,41)){\n      $out += [pscustomobject]@{Time=$_.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss");Log=$_.LogName;Id=$_.Id;Level=$_.LevelDisplayName;Provider=$_.ProviderName;Message=$m}\n    }\n   }\n } catch {\n  $out += [pscustomobject]@{Time=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss");Log=$log;Id=-1;Level="ACCESS/ERROR";Provider="ZYNTRASEC";Message=$_.Exception.Message}\n }\n}\n$out | ConvertTo-Json -Compress -Depth 5'
        try:
            raw=_zyntrasec_check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",ps],
                                        text=True,stderr=subprocess.DEVNULL,timeout=120).strip()
            if raw:
                obj=json.loads(raw)
                if isinstance(obj,dict): obj=[obj]
                for e in obj:
                    msg=str(e.get("Message","")).replace("\r"," ").replace("\n"," ")
                    low=msg.lower()
                    matches=[t for t in ("python.exe","python ","ultron_native","zyntrasec","startup","command line") if t in low]
                    proc=""
                    for pat in (r"New Process Name:\s*(.+)",r"Creator Process Name:\s*(.+)",r"Command Line:\s*(.+)"):
                        m=re.search(pat,msg,re.I)
                        if m:
                            proc=m.group(1).strip()
                            break
                    events.append({"time":e.get("Time",""),"log":e.get("Log",""),"event_id":str(e.get("Id","")),
                                   "level":e.get("Level",""),"provider":e.get("Provider",""),
                                   "message":msg,"process_task":proc,"match":", ".join(matches)})
            else:
                events.append({"time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               "log":"ZYNTRASEC","event_id":"NO DATA","level":"INFO",
                               "provider":"Event Viewer","message":"No matching events were returned by Windows Event Viewer.",
                               "process_task":"","match":""})
        except Exception as ex:
            events.append({"time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           "log":"ZYNTRASEC","event_id":"SCAN ERROR","level":"ERROR",
                           "provider":"Event Viewer","message":str(ex),"process_task":"","match":"SCAN ERROR"})
        self.event_logs=events
        try:
            self.after(0, self.populate)
            self.after(0, lambda: self.live_status.config(text=f"● EVENT LOGS READY // {len(events)} EVENTS", fg=GREEN))
        except Exception:
            pass

    def enable_process_creation_audit(self):
        try:
            _zyntrasec_run(["auditpol","/set","/subcategory:Process Creation","/success:enable","/failure:enable"],
                           check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            messagebox.showinfo(APP,"Process Creation auditing enabled. Future process starts can appear as Security Event ID 4688.")
        except Exception as e:
            messagebox.showerror(APP,"Could not enable Process Creation auditing:\n"+str(e))

    def scan_all_windows_startup_forensics(self):
        self.scan_startup_issues()
        self.scan_event_logs(24)

    def get_process_snapshot(self):
        rows=[]
        try:
            cmd='Get-CimInstance Win32_Process | Select-Object ProcessId,Name,ExecutablePath | ConvertTo-Json -Compress'
            raw=_zyntrasec_check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",cmd],text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
            if not raw: return rows
            obj=json.loads(raw)
            if isinstance(obj,dict): obj=[obj]
            for p in obj:
                rows.append({"pid":p.get("ProcessId",""),"name":p.get("Name",""),"path":p.get("ExecutablePath") or ""})
        except Exception: pass
        return rows

    def capture_boot_processes(self, seconds=30):
        import time
        os.makedirs(os.path.dirname(self.boot_log_file),exist_ok=True)
        seen=set()
        end=time.time()+seconds
        with open(self.boot_log_file,"a",encoding="utf-8") as log:
            while time.time()<end:
                for x in self.get_process_snapshot():
                    key=(str(x.get("pid","")),str(x.get("path","")))
                    if key not in seen:
                        seen.add(key)
                        event={"time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                               "pid":x.get("pid",""),"name":x.get("name",""),"path":x.get("path",""),
                               "publisher":"Unknown","source":"BOOT PROCESS CAPTURE","status":"OBSERVED"}
                        self.boot_events.append(event)
                        log.write(json.dumps(event,ensure_ascii=False)+"\n")
                        log.flush()
                try: self.populate()
                except Exception: pass
                time.sleep(0.20)

    def run_full_startup_audit(self):
        self.scan_startup_issues()
        self.boot_events=[]
        self.populate()
        threading.Thread(target=self.capture_boot_processes,args=(self.capture_seconds,),daemon=True).start()

    def install_boot_capture(self):
        try:
            startup_dir=os.path.join(os.environ.get("APPDATA",""),r"Microsoft\Windows\Start Menu\Programs\Startup")
            os.makedirs(startup_dir,exist_ok=True)
            bat=os.path.abspath("RUN_ZYNTRASEC_V43.bat")
            lnk=os.path.join(startup_dir,"ZYNTRASEC V43 Boot Capture.lnk")
            ps="$ws=New-Object -ComObject WScript.Shell; $sc=$ws.CreateShortcut('" + lnk.replace("'","''") + "'); $sc.TargetPath='" + bat.replace("'","''") + "'; $sc.WorkingDirectory='" + os.path.dirname(bat).replace("'","''") + "'; $sc.WindowStyle=7; $sc.Save()"
            _zyntrasec_run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",ps],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            messagebox.showinfo(APP,"Boot Capture installed. It will start at your Windows logon.")
        except Exception as e:
            messagebox.showerror(APP,"Could not install Boot Capture:\n"+str(e))

    def scan_startup_issues(self):
        issues=[]

        def add_issue(source, exact, name, target, issue, missing):
            issues.append({
                "source":source,
                "exact_source":exact,
                "name":name,
                "target":target,
                "issue":issue,
                "expected_path":missing,
                "risk_label":"HIGH",
                "risk":"HIGH",
                "recommendation":"Review the startup entry before removing or disabling it."
            })

        def check_target(source, exact, name, target):
            target=str(target or "")
            # Extract common executable/script paths.
            pats=[
                r'"([A-Za-z]:\\[^"]+?\.(?:exe|cmd|bat|ps1|py|vbs|js|dll))"',
                r'([A-Za-z]:\\[^\s,;"]+?\.(?:exe|cmd|bat|ps1|py|vbs|js|dll))'
            ]
            paths=[]
            for pat in pats:
                paths += re.findall(pat,target,re.I)
            paths=list(dict.fromkeys(paths))

            # Explicit Python command handling.
            mt=re.search(r'(?:^|\s)python(?:\.exe)?\s+(?:"([^"]+)"|([A-Za-z]:\\\S+))',target,re.I)
            if mt:
                script=os.path.expandvars((mt.group(1) or mt.group(2)).rstrip('"'))
                if not os.path.exists(script):
                    add_issue(source,exact,name,target,"PYTHON SCRIPT MISSING",script)
                    return

            for pth in paths:
                pth=os.path.expandvars(pth)
                if not os.path.exists(pth):
                    add_issue(source,exact,name,target,"MISSING TARGET / BROKEN STARTUP REFERENCE",pth)
                    return

        # Registry Run / RunOnce — exact registry key + value name.
        try:
            specs=[
                (winreg.HKEY_CURRENT_USER,"HKCU",r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER,"HKCU",r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE,"HKLM",r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE,"HKLM",r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
            ]
            for root,hive,key in specs:
                try:
                    with winreg.OpenKey(root,key) as k:
                        for i in range(winreg.QueryInfoKey(k)[1]):
                            name,val,_=winreg.EnumValue(k,i)
                            exact=f"{hive}\\{key}\\{name}"
                            check_target("Registry Run / RunOnce",exact,name,str(val))
                except Exception:
                    pass
        except Exception:
            pass

        # Existing scanned startup/task/service/winlogon records.
        pools=[
            ("AUTO START",self.startup+self.tasks),
            ("SERVICES",self.services),
            ("TASK SCHEDULER",self.tasks),
            ("WINLOGON",self.winlogon)
        ]
        for source,data in pools:
            for x in data:
                name=x.get("name") or x.get("service") or x.get("task") or x.get("display") or x.get("value") or "Unknown"
                target=x.get("target") or x.get("path") or x.get("command") or x.get("action") or x.get("exe") or ""
                exact=x.get("key") or x.get("task_path") or x.get("service_name") or x.get("source") or source
                check_target(source,str(exact),str(name),str(target))

        # Actual Startup folders and .LNK targets.
        startup_dirs=[
            os.path.join(os.environ.get("APPDATA",""),r"Microsoft\Windows\Start Menu\Programs\Startup"),
            os.path.join(os.environ.get("PROGRAMDATA",""),r"Microsoft\Windows\Start Menu\Programs\StartUp")
        ]
        for folder in startup_dirs:
            if not os.path.isdir(folder):
                continue
            for fn in os.listdir(folder):
                full=os.path.join(folder,fn)
                if fn.lower().endswith(".lnk"):
                    try:
                        ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('" + full.replace("'","''") + "'); [pscustomobject]@{Target=$s.TargetPath;Args=$s.Arguments} | ConvertTo-Json -Compress"
                        raw=_zyntrasec_check_output(["powershell","-NoProfile","-Command",ps],text=True,stderr=subprocess.DEVNULL,timeout=4)
                        obj=json.loads(raw)
                        target=str(obj.get("Target","") or "")
                        args=str(obj.get("Args","") or "")
                        command=(target+" "+args).strip()
                        if target and not os.path.exists(os.path.expandvars(target)):
                            add_issue("Startup Shortcut",full,fn,command,"SHORTCUT TARGET MISSING",target)
                        else:
                            check_target("Startup Shortcut",full,fn,command)
                    except Exception:
                        pass
                else:
                    check_target("Startup Folder",full,fn,full)

        # Deduplicate while preserving exact source.
        seen=set()
        self.startup_issues=[]
        for x in issues:
            k=(x["source"],x["exact_source"],x["name"],x["expected_path"],x["issue"])
            if k not in seen:
                seen.add(k)
                self.startup_issues.append(x)

    def populate_startup_issues(self):
        tr=self.tabs["STARTUP ISSUES"].tree
        for i in tr.get_children(): tr.delete(i)
        for i,x in enumerate(self.startup_issues):
            tr.insert("", "end", iid=str(i),
                      values=(x.get("source",""),x.get("exact_source",""),x.get("name",""),
                              x.get("target",""),x.get("issue",""),x.get("expected_path",""),
                              x.get("risk_label","HIGH"),x.get("recommendation","")),
                      tags=("high",))

    def populate(self):
        tab_now=self.nb.tab(self.nb.select(),"text").strip()
        if tab_now=="BOOT CAPTURE":
            tr=self.tabs["BOOT CAPTURE"].tree
            for i in tr.get_children(): tr.delete(i)
            for i,x in enumerate(self.boot_events):
                tr.insert("", "end", iid=str(i), values=(x.get("time",""),x.get("pid",""),x.get("name",""),x.get("path",""),x.get("publisher","Unknown"),x.get("source",""),x.get("status","")), tags=("low",))
            self.current=self.boot_events
            self.update_filter_banner()
            return
        if tab_now=="LAUNCH SOURCES":
            tr=self.tabs["LAUNCH SOURCES"].tree
            for i in tr.get_children(): tr.delete(i)
            for i,x in enumerate(self.launch_sources):
                tr.insert("", "end", iid=str(i), values=(x.get("source_type",""),x.get("location",""),x.get("command",""),x.get("target",""),x.get("status",""),x.get("details","")))
            self.current=self.launch_sources
            self.update_filter_banner()
            return
        if tab_now=="EVENT LOGS":
            tr=self.tabs["EVENT LOGS"].tree
            for i in tr.get_children(): tr.delete(i)
            data=list(self.event_logs)
            level=str(getattr(self,"event_level_filter",tk.StringVar(value="ALL")).get()).lower()
            log_name=str(getattr(self,"event_log_filter",tk.StringVar(value="ALL")).get()).lower()
            provider=str(getattr(self,"event_provider_filter",tk.StringVar(value="")).get()).lower()
            event_id=str(getattr(self,"event_id_filter",tk.StringVar(value="")).get()).lower()
            query=str(getattr(self,"event_text_filter",tk.StringVar(value="")).get()).lower()
            data=[x for x in data
                  if level in ("","all") or level==str(x.get("level","")).lower()]
            data=[x for x in data
                  if log_name in ("","all") or log_name==str(x.get("log","")).lower()]
            if provider not in ("","provider"):
                data=[x for x in data if provider in str(x.get("provider","")).lower()]
            if event_id not in ("","event id"):
                data=[x for x in data if event_id in str(x.get("event_id","")).lower()]
            if query not in ("","search"):
                data=[x for x in data if query in (" ".join(str(x.get(k,"")) for k in ("message","provider","process_task","match"))).lower()]
            for i,x in enumerate(data):
                tr.insert("", "end", iid=str(i),
                          values=(x.get("time",""),x.get("log",""),x.get("event_id",""),
                                  x.get("level",""),x.get("provider",""),x.get("message",""),
                                  x.get("process_task",""),x.get("match","")),
                          tags=("high" if str(x.get("level","")).upper() in ("ERROR","CRITICAL","WARNING") else "low",))
            self.current=data
            self.update_filter_banner()
            return
        if tab_now=="STARTUP ISSUES":
            self.populate_startup_issues()
            self.current=self.startup_issues
            self.update_filter_banner()
            return
        data,tr=self.active();self.current=data
        for i in tr.get_children():tr.delete(i)
        tab=self.nb.tab(self.nb.select(),"text").strip()
        for i,x in enumerate(data):
            rec,cat,impact=recommendation(x)
            if tab=="STARTUP APPS":vals=(x.get("task_manager_status",x.get("status","Enabled")),x.get("name",""),x.get("startup_source",x.get("key",x.get("source",""))),x.get("target",""),x.get("startup_user",x.get("when","")),x.get("company","Unknown"),x.get("type","Unknown"),x.get("signature","Unknown"),x.get("risk_label",x.get("risk","LOW")),x.get("risk_reason",""),rec,impact)
            elif tab=="PROCESSES":vals=(x.get("pid",""),x["name"],x["target"],x.get("company","Unknown"),x.get("type","Unknown"),x.get("signature","Unknown"),x["risk_label"],x["risk_reason"],rec,impact,x["status"])
            elif tab=="SERVICES":vals=(x["when"],x["name"],x.get("display",""),x.get("state",""),x["target"],x.get("company","Unknown"),x.get("type","Unknown"),x.get("signature","Unknown"),x["risk_label"],x["risk_reason"],rec,impact)
            elif tab=="REGISTRY RUN":vals=(x.get("hive",""),x["name"],x["target"],x.get("company","Unknown"),x.get("type","Unknown"),x.get("signature","Unknown"),x["risk_label"],x["risk_reason"],rec,impact)
            elif tab=="STARTUP FOLDERS":vals=(x.get("scope",""),x["name"],x["target"],x.get("company","Unknown"),x.get("type","Unknown"),x.get("signature","Unknown"),x["risk_label"],x["risk_reason"],rec,impact)
            elif tab=="WINLOGON":vals=(x.get("hive",""),x["name"],x["target"],x.get("company","Unknown"),x.get("type","Unknown"),x.get("signature","Unknown"),x["risk_label"],x["risk_reason"],rec,impact)
            else:vals=(x["when"],x["source"],x["name"],x["target"],x.get("company","Unknown"),x.get("type","Unknown"),x.get("signature","Unknown"),x["risk_label"],x["risk_reason"],rec,impact,x.get("status",""))
            risk=str(x.get("risk_label",x.get("risk","LOW"))).upper()
            if "VERY HIGH" in risk: tag="veryhigh"
            elif "HIGH" in risk: tag="high"
            elif "MEDIUM" in risk: tag="medium"
            elif "LOW / SYSTEM" in risk: tag="system"
            else: tag="low"
            tr.insert("", "end",iid=str(i),values=vals,tags=(tag,))

    def current_tab(self):
        return self.nb.tab(self.nb.select(),"text").strip()

    def set_company_filter(self, value):
        self.company_filter=value or ""
        self.populate()
        self.update_filter_banner()

    def set_signature_filter(self, value):
        self.signature_filter=value or ""
        self.populate()
        self.update_filter_banner()

    def update_filter_banner(self):
        r=self.risk_filter or "ALL"
        c=self.company_filter or "ALL"
        sig=self.signature_filter or "ALL"
        if hasattr(self,"filter_banner"):
            if self.current_tab()=="STARTUP ISSUES":
                self.filter_banner.config(text=f"STARTUP ISSUES: {len(getattr(self,'startup_issues',[]))} broken/missing startup references")
            elif self.current_tab()=="BOOT CAPTURE":
                self.filter_banner.config(text=f"BOOT CAPTURE: {len(getattr(self,'boot_events',[]))} processes observed")
            elif self.current_tab()=="EVENT LOGS":
                self.filter_banner.config(text=f"EVENT LOGS: {len(getattr(self,'event_logs',[]))} matching/relevant events from the last 7 days")
            else:
                self.filter_banner.config(text=f"SHOWING: RISK={r}  |  COMPANY={c}  |  SIGNATURE={sig}")
        for d,key in ((getattr(self,"company_buttons",{}),self.company_filter),(getattr(self,"signature_buttons",{}),self.signature_filter)):
            for k,b in d.items(): b.config(bg="#174817" if k==key else "#081408")

    def set_risk_filter(self, value):
        self.risk_filter=value or ""
        labels={"":"ALL","LOW":"LOW","MEDIUM":"MEDIUM","HIGH":"HIGH","VERY HIGH":"VERY HIGH"}
        shown=labels.get(self.risk_filter,self.risk_filter or "ALL")
        if hasattr(self,"selection_status"):
            self.selection_status.config(text=f"RISK FILTER: {shown}")
        self.update_filter_banner()
        if hasattr(self,"filter_buttons"):
            for k,b in self.filter_buttons.items():
                b.config(bg="#174817" if k==self.risk_filter else "#081408")
        self.populate()
        # Clear stale selection after changing the filtered dataset.
        try:
            _,tr=self.active()
            tr.selection_remove(tr.selection())
        except Exception:
            pass
        self.update_details()

    def update_details(self):
        data,tr=self.active()
        sel=tr.selection()
        if not sel:
            self.detail_status.config(text="NO ITEM SELECTED",fg=DIM)
            self.detail_text.configure(state="normal");self.detail_text.delete("1.0","end");self.detail_text.configure(state="disabled")
            return
        try:
            idx=int(sel[0])
        except Exception:
            self.detail_status.config(text="NO ITEM SELECTED",fg=DIM)
            return
        if idx < 0 or idx >= len(data):
            self.detail_status.config(text="NO ITEM SELECTED",fg=DIM)
            self.detail_text.configure(state="normal");self.detail_text.delete("1.0","end");self.detail_text.configure(state="disabled")
            return

        x=data[idx]
        tab=self.current_tab()

        # Event Logs get an Event Viewer-style detail panel instead of the
        # generic startup/service/process fields.
        if tab=="EVENT LOGS":
            msg=str(x.get("message","")).replace("\r"," ").replace("\n"," ")
            event_lines=[
                "EVENT DETAILS // WINDOWS EVENT VIEWER",
                "────────────────────────────────────────────────────────",
                f"TIME         : {x.get('time','')}",
                f"LOG          : {x.get('log','')}",
                f"EVENT ID     : {x.get('event_id','')}",
                f"LEVEL        : {x.get('level','')}",
                f"PROVIDER     : {x.get('provider','')}",
                f"PROCESS/TASK : {x.get('process_task','') or 'Not detected'}",
                f"MATCH        : {x.get('match','') or 'None'}",
                "",
                "MESSAGE",
                "────────────────────────────────────────────────────────",
                msg or "(No event message)",
            ]
            self.detail_status.config(
                text=f"EVENT {x.get('event_id','')}  •  {x.get('level','')}  •  {x.get('log','')}",
                fg=GREEN
            )
            self.selection_status.config(text=f"EVENT {x.get('event_id','')} // {str(x.get('provider',''))[:60]}")
            self.detail_text.configure(state="normal")
            self.detail_text.delete("1.0","end")
            self.detail_text.insert("1.0","\n".join(event_lines))
            self.detail_text.configure(state="disabled")
            return

        rec,cat,impact=recommendation(x)
        p=os.path.expandvars(x.get("exe") or exe_from(x.get("target","")))
        lines=[
            f"NAME         : {x.get('name','')}",
            f"SOURCE       : {x.get('source','')}",
            f"START / STATE: {x.get('when',x.get('status',''))}",
            f"PATH / CMD   : {x.get('target','')}",
            f"EXECUTABLE   : {p}",
            f"COMPANY      : {x.get('company','Unknown')}",
            f"TYPE         : {x.get('type','Unknown')}",
            f"SIGNATURE    : {x.get('signature','Unknown')}",
            f"RISK         : {x.get('risk_label',x.get('risk',''))}",
            f"WHY          : {x.get('risk_reason','')}",
            f"CHANGE       : {self.changes.get(self.item_key(x),'UNCHANGED')}",
            f"RECOMMEND    : {rec}  |  {cat}",
            f"IMPACT       : {impact}",
        ]
        self.detail_status.config(text=f"{x.get('risk_label',x.get('risk','')).upper()}  •  {x.get('company','Unknown')}",fg=GREEN)
        self.selection_status.config(text=x.get("name","")[:70])
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0","end")
        self.detail_text.insert("1.0","\n".join(lines))
        self.detail_text.configure(state="disabled")

    def selected(self):
        tab=self.current_tab()
        tr=self.tabs[tab].tree
        sel=tr.selection()
        if not sel:
            return None
        try:
            idx=int(sel[0])
        except Exception:
            return None

        data,_=self.active()
        if tab=="LAUNCH SOURCES":
            data=self.launch_sources
        elif tab=="EVENT LOGS":
            data=self.event_logs

        if idx < 0 or idx >= len(data):
            return None
        return data[idx]

    def remove_service_safe(self, x):
        """Robust service removal: resolve -> backup -> elevated PowerShell -> verify."""
        display=str(x.get("display_name") or x.get("name") or "").strip()
        name=str(x.get("service_name") or x.get("name") or "").strip()
        path=str(x.get("path") or x.get("command") or x.get("target") or "").strip()
        loc=str(x.get("location") or x.get("exact_entry") or "").strip()

        # Resolve from the selected Launch Sources row.
        if "|" in loc:
            a,b=[q.strip() for q in loc.split("|",1)]
            if a: name=a
            if b: display=b
        if not name and display:
            name=display

        # Ask Windows for the exact service object, including orphaned services.
        try:
            qname=name.replace("'","''")
            qdisp=display.replace("'","''")
            qpath=path.replace('"',"").replace("'","''")
            ps=("Get-CimInstance Win32_Service | Where-Object { "
                f"$_.Name -eq '{qname}' -or $_.DisplayName -eq '{qdisp}'"
                + (f" -or $_.PathName -like '*{qpath}*'" if qpath else "")
                + " } | Select-Object -First 1 Name,DisplayName,State,StartMode,StartName,PathName,Description | ConvertTo-Json -Compress")
            raw=_zyntrasec_check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",ps],
                                        text=True,stderr=subprocess.DEVNULL,timeout=20).strip()
            if raw:
                cfg=json.loads(raw)
                name=str(cfg.get("Name") or name)
                display=str(cfg.get("DisplayName") or display or name)
                path=str(cfg.get("PathName") or path)
            else:
                cfg={"Name":name,"DisplayName":display,"PathName":path,"State":"Unknown","StartMode":"Unknown"}
        except Exception:
            cfg={"Name":name,"DisplayName":display,"PathName":path,"State":"Unknown","StartMode":"Unknown"}

        if not name:
            messagebox.showerror(APP,"Could not determine the Windows service name.")
            return

        backup_dir=Path("backup")/"service_quarantine"
        backup_dir.mkdir(parents=True,exist_ok=True)
        stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe=re.sub(r"[^A-Za-z0-9_.-]","_",name)
        meta=backup_dir/f"{safe}_{stamp}.json"
        meta.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")

        if not messagebox.askyesno(APP,
            "REMOVE WINDOWS SERVICE\n\n"
            f"Service Name : {name}\n"
            f"Display Name : {display}\n"
            f"State        : {cfg.get('State','Unknown')}\n"
            f"Startup      : {cfg.get('StartMode','Unknown')}\n"
            f"Target       : {path or cfg.get('PathName','Unknown')}\n\n"
            "The tool will automatically request Administrator permission if required.\n"
            "Backup will be saved before removal.\n\nContinue?"):
            return

        # Create a one-shot elevated PowerShell script. This avoids fragile nested quoting.
        psfile=backup_dir/f"REMOVE_{safe}_{stamp}.ps1"
        log=backup_dir/f"REMOVE_{safe}_{stamp}.log"
        esc=name.replace("'","''")
        script=f"""$ErrorActionPreference='Continue'
$svcName='{esc}'
$logFile='{str(log).replace("'","''")}'
"ZYNTRASEC SERVICE REMOVE START: $svcName" | Out-File -FilePath $logFile -Encoding UTF8
try {{ Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue }} catch {{}}
try {{ sc.exe stop "$svcName" | Out-File $logFile -Append }} catch {{}}
Start-Sleep -Milliseconds 500
try {{ sc.exe delete "$svcName" | Out-File $logFile -Append }} catch {{}}
Start-Sleep -Seconds 1
$left=Get-CimInstance Win32_Service -Filter ("Name='"+$svcName.Replace("'","''")+"'") -ErrorAction SilentlyContinue
if($left) {{
  "VERIFY: STILL REGISTERED / MAY BE PENDING DELETION" | Out-File $logFile -Append
  exit 5
}} else {{
  "VERIFY: SERVICE REGISTRATION GONE" | Out-File $logFile -Append
  exit 0
}}
"""
        psfile.write_text(script,encoding="utf-8")

        # Always use an elevated PowerShell attempt for the final operation.
        try:
            _zyntrasec_run([
                "powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",
                f'Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File","{str(psfile)}")'
            ],capture_output=True,text=True,timeout=120)
        except Exception as e:
            messagebox.showerror(APP,f"Could not start Administrator PowerShell:\n{e}\n\nBackup:\n{meta}")
            return

        # Verify with a fresh CIM query.
        try:
            verify_ps=("Get-CimInstance Win32_Service | Where-Object "
                       f"{{$_.Name -eq '{esc}'}} | Measure-Object | Select-Object -ExpandProperty Count")
            vr=_zyntrasec_run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",verify_ps],
                              capture_output=True,text=True,timeout=20)
            count=vr.stdout.strip()
        except Exception:
            count="UNKNOWN"

        if count=="0":
            messagebox.showinfo(APP,
                f"REMOVED + VERIFIED\n\nService: {name}\n\n"
                f"Backup: {meta}\nLog: {log}")
            self.refresh_all()
        elif count=="UNKNOWN":
            messagebox.showwarning(APP,
                f"Removal command completed, but verification failed.\n\n"
                f"Service: {name}\nLog: {log}\n\nUse REFRESH to verify.")
            self.refresh_all()
        else:
            messagebox.showerror(APP,
                f"Windows still reports this service.\n\n"
                f"Service: {name}\n\n"
                f"Check removal log:\n{log}\n\n"
                "If Windows marked it for deletion, a restart may be required before it disappears.")
            self.refresh_all()


    def restore_selected(self):
        tab=self.current_tab()
        x=self.selected()
        if x and tab=="SERVICES":
            name=str(x.get("name") or x.get("service_name") or "").strip()
            if name:
                self.restore_service_by_name(name)
                return
        if x and tab=="LAUNCH SOURCES" and str(x.get("source_type","")).upper()=="SERVICE":
            name=str(x.get("name") or "").strip()
            if name:
                self.restore_service_by_name(name)
                return
        try:
            self.restore()
        except Exception:
            messagebox.showinfo(APP,"Select a backup from RESTORE CENTER.")

    def restore_service_by_name(self,name):
        d=Path("backup")/"service_quarantine"
        safe=re.sub(r"[^A-Za-z0-9_.-]","_",name)
        candidates=sorted(d.glob(safe+"_*.json"),reverse=True)
        if not candidates:
            messagebox.showwarning(APP,"No service backup found for:\n"+name)
            return
        meta=candidates[0]
        try:
            cfg=json.loads(meta.read_text(encoding="utf-8"))
            path=str(cfg.get("PathName",""))
            display=str(cfg.get("DisplayName") or name)
            start=str(cfg.get("StartMode","Manual")).lower()
            mode={"auto":"auto","manual":"demand","disabled":"disabled"}.get(start,"demand")
            if not path:
                raise RuntimeError("Saved service executable path is missing.")
            r=_zyntrasec_run(["sc.exe","create",name,"binPath=",path,"DisplayName=",display,"start=",mode],
                             capture_output=True,text=True,timeout=20)
            if r.returncode!=0 and "already exists" not in (r.stdout+r.stderr).lower():
                raise RuntimeError((r.stderr or r.stdout or "sc.exe create failed").strip())
            desc=str(cfg.get("Description",""))
            if desc:
                _zyntrasec_run(["sc.exe","description",name,desc],capture_output=True,text=True,timeout=10)
            messagebox.showinfo(APP,f"Service restored from:\n{meta}")
            self.scan()
        except Exception as e:
            messagebox.showerror(APP,"Could not restore service:\n"+str(e))


    def _remove_legacy(self,x):
        src=str(x.get("source","")).upper()
        if src in ("SERVICE","WINLOGON","PROCESS"):
            messagebox.showwarning(APP,"This item is protected.")
            return
        p=str(x.get("path",x.get("command","")))
        if p and os.path.exists(p) and os.path.isfile(p):
            backup_dir=Path("backup")/"startup_removed"; backup_dir.mkdir(parents=True,exist_ok=True)
            dst=backup_dir/Path(p).name
            if messagebox.askyesno(APP,f"Move this file to backup?\\n\\n{p}"):
                shutil.move(p,str(dst)); self.scan()
        else:
            messagebox.showinfo(APP,"No removable file target was found.")

    def details(self):
        x=self.selected()
        if not x:return
        p=os.path.expandvars(x.get("exe") or exe_from(x.get("target","")))
        c=company(p);sig,_=file_signature(p)
        size="N/A";modified="N/A";version="N/A";sha="N/A"
        if os.path.isfile(p):
            try:
                st=os.stat(p);size=f"{st.st_size:,} bytes";modified=datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            except:pass
            try:
                r=ps("(Get-Item -LiteralPath '"+p.replace("'","''")+"').VersionInfo | Select-Object FileVersion,ProductVersion | ConvertTo-Json -Compress",8)
                if r and r.stdout.strip():
                    z=json.loads(r.stdout);version=f"{z.get('FileVersion','N/A')} / {z.get('ProductVersion','N/A')}"
            except:pass
            try:
                r=ps("(Get-FileHash -LiteralPath '"+p.replace("'","''")+"' -Algorithm SHA256).Hash",15)
                if r:sha=r.stdout.strip() or "N/A"
            except:pass

        deps="N/A"
        if x.get("service"):
            try:
                r=ps(f"(Get-Service -Name '{x['name'].replace(chr(39),chr(39)+chr(39))}' -ErrorAction SilentlyContinue).DependentServices | Select-Object -ExpandProperty Name | ConvertTo-Json -Compress",8)
                deps=r.stdout.strip() or "None"
            except:pass

        parent="N/A"
        if x.get("source")=="Process":
            try:
                r=ps(f"(Get-CimInstance Win32_Process -Filter \"ProcessId={int(x.get('pid',0))}\" -ErrorAction SilentlyContinue).ParentProcessId",8)
                parent=r.stdout.strip() or "N/A"
            except:pass

        x["company"]=c;x["signature"]=sig
        rec,cat,impact=recommendation(x)
        messagebox.showinfo("ZYNTRASEC // FULL ITEM INTEL",
            f"NAME        : {x.get('name','')}\n"
            f"SOURCE      : {x.get('source','')}\n"
            f"WHEN/STATE  : {x.get('when',x.get('status',''))}\n"
            f"PATH/CMD    : {x.get('target','')}\n"
            f"EXECUTABLE  : {p}\n"
            f"COMPANY     : {c}\n"
            f"TYPE        : {x.get('type','Unknown')}\n"
            f"SIGNATURE   : {sig}\n"
            f"FILE SIZE   : {size}\n"
            f"MODIFIED    : {modified}\n"
            f"VERSION     : {version}\n"
            f"SHA-256     : {sha}\n"
            f"PARENT PID  : {parent}\n"
            f"DEPENDENTS  : {deps}\n"
            f"CHANGE      : {self.changes.get(self.item_key(x),'UNCHANGED')}\n\n"
            f"FAST REVIEW : {x.get('risk_label', x.get('level', x.get('risk', 'UNKNOWN')))}\n"
            f"WHY         : {x['risk_reason']}\n"
            f"RECOMMEND   : {rec} / {cat}\n"
            f"IMPACT      : {impact}\n\n"
            "Risk is a review priority, not a malware verdict.")
    def what_happens(self):
        x=self.selected()
        if not x:return
        rec,cat,impact=recommendation(x)
        messagebox.showinfo("ZYNTRASEC // REMOVE IMPACT",
            f"RECOMMENDATION : {rec}\nCATEGORY       : {cat}\n\nWHAT CHANGES   : {impact}\n\n"
            "Use DISABLE first when possible. Create BACKUP before removing Registry/Startup entries.\n"
            "The tool intentionally does not promise that a component is '100% safe to remove'.")

    def run_now(self):
        x=self.selected()
        if x and messagebox.askyesno(APP,"Run this command now?"):_zyntrasec_popen(x.get("target",""),shell=True)

    def stop_now(self):
        x=self.selected()
        if not x:
            messagebox.showinfo(APP,"Select an item first.")
            return
        source=str(x.get("source") or "").upper()
        if x.get("service") or source in ("SERVICE","WINDOWS SERVICE","SERVICES"):
            name=str(x.get("service_name") or x.get("name") or "").strip()
            if not name:return
            blocked,why=self.protected_item(x)
            if blocked and str(x.get("company","")).lower()=="microsoft corporation":
                messagebox.showwarning(APP,f"STOP BLOCKED\n\n{name}\nReason: {why}")
                return
            if messagebox.askyesno(APP,f"Stop this service?\n\n{name}"):
                r=cmd(["sc","stop",name],15)
                messagebox.showinfo(APP, f"SERVICE STOP REQUESTED\n\n{name}\n\n{(r.stdout or r.stderr or '').strip()}")
                self.refresh_all()
            return
        if source=="PROCESS" or self.current_tab()=="PROCESSES":
            pid=str(x.get("pid") or "").strip(); name=str(x.get("name") or "").strip()
            if not pid.isdigit():
                messagebox.showerror(APP,"Process PID was not detected."); return
            blocked,why=self.protected_item(x)
            if blocked:
                messagebox.showwarning(APP,f"STOP BLOCKED\n\n{name} (PID {pid})\nReason: {why}"); return
            if messagebox.askyesno(APP,f"Stop this process?\n\n{name}\nPID: {pid}\n\nThis stops the running process only; it does not delete its file."):
                r=cmd(["taskkill","/PID",pid],15); time.sleep(0.5)
                still=cmd(["tasklist","/FI",f"PID eq {pid}","/FO","CSV","/NH"],10)
                alive=bool((still.stdout or "").strip()) and "No tasks are running" not in (still.stdout or "")
                if alive:
                    messagebox.showwarning(APP,f"PROCESS STILL RUNNING\n\n{name}\nPID: {pid}\n\nWindows did not stop it. Use REMOVE to terminate it if it is not protected.")
                else:
                    messagebox.showinfo(APP,f"PROCESS STOPPED + VERIFIED\n\n{name}\nPID: {pid}")
                self.refresh_all()
            return
        messagebox.showinfo(APP,"STOP is available for Services and Processes.")

    def _service_action(self, x, startup_type):
        """Change service startup type and verify the result. Uses the real service Name."""
        name=str(x.get("service_name") or x.get("name") or "").strip()
        if not name:
            messagebox.showerror(APP,"Service name was not detected.")
            return False
        safe=name.replace("'", "''")
        # PowerShell handles service names with spaces reliably. The app is already elevated.
        r=ps(f"Set-Service -Name '{safe}' -StartupType {startup_type}; (Get-CimInstance Win32_Service -Filter \"Name='{safe}'\").StartMode",15)
        if not r or r.returncode!=0:
            err=(r.stderr or r.stdout or "Unknown Windows service error").strip() if r else "PowerShell did not return a result."
            messagebox.showerror(APP,f"Could not change service startup mode.\n\nSERVICE: {name}\nREQUESTED: {startup_type}\n\n{err}")
            return False
        mode=(r.stdout or "").strip().splitlines()[-1].strip() if (r.stdout or "").strip() else ""
        expected={"Disabled":"Disabled","Automatic":"Auto","Manual":"Manual"}.get(startup_type,startup_type)
        if mode and mode.lower()!=expected.lower():
            messagebox.showwarning(APP,f"Windows returned an unexpected startup mode.\n\nSERVICE: {name}\nREQUESTED: {startup_type}\nACTUAL: {mode}")
            return False
        x["status"]="Disabled" if startup_type=="Disabled" else "Enabled"
        x["start_mode"]="Disabled" if startup_type=="Disabled" else startup_type
        return True

    def _task_action(self, x, enable=True):
        name=str(x.get("name") or "").replace("'", "''")
        path=str(x.get("taskpath") or "\\").replace("'", "''")
        if not name:
            messagebox.showerror(APP,"Task name was not detected.")
            return False
        action="Enable-ScheduledTask" if enable else "Disable-ScheduledTask"
        r=ps(f"{action} -TaskName '{name}' -TaskPath '{path}'; (Get-ScheduledTask -TaskName '{name}' -TaskPath '{path}').State",15)
        if not r or r.returncode!=0:
            err=(r.stderr or r.stdout or "Unknown Scheduled Task error").strip() if r else "PowerShell did not return a result."
            messagebox.showerror(APP,f"Could not change scheduled task.\n\nTASK: {name}\nPATH: {path}\n\n{err}")
            return False
        x["status"]="Ready" if enable else "Disabled"
        return True

    def _startup_approved_action(self, x, enable=True):
        r"""Enable/disable a Windows Startup Apps entry using Explorer\StartupApproved."""
        name=str(x.get("name") or "").strip()
        if not name:
            messagebox.showerror(APP,"Startup app name was not detected.")
            return False
        location=str(x.get("startup_source") or "").lower()
        target=str(x.get("target") or "")
        hive=str(x.get("startup_approved_hive") or "").upper()
        if not hive:
            if "hklm" in location or "local_machine" in location or target.lower().startswith(os.path.normcase(os.environ.get("PROGRAMDATA",""))):
                hive="HKLM"
            else:
                hive="HKCU"
        if "startupfolder" in location or "startup folder" in location or "startup\\" in target.lower():
            subkey=r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
        elif "run32" in location:
            subkey=r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"
        else:
            subkey=r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
        root="HKLM:" if hive=="HKLM" else "HKCU:"
        # Preserve the existing binary payload when possible; only change the first state byte.
        safe_name=name.replace("'","''")
        state=2 if enable else 3
        script=(
            f"$p='{root}\\{subkey}'.Replace('\\\\','\\'); "
            f"if(-not(Test-Path -LiteralPath $p)){{New-Item -Path $p -Force | Out-Null}}; "
            f"$v=$null; try{{$v=(Get-ItemProperty -LiteralPath $p -Name '{safe_name}' -ErrorAction Stop).'{safe_name}'}}catch{{}}; "
            f"if($v -is [byte[]] -and $v.Length -ge 4){{$v[0]={state}}}else{{$v=[byte[]]( {state},0,0,0,0,0,0,0,0,0,0,0 )}}; "
            f"Set-ItemProperty -LiteralPath $p -Name '{safe_name}' -Value $v -Type Binary; "
            f"$z=(Get-ItemProperty -LiteralPath $p -Name '{safe_name}').'{'{'}safe_name{'}'}'; "
            f"if($z -is [byte[]] -and $z.Length -ge 1){{if($z[0] -eq {state}){{'OK'}}else{{'FAILED'}}}}else{{'FAILED'}}"
        )
        # Correct the final property interpolation explicitly (PowerShell accepts quoted property names).
        script=script.replace(".'{safe_name}'",f".'{safe_name}'")
        r=ps(script,15)
        if not r or r.returncode!=0 or "OK" not in (r.stdout or ""):
            err=(r.stderr or r.stdout or "Windows did not accept the StartupApproved change.").strip() if r else "PowerShell did not return a result."
            messagebox.showerror(APP,f"Could not change Startup App state.\n\nAPP: {name}\nREQUESTED: {'Enabled' if enable else 'Disabled'}\n\n{err}")
            return False
        x["status"]="Enabled" if enable else "Disabled"
        x["task_manager_status"]=x["status"]
        return True

    def disable(self):
        x=self.selected()
        if not x:
            messagebox.showinfo(APP,"Select an item first.")
            return
        source=str(x.get("source") or "").lower()
        is_service=bool(x.get("service")) or source in ("windows service","service","services") or self.current_tab()=="SERVICES"
        is_task=source=="task scheduler" or self.current_tab()=="TASK SCHEDULER"
        is_startup_app=bool(x.get("task_manager")) or source=="task manager startup app" or self.current_tab()=="AUTO START" and bool(x.get("task_manager"))
        blocked,why=self.protected_item(x)
        if blocked and is_service:
            # protected_item historically blocks all service rows; allow a reversible startup-mode change
            # for non-core services while still protecting Windows/Microsoft-signed core components.
            if str(x.get("company","")).lower()=="microsoft corporation" or str(x.get("name","")).lower() in ("winmgmt","rpcss","eventlog","plugplay","dcomlaunch"):
                messagebox.showwarning("ZYNTRASEC // BLOCKED",f"DISABLE BLOCKED\n\n{x.get('name','')}\nReason: {why}")
                return
        if not messagebox.askyesno("ZYNTRASEC // SAFETY CHECK",
            f"Disable this item?\n\n{x.get('name','')}\n{x.get('target','')}\n\n"
            "This is reversible. The change will be verified after Windows applies it."):
            return
        if is_service:
            if self._service_action(x,"Disabled"):
                self.populate()
                messagebox.showinfo(APP,f"SERVICE DISABLED\n\n{x.get('name','')}\n\nStartup mode: Disabled")
            return
        if is_task:
            if self._task_action(x,False):
                self.populate()
                messagebox.showinfo(APP,f"TASK DISABLED\n\n{x.get('name','')}\n\nState: Disabled")
            return
        if is_startup_app:
            if self._startup_approved_action(x,False):
                self.populate()
                messagebox.showinfo(APP,f"STARTUP APP DISABLED\n\n{x.get('name','')}\n\nTask Manager Startup Apps state: Disabled")
            return
        messagebox.showinfo(APP,"This item type is not directly disable-able here.\nUse REMOVE only for supported Registry/Startup entries, or use the item-specific control.")

    def enable(self):
        x=self.selected()
        if not x:
            messagebox.showinfo(APP,"Select an item first.")
            return
        source=str(x.get("source") or "").lower()
        is_service=bool(x.get("service")) or source in ("windows service","service","services") or self.current_tab()=="SERVICES"
        is_task=source=="task scheduler" or self.current_tab()=="TASK SCHEDULER"
        is_startup_app=bool(x.get("task_manager")) or source=="task manager startup app"
        if is_service:
            if messagebox.askyesno(APP,"Enable this service as Automatic?\n\nThe startup mode will be set to Automatic."):
                if self._service_action(x,"Automatic"):
                    self.populate()
                    messagebox.showinfo(APP,f"SERVICE ENABLED\n\n{x.get('name','')}\n\nStartup mode: Automatic")
            return
        if is_task:
            if messagebox.askyesno(APP,"Enable this scheduled task?"):
                if self._task_action(x,True):
                    self.populate()
                    messagebox.showinfo(APP,f"TASK ENABLED\n\n{x.get('name','')}\n\nState: Ready")
            return
        if is_startup_app:
            if messagebox.askyesno(APP,"Enable this Startup App?\n\nWindows Task Manager will show it as Enabled after verification."):
                if self._startup_approved_action(x,True):
                    self.populate()
                    messagebox.showinfo(APP,f"STARTUP APP ENABLED\n\n{x.get('name','')}\n\nTask Manager Startup Apps state: Enabled")
            return
        messagebox.showinfo(APP,"Registry Run entries are enabled while the entry exists.\nStartup-folder items are enabled while they remain in the Startup folder.")

    def protected_item(self,x):
        p=os.path.normcase(os.path.expandvars(x.get("exe") or exe_from(x.get("target",""))))
        target=os.path.normcase(os.path.expandvars(str(x.get("target",""))))
        windir=os.path.normcase(os.environ.get("WINDIR",r"C:\Windows"))
        programdata=os.path.normcase(os.environ.get("PROGRAMDATA",r"C:\ProgramData"))
        source=str(x.get("source","")).lower()
        company=str(x.get("company","")).lower()
        name=str(x.get("name","")).lower()

        # Never allow the Remove button to delete core Windows/service files.
        if p.startswith(windir+os.sep) or target.startswith(windir+os.sep):
            return True, "Windows system path"
        if source=="windows service":
            return True, "Windows service"
        if company=="microsoft corporation" and x.get("signature")=="Valid":
            return True, "Microsoft-signed component"
        if any(k in name for k in ("winlogon","wininit","services","lsass","smss","csrss","svchost")):
            return True, "Windows core process/component"
        if source=="winlogon":
            return True, "Winlogon configuration"
        return False, ""

    def confirm_destructive(self,x,action):
        blocked,why=self.protected_item(x)
        if blocked:
            messagebox.showwarning(
                "ZYNTRASEC // BLOCKED",
                f"{action} BLOCKED\n\n"
                f"ITEM: {x.get('name','')}\n"
                f"PATH: {x.get('target','')}\n"
                f"REASON: {why}\n\n"
                "This safety lock prevents accidental removal of Windows/system components."
            )
            return False

        rec,cat,impact=recommendation(x)
        text=(
            f"ACTION: {action}\n\n"
            f"NAME: {x.get('name','')}\n"
            f"COMPANY: {x.get('company','Unknown')}\n"
            f"TYPE: {x.get('type','Unknown')}\n"
            f"SIGNATURE: {x.get('signature','Unknown')}\n"
            f"PATH: {x.get('target','')}\n\n"
            f"RECOMMENDATION: {rec}\n"
            f"IMPACT: {impact}\n\n"
            "A backup will be created before a supported removal.\n"
            "Continue?"
        )
        return messagebox.askyesno("ZYNTRASEC // FINAL SAFETY CHECK",text)

    def _remove_registry_startup(self, x):
        """Remove a Registry Run/RunOnce startup value after exporting its key."""
        name=str(x.get("name") or "").strip()
        target=str(x.get("target") or "")
        if not name:
            messagebox.showerror(APP,"Registry value name was not detected.")
            return False
        root=x.get("root")
        hive=str(x.get("hive") or "").upper()
        if root is None:
            root=winreg.HKEY_LOCAL_MACHINE if hive=="HKLM" else winreg.HKEY_CURRENT_USER
        key=str(x.get("key") or r"Software\Microsoft\Windows\CurrentVersion\Run")
        # Ensure we only touch the standard Run/RunOnce startup locations.
        allowed=(r"Software\Microsoft\Windows\CurrentVersion\Run",
                 r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
        if key not in allowed:
            messagebox.showwarning(APP,"This registry location is not a supported startup-removal target.")
            return False
        hive_name="HKLM" if root==winreg.HKEY_LOCAL_MACHINE else "HKCU"
        backup_dir=Path("backup")/"registry_removed"
        backup_dir.mkdir(parents=True,exist_ok=True)
        stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe=re.sub(r"[^A-Za-z0-9_.-]","_",name)
        backup_file=backup_dir/f"{hive_name}_{safe}_{stamp}.reg"
        full=f"{hive_name}\\{key}"
        try:
            ex=_zyntrasec_run(["reg","export",full,str(backup_file),"/y"],capture_output=True,text=True,timeout=20)
            if ex.returncode!=0:
                raise RuntimeError((ex.stderr or ex.stdout or "Registry export failed").strip())
            with winreg.OpenKey(root,key,0,winreg.KEY_SET_VALUE|winreg.KEY_QUERY_VALUE) as k:
                current,_=winreg.QueryValueEx(k,name)
                # If a target is known, require it to match before deletion.
                if target and str(current)!=target:
                    raise RuntimeError("The startup command changed since the scan. Refresh and try again.")
                winreg.DeleteValue(k,name)
            # Verify the value is gone.
            try:
                with winreg.OpenKey(root,key,0,winreg.KEY_QUERY_VALUE) as k:
                    winreg.QueryValueEx(k,name)
                raise RuntimeError("Windows still reports the registry value.")
            except FileNotFoundError:
                pass
            messagebox.showinfo(APP,f"STARTUP ENTRY REMOVED + VERIFIED\n\n{name}\n\nBackup: {backup_file}")
            return True
        except Exception as e:
            messagebox.showerror(APP,f"Could not remove Registry startup entry.\n\n{name}\n\n{e}")
            return False

    def _remove_startup_file(self, x):
        """Move a Startup-folder file/shortcut into a timestamped backup instead of deleting it."""
        target=str(x.get("target") or x.get("path") or "").strip()
        if not target or not os.path.exists(target):
            messagebox.showinfo(APP,"Startup file is already missing or its path could not be resolved.")
            return False
        if not messagebox.askyesno(APP, f"Move this Startup item to backup?\n\n{target}\n\nThe original will not be permanently deleted."):
            return False
        try:
            backup_dir=Path("backup")/"startup_removed"
            backup_dir.mkdir(parents=True,exist_ok=True)
            stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dst=backup_dir/f"{stamp}_{Path(target).name}"
            shutil.move(target,str(dst))
            if os.path.exists(target):
                raise RuntimeError("Windows still reports the Startup item at its original path.")
            messagebox.showinfo(APP,f"STARTUP ITEM REMOVED + VERIFIED\n\nMoved to backup:\n{dst}")
            return True
        except Exception as e:
            messagebox.showerror(APP,f"Could not remove Startup item.\n\n{e}")
            return False

    def remove(self):
        x=self.selected()
        if not x:
            messagebox.showinfo(APP,"Select an item first.")
            return

        tab=self.current_tab()

        # Direct removal from the main startup tabs. Registry values are deleted
        # from their exact Run/RunOnce key; Startup-folder files are moved to backup.
        source=str(x.get("source") or "").upper()
        startup_source=str(x.get("startup_source") or "").upper()
        if tab in ("AUTO START","STARTUP APPS","REGISTRY RUN"):
            if source=="REGISTRY RUN" or startup_source=="REGISTRY RUN" or tab=="REGISTRY RUN":
                if not self.confirm_destructive(x,"REMOVE"):
                    return
                return self._remove_registry_startup(x)
            if source in ("USER STARTUP","ALL USERS STARTUP") or "STARTUP" in startup_source or tab=="STARTUP FOLDERS":
                if not self.confirm_destructive(x,"REMOVE"):
                    return
                return self._remove_startup_file(x)
            if tab=="STARTUP APPS" and x.get("task_manager"):
                messagebox.showinfo(APP,"This Startup App does not expose a removable underlying Run/Startup-file source. Use DISABLE first; REMOVE is only enabled when the actual startup source can be safely identified.")
                return

        if tab=="TASK SCHEDULER":
            name=str(x.get("name") or "").strip(); path=str(x.get("taskpath") or "\\").strip()
            if name and self.confirm_destructive(x,"REMOVE"):
                try:
                    r=_zyntrasec_run(["schtasks","/Delete","/TN",name,"/F"],capture_output=True,text=True,timeout=30)
                    if r.returncode!=0: raise RuntimeError((r.stderr or r.stdout or "schtasks failed").strip())
                    messagebox.showinfo(APP,f"SCHEDULED TASK REMOVED\n\n{name}")
                    self.refresh_all(); return
                except Exception as e:
                    messagebox.showerror(APP,f"Could not remove scheduled task.\n\n{name}\n\n{e}")
                    return


        # LAUNCH SOURCES are diagnostic rows; remove the actual startup source
        # only after identifying the source type and showing an explicit confirmation.
        if tab=="LAUNCH SOURCES":
            kind=str(x.get("source_type") or x.get("launch_source") or x.get("source") or "").upper()
            loc=str(x.get("location",""))
            cmd=str(x.get("command",""))
            target=str(x.get("target",""))

            if kind in ("SERVICE","SERVICES","WINDOWS SERVICE","WINDOWS_SERVICES"):
                return self.remove_service_safe(x)

            if kind=="SCHEDULED TASK":
                m=re.search(r'(?i)(\\[^|]+)$',loc)
                task_name=loc.strip()
                if "|" in task_name:
                    task_name=task_name.split("|")[-1].strip()
                if not messagebox.askyesno(APP,
                    f"Disable/remove this scheduled task?\\n\\n{task_name}\\n\\nCommand:\\n{cmd}\\n\\nA backup/export is recommended first."):
                    return
                try:
                    _zyntrasec_run(["schtasks","/Delete","/TN",task_name,"/F"],check=True,
                                   capture_output=True,text=True)
                    messagebox.showinfo(APP,"Scheduled task removed.")
                    self.scan_launch_sources()
                    return
                except Exception as e:
                    messagebox.showerror(APP,"Could not remove scheduled task:\\n"+str(e))
                    return

            if kind=="REGISTRY":
                if not messagebox.askyesno(APP,
                    f"Remove this Run/RunOnce startup entry?\\n\\n{loc}\\n\\n{cmd}\\n\\nA .reg backup will be created first."):
                    return
                try:
                    # Export the relevant key before deletion.
                    keypath=loc.rsplit("\\\\",1)[0]
                    value_name=loc.rsplit("\\\\",1)[-1]
                    backup_dir=Path("backup"); backup_dir.mkdir(exist_ok=True)
                    safe=re.sub(r'[^A-Za-z0-9_.-]+','_',value_name)
                    backup_file=backup_dir/f"registry_{safe}_V43.reg"
                    hive="HKCU" if keypath.startswith("Software") else "HKLM"
                    full=f"{hive}\\\\{keypath}"
                    _zyntrasec_run(["reg","export",full,str(backup_file),"/y"],capture_output=True,text=True)
                    # Determine hive from the original path.
                    if loc.startswith("Software\\"):
                        # V43 rows are from the four Run/RunOnce keys; prefer HKCU then HKLM based on command lookup.
                        # We can safely delete by searching both exact value names and only deleting a matching value.
                        deleted=False
                        for root in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
                            for sub in (r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                                        r"Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce"):
                                try:
                                    k=winreg.OpenKey(root,sub,0,winreg.KEY_SET_VALUE|winreg.KEY_QUERY_VALUE)
                                    try:
                                        v,_=winreg.QueryValueEx(k,value_name)
                                        if str(v)==cmd:
                                            winreg.DeleteValue(k,value_name); deleted=True
                                    finally: winreg.CloseKey(k)
                                except Exception: pass
                        if deleted:
                            messagebox.showinfo(APP,f"Startup registry entry removed.\\nBackup: {backup_file}")
                            self.scan_launch_sources()
                            return
                    raise RuntimeError("Matching registry value was not found.")
                except Exception as e:
                    messagebox.showerror(APP,"Could not remove registry startup entry:\\n"+str(e))
                    return

            if kind in ("STARTUP FILE","STARTUP SHORTCUT"):
                if not target or not os.path.exists(target):
                    messagebox.showinfo(APP,"Target is already missing.")
                    self.scan_launch_sources()
                    return
                if not messagebox.askyesno(APP,
                    f"Move this Startup item to backup?\\n\\n{target}"):
                    return
                try:
                    backup_dir=Path("backup")/"startup_removed"
                    backup_dir.mkdir(parents=True,exist_ok=True)
                    dst=backup_dir/Path(target).name
                    shutil.move(target,str(dst))
                    messagebox.showinfo(APP,f"Startup item moved to backup:\\n{dst}")
                    self.scan_launch_sources()
                    return
                except Exception as e:
                    messagebox.showerror(APP,"Could not move Startup item:\\n"+str(e))
                    return

            messagebox.showinfo(APP,"This Launch Source type is diagnostic-only or requires manual handling.\\nUse the exact source shown in the table.")
            return

        # Service rows need service-specific handling; they are not files.
        src_name=str(x.get("source","")).upper()
        if src_name=="SERVICE":
            return self.remove_service_safe(x)

        # Processes can be terminated from REMOVE. REMOVE terminates the running
        # process only; it never deletes the executable file from disk.
        if src_name=="PROCESS" or tab=="PROCESSES":
            pid=str(x.get("pid") or "").strip(); name=str(x.get("name") or "").strip()
            if not pid.isdigit():
                messagebox.showerror(APP,"Process PID was not detected."); return
            blocked,why=self.protected_item(x)
            if blocked:
                messagebox.showwarning(APP,f"REMOVE BLOCKED\n\n{name} (PID {pid})\nReason: {why}\n\nREMOVE terminates the running process; it does not delete the executable file."); return
            if not messagebox.askyesno("ZYNTRASEC // TERMINATE PROCESS",
                f"Terminate this running process?\n\n{name}\nPID: {pid}\n\nREMOVE means terminate the process only. The executable/file will NOT be deleted.\n\nContinue?"):
                return
            r=cmd(["taskkill","/PID",pid,"/F"],15); time.sleep(0.5)
            still=cmd(["tasklist","/FI",f"PID eq {pid}","/FO","CSV","/NH"],10)
            alive=bool((still.stdout or "").strip()) and "No tasks are running" not in (still.stdout or "")
            if alive:
                messagebox.showerror(APP,f"PROCESS TERMINATION FAILED\n\n{name}\nPID: {pid}\n\n{(r.stderr or r.stdout or '').strip()}")
            else:
                messagebox.showinfo(APP,f"PROCESS TERMINATED + VERIFIED\n\n{name}\nPID: {pid}\n\nExecutable was NOT deleted.")
            self.refresh_all(); return

        if src_name=="WINLOGON":
            messagebox.showwarning(APP,"This item cannot be removed from this button.\n\nWinlogon configuration is protected."); return

        # Existing V32 removal behavior for other tabs.
        try:
            self._remove_legacy(x)
        except AttributeError:
            messagebox.showwarning(APP,"Remove is not available for this item. Use BACKUP/Disable instead.")


    def permanent_delete(self):
        """Permanently delete a selected non-protected file after explicit confirmation.
        This intentionally does NOT recursively delete arbitrary folders or Windows/system files.
        """
        x=self.selected()
        if not x:
            messagebox.showinfo(APP,"Select an item first.")
            return
        blocked,why=self.protected_item(x)
        if blocked:
            messagebox.showwarning(APP,f"PERMANENT DELETE BLOCKED\n\n{x.get('name','')}\nReason: {why}\n\nWindows/system components are protected.")
            return
        source=str(x.get("source") or "").upper()
        if source in ("SERVICE","WINDOWS SERVICE","SERVICES","WINLOGON") or self.current_tab()=="SERVICES":
            messagebox.showwarning(APP,"PERMANENT DELETE BLOCKED\n\nServices are not deleted as files. Remove the service registration using REMOVE first, then uninstall the owning application normally.")
            return
        target=str(x.get("exe") or x.get("target") or x.get("path") or "").strip()
        target=os.path.expandvars(target).strip().strip('\"')
        # Only accept a concrete local file path; do not execute or expand arbitrary commands.
        if not target or not os.path.isfile(target):
            target=exe_from(x.get("target", ""))
        target=os.path.abspath(os.path.expandvars(str(target)).strip().strip('\"')) if target else ""
        if not target or not os.path.isfile(target):
            messagebox.showwarning(APP,"PERMANENT DELETE\n\nNo existing executable/file was found for this item.")
            return
        # Never recursively delete directories and never delete files outside a normal local path.
        windir=os.path.normcase(os.path.abspath(os.environ.get("WINDIR",r"C:\\Windows")))
        if os.path.normcase(target).startswith(windir+os.sep):
            messagebox.showwarning(APP,"PERMANENT DELETE BLOCKED\n\nWindows system files are protected.")
            return
        sig,_=file_signature(target)
        company_name=str(x.get("company") or company(target) or "Unknown")
        first=(f"PERMANENT DELETE\n\nFILE:\n{target}\n\nCOMPANY: {company_name}\nSIGNATURE: {sig}\n\nThis will permanently delete the FILE.\nThere is no automatic restore for this action.\n\nContinue?")
        if not messagebox.askyesno("ZYNTRASEC // PERMANENT DELETE",first):
            return
        # For a running process, stop it first so the file can be removed.
        if source=="PROCESS" or self.current_tab()=="PROCESSES":
            pid=str(x.get("pid") or "").strip()
            if pid.isdigit():
                try:
                    cmd(["taskkill","/PID",pid,"/F"],15)
                    time.sleep(0.8)
                except Exception: pass
        if not messagebox.askyesno("ZYNTRASEC // FINAL CONFIRMATION",
            f"FINAL CONFIRMATION\n\nPermanently delete this file?\n\n{target}\n\nThis cannot be undone by ZYNTRASEC.\nClick YES only if you are certain."):
            return
        try:
            os.remove(target)
            if os.path.exists(target):
                raise RuntimeError("Windows still reports the file as present.")
            messagebox.showinfo(APP,f"PERMANENT DELETE COMPLETE + VERIFIED\n\n{target}")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror(APP,f"PERMANENT DELETE FAILED\n\n{target}\n\n{e}\n\nThe file may be in use or protected by Windows.")

    def _intel_all_items(self):
        pools=[("AUTO START",self.startup),("TASK",self.tasks),("SERVICE",self.services),
               ("PROCESS",self.processes),("WINLOGON",self.winlogon),
               ("STARTUP ISSUE",self.startup_issues),("LAUNCH SOURCE",self.launch_sources)]
        rows=[]
        for kind,items in pools:
            for x in items or []: rows.append((kind,x))
        return rows

    def _intel_render(self,tree,items,query=""):
        for iid in tree.get_children(): tree.delete(iid)
        q=(query or "").strip().lower()
        for kind,x in items:
            if q and q not in json.dumps(x,default=str).lower(): continue
            name=str(x.get("name") or x.get("display_name") or "")
            path=str(x.get("target") or x.get("path") or x.get("command") or "")
            status=str(x.get("status") or x.get("state") or x.get("when") or "")
            detail=str(x.get("company") or x.get("provider") or x.get("details") or x.get("risk_label") or "")
            tree.insert("", "end", values=(kind,name,path,status,detail))

    def _intel_set_text(self,w,s):
        w.configure(state="normal");w.delete("1.0","end");w.insert("1.0",s);w.configure(state="disabled")

    def open_intelligence_hub(self):
        if getattr(self,"_intel_window",None) is not None:
            try:
                if self._intel_window.winfo_exists():
                    self._intel_window.lift();return
            except Exception: pass
        win=tk.Toplevel(self);self._intel_window=win
        win.title("ZYNTRASEC // INTELLIGENCE HUB");win.geometry("1320x760");win.configure(bg=BG)
        tk.Label(win,text="ZYNTRASEC // INTELLIGENCE HUB",bg=BG,fg=GREEN,font=("Consolas",16,"bold")).pack(anchor="w",padx=14,pady=(10,2))
        tk.Label(win,text="SEARCH • HEALTH • BROKEN ITEMS • DUPLICATES • PROCESS TREE • TIMELINE • DEPENDENCIES • SAFE REMOVE PREVIEW",bg=BG,fg=DIM,font=("Consolas",8,"bold")).pack(anchor="w",padx=14,pady=(0,8))
        top=tk.Frame(win,bg=BG);top.pack(fill="x",padx=14,pady=3)
        tk.Label(top,text="SEARCH EVERYTHING",bg=BG,fg=GREEN,font=("Consolas",9,"bold")).pack(side="left",padx=(0,6))
        qv=tk.StringVar()
        qe=tk.Entry(top,textvariable=qv,bg="#010201",fg=GREEN,insertbackground=GREEN,font=("Consolas",10),relief="solid",bd=1,width=38);qe.pack(side="left",padx=4)
        body=tk.Frame(win,bg=BG);body.pack(fill="both",expand=True,padx=14,pady=5)
        left=tk.Frame(body,bg="#061006");left.pack(side="left",fill="both",expand=True)
        right=tk.Frame(body,bg="#061006",width=390);right.pack(side="right",fill="both",padx=(8,0));right.pack_propagate(False)
        cols=("TYPE","NAME","PATH / COMMAND","STATUS","DETAIL");tree=ttk.Treeview(left,columns=cols,show="headings")
        for c,w in zip(cols,(120,220,430,150,220)): tree.heading(c,text=c);tree.column(c,width=w,anchor="w")
        tree.pack(fill="both",expand=True)
        sx=ttk.Scrollbar(left,orient="horizontal",command=tree.xview);sx.pack(fill="x");tree.configure(xscrollcommand=sx.set)
        info=tk.Text(right,bg="#020502",fg=GREEN,insertbackground=GREEN,font=("Consolas",9),wrap="word",relief="flat");info.pack(fill="both",expand=True,padx=6,pady=6)
        self._intel_set_text(info,"INTELLIGENCE HUB READY\n\nUse the controls above/below to inspect the current Windows state.")
        tk.Button(top,text="SEARCH",command=lambda:self._intel_render(tree,self._intel_all_items(),qv.get()),bg="#081408",fg=GREEN,activebackground=GREEN,activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=3)
        tk.Button(top,text="HEALTH",command=lambda:self._intel_health(info),bg="#081408",fg="#54d6ff",activebackground="#54d6ff",activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=3)
        tk.Button(top,text="BROKEN / MISSING",command=lambda:self._intel_broken(tree),bg="#081408",fg="#ffd54a",activebackground="#ffd54a",activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=3)
        tk.Button(top,text="DUPLICATES",command=lambda:self._intel_duplicates(tree),bg="#081408",fg="#ff8a00",activebackground="#ff8a00",activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=3)
        tk.Button(top,text="PROCESS TREE",command=lambda:self._intel_process_tree(tree),bg="#081408",fg="#b66cff",activebackground="#b66cff",activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=3)
        tk.Button(top,text="TIMELINE",command=lambda:self._intel_timeline(tree),bg="#081408",fg="#54d6ff",activebackground="#54d6ff",activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=3)
        bottom=tk.Frame(win,bg=BG);bottom.pack(fill="x",padx=14,pady=(0,10))
        tk.Button(bottom,text="SERVICE DEPENDENCIES",command=lambda:self._intel_dependencies(info),bg="#081408",fg="#54d6ff",activebackground="#54d6ff",activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=2)
        tk.Button(bottom,text="SAFE REMOVE PREVIEW",command=lambda:self._intel_remove_preview(info),bg="#081408",fg="#ffd54a",activebackground="#ffd54a",activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=2)
        tk.Button(bottom,text="RESTORE CENTER",command=self.restore_center,bg="#081408",fg=GREEN,activebackground=GREEN,activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=2)
        tk.Button(bottom,text="REFRESH MAIN DATA",command=self.refresh_all,bg="#081408",fg=GREEN,activebackground=GREEN,activeforeground="black",font=("Consolas",9,"bold"),relief="solid",bd=1).pack(side="left",padx=2)
        self._intel_render(tree,self._intel_all_items());qe.focus_set()

    def _intel_health(self,info):
        rows=self._intel_all_items();broken=third=unsigned=high=changed=0
        for _,x in rows:
            p=os.path.expandvars(x.get("exe") or exe_from(x.get("target","")))
            if p and not os.path.exists(p) and x.get("source") not in ("PROCESS","Winlogon"): broken+=1
            if str(x.get("type","")).upper()=="3RD PARTY": third+=1
            if str(x.get("signature","")).upper() in ("UNKNOWN","NOT SIGNED","NOTSIGNED","INVALID"): unsigned+=1
            if str(x.get("risk_label","")).upper() in ("HIGH","VERY HIGH"): high+=1
            if self.changes.get(self.item_key(x),"UNCHANGED") not in ("UNCHANGED","BASELINE"): changed+=1
        self._intel_set_text(info,"SYSTEM HEALTH SUMMARY\n====================\n"
            f"Tracked items       : {len(rows)}\nBroken / missing    : {broken}\n3rd party           : {third}\nUnsigned/unknown    : {unsigned}\nHigh+ review        : {high}\nChanged since base  : {changed}\n\nInspection indicators only; not a malware verdict.")

    def _intel_broken(self,tree):
        rows=[]
        for kind,x in self._intel_all_items():
            p=os.path.expandvars(x.get("exe") or exe_from(x.get("target","")))
            if p and not os.path.exists(p): rows.append((kind,x))
        self._intel_render(tree,rows)

    def _intel_duplicates(self,tree):
        groups={}
        for kind,x in self._intel_all_items():
            p=os.path.expandvars(x.get("exe") or exe_from(x.get("target","")))
            if p: groups.setdefault(os.path.normcase(p),[]).append((kind,x))
        rows=[]
        for vals in groups.values():
            if len(vals)>1: rows.extend(vals)
        self._intel_render(tree,rows)

    def _intel_process_tree(self,tree):
        for iid in tree.get_children(): tree.delete(iid)
        try:
            cmd='Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath | ConvertTo-Json -Compress'
            raw=_zyntrasec_check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",cmd],text=True,stderr=subprocess.DEVNULL,timeout=20).strip()
            obj=json.loads(raw) if raw else []
            if isinstance(obj,dict): obj=[obj]
        except Exception as e:
            tree.insert("", "end", values=("PROCESS TREE","ERROR",str(e),"",""));return
        by_parent={}
        for p in obj: by_parent.setdefault(str(p.get("ParentProcessId","")),[]).append(p)
        def add(parent,depth=0):
            for p in by_parent.get(str(parent),[]):
                prefix="  "*depth+("└─ " if depth else "")
                tree.insert("", "end", values=("PROCESS",prefix+str(p.get("Name","")),str(p.get("ExecutablePath") or ""),f"PID {p.get('ProcessId','')}",f"PPID {p.get('ParentProcessId','')}"))
                add(p.get("ProcessId",""),depth+1)
        add("0")

    def _intel_timeline(self,tree):
        for iid in tree.get_children(): tree.delete(iid)
        ev=[("EVENT",e.get("time",""),e.get("log",""),e.get("event_id",""),e.get("provider",""),e.get("message","")) for e in self.event_logs or []]
        ev += [("BOOT",e.get("time",""),e.get("pid",""),e.get("process",""),e.get("source",""),e.get("status","")) for e in self.boot_events or []]
        ev.sort(key=lambda x:str(x[1]),reverse=True)
        for e in ev: tree.insert("", "end", values=(e[0],e[1],e[2],e[3],e[4],e[5][:180]))

    def _intel_dependencies(self,info):
        x=self.selected()
        if not x or "SERVICE" not in str(x.get("source","")).upper():
            self._intel_set_text(info,"SERVICE DEPENDENCIES\n\nSelect a Windows Service row in the main window first.");return
        name=str(x.get("service_name") or x.get("name") or x.get("display") or "").strip()
        try:
            q=name.replace("'","''")
            cmd=f"$s=Get-Service -Name '{q}' -ErrorAction Stop; [pscustomobject]@{{Name=$s.Name;Display=$s.DisplayName;Status=$s.Status;Required=(($s.RequiredServices|ForEach-Object Name)-join ', ');Dependents=(($s.DependentServices|ForEach-Object Name)-join ', ')}} | ConvertTo-Json -Compress"
            d=json.loads(_zyntrasec_check_output(["powershell","-NoProfile","-Command",cmd],text=True,stderr=subprocess.DEVNULL,timeout=15).strip())
            self._intel_set_text(info,"SERVICE DEPENDENCIES\n===================\n"
                f"Name       : {d.get('Name','')}\nDisplay    : {d.get('Display','')}\nStatus     : {d.get('Status','')}\n\nRequires   : {d.get('Required') or 'None'}\nDependents : {d.get('Dependents') or 'None'}")
        except Exception as e: self._intel_set_text(info,"SERVICE DEPENDENCIES\n\nCould not query service:\n"+str(e))

    def _intel_remove_preview(self,info):
        x=self.selected()
        if not x: self._intel_set_text(info,"SAFE REMOVE PREVIEW\n\nNo item selected in the main window.");return
        source=str(x.get("source","")).upper();target=str(x.get("target") or x.get("path") or x.get("command") or "");name=str(x.get("name") or x.get("display_name") or "")
        if source in ("PROCESS","WINLOGON"): action="Protected: Remove is blocked for this source."
        elif "SERVICE" in source: action="Backup metadata → stop service → delete registration → verify → refresh."
        elif source=="REGISTRY RUN": action="Backup exact Run/RunOnce value → remove → verify → refresh."
        elif "TASK" in source: action="Backup task metadata → remove exact task → verify → refresh."
        elif "STARTUP" in source: action="Backup/move startup item → verify → refresh."
        else: action="Source-specific safe handler → backup where supported → verify → refresh."
        self._intel_set_text(info,"SAFE REMOVE PREVIEW\n===================\n"
            f"Name   : {name}\nSource : {source}\nTarget : {target}\n\nPLAN   : {action}\n\nNo change is made by this preview.")

    def item_key(self,x):
        return "|".join([str(x.get("source","")),str(x.get("name","")),str(x.get("target",""))])

    def snapshot(self,items):
        return {self.item_key(x):{
            "source":x.get("source",""),"name":x.get("name",""),"target":x.get("target",""),
            "company":x.get("company",""),"signature":x.get("signature",""),"type":x.get("type",""),
            "risk":x.get("risk_label","")
        } for x in items}

    def compare_baseline(self,items):
        cur=self.snapshot(items)
        try:
            if not os.path.isfile(self.baseline_file):
                return {k:"NEW" for k in cur}
            with open(self.baseline_file,"r",encoding="utf-8") as f: base=json.load(f)
        except:
            return {k:"NEW" for k in cur}
        out={}
        for k,v in cur.items():
            if k not in base: out[k]="NEW"
            elif any(base[k].get(a)!=v.get(a) for a in ("target","company","signature","type")): out[k]="CHANGED"
            else: out[k]="UNCHANGED"
        for k in base:
            if k not in cur: out[k]="REMOVED"
        return out

    def set_baseline(self):
        allx=self.startup+self.tasks+self.services+self.processes+self.winlogon
        if not allx:
            messagebox.showwarning(APP,"Run a scan first.");return
        os.makedirs("backup",exist_ok=True)
        with open(self.baseline_file,"w",encoding="utf-8") as f:json.dump(self.snapshot(allx),f,indent=2)
        self.changes={k:"BASELINE" for k in self.snapshot(allx)}
        self.cards[5].config(text=0)
        self.populate()
        messagebox.showinfo("ZYNTRASEC // BASELINE","Current scan saved as the comparison baseline.\nFuture scans will show NEW / CHANGED / REMOVED items.")

    def show_changes(self):
        allx=self.startup+self.tasks+self.services+self.processes+self.winlogon
        if not allx:
            messagebox.showwarning(APP,"Run a scan first.");return
        win=tk.Toplevel(self);win.title("ZYNTRASEC // CHANGE MONITOR");win.geometry("1200x650");win.configure(bg=BG)
        tk.Label(win,text="BASELINE DELTA // NEW • CHANGED • REMOVED",bg=BG,fg=GREEN,font=("Consolas",15,"bold")).pack(anchor="w",padx=14,pady=10)
        tr=ttk.Treeview(win,columns=("CHANGE","SOURCE","NAME","PATH","COMPANY","SIGNATURE"),show="headings")
        for c,w in zip(tr["columns"],(110,140,200,420,180,120)):tr.heading(c,text=c);tr.column(c,width=w,anchor="w")
        tr.tag_configure("NEW",foreground=GREEN);tr.tag_configure("CHANGED",foreground=AMBER);tr.tag_configure("REMOVED",foreground=RED)
        cur=self.snapshot(allx)
        for k,state in self.changes.items():
            if state=="UNCHANGED" or state=="BASELINE":continue
            if k in cur:
                v=cur[k];tr.insert("", "end",values=(state,v["source"],v["name"],v["target"],v["company"],v["signature"]),tags=(state,))
            else:
                old=json.load(open(self.baseline_file,encoding="utf-8")).get(k,{})
                tr.insert("", "end",values=("REMOVED",old.get("source",""),old.get("name",""),old.get("target",""),old.get("company",""),old.get("signature","")),tags=("REMOVED",))
        tr.pack(fill="both",expand=True,padx=14,pady=(0,14))
        tk.Label(win,text="Baseline comparison is a change detector, not a security verdict.",bg=BG,fg=DIM,font=("Consolas",9)).pack(anchor="w",padx=14,pady=(0,10))

    def restore_center(self):
        os.makedirs("backup",exist_ok=True)
        win=tk.Toplevel(self);win.title("ZYNTRASEC // RESTORE CENTER");win.geometry("900x560");win.configure(bg=BG)
        tk.Label(win,text="BACKUP / RESTORE CENTER",bg=BG,fg=GREEN,font=("Consolas",15,"bold")).pack(anchor="w",padx=14,pady=10)
        lb=tk.Listbox(win,bg="#020502",fg=GREEN,selectbackground="#164916",font=("Consolas",10),relief="flat")
        files=sorted(os.listdir("backup"),reverse=True)
        for f in files:lb.insert("end",f)
        lb.pack(fill="both",expand=True,padx=14,pady=6)
        info=tk.Label(win,text="REG backups can be imported with Windows Registry Editor. JSON files are snapshots only.",bg=BG,fg=DIM,font=("Consolas",9))
        info.pack(anchor="w",padx=14,pady=5)
        def open_backup():
            s=lb.curselection()
            if not s:return
            path=os.path.abspath(os.path.join("backup",lb.get(s[0])))
            if os.path.exists(path):os.startfile(path)
        ttk.Button(win,text="OPEN SELECTED BACKUP",command=open_backup).pack(anchor="e",padx=14,pady=10)

    def open_location(self):
        x=self.selected()
        if not x:
            messagebox.showinfo(APP, "Select an item first.")
            return

        # Resolve a real Windows filesystem target.  Do not use the hidden
        # subprocess wrapper for Explorer because Explorer must be visible.
        candidates=[]
        raw_values=(x.get("exe"), x.get("target"), x.get("path"), x.get("command"))
        for v in raw_values:
            if not v: continue
            z=os.path.expandvars(str(v).strip())
            z=z.strip('\"')
            if z and z not in candidates: candidates.append(z)
            parsed=exe_from(str(v))
            if parsed:
                parsed=os.path.expandvars(parsed.strip().strip('\"'))
                if parsed and parsed not in candidates: candidates.insert(0,parsed)

        def explorer(arg):
            try:
                # Explorer is intentionally visible; this is the one GUI
                # process that must not use CREATE_NO_WINDOW/hidden startup.
                subprocess.Popen(["explorer.exe", arg], close_fds=True)
                return True
            except Exception:
                return False

        for p in candidates:
            # Ignore registry/protocol strings that are not filesystem paths.
            if not (os.path.isabs(p) or (len(p) >= 2 and p[1] == ':') or p.startswith('\\')):
                continue
            p=os.path.normpath(p)
            if os.path.isfile(p):
                if explorer('/select,' + p): return
            if os.path.isdir(p):
                if explorer(p): return
            parent=os.path.dirname(p)
            if parent and os.path.isdir(parent):
                if explorer(parent): return

        messagebox.showwarning(APP, "OPEN LOCATION\n\nNo valid Windows file/folder path was found for the selected item.")

    def backup(self):
        os.makedirs("backup",exist_ok=True);ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"backup\\CONTROL_NODE_{ts}.json","w",encoding="utf-8") as f:json.dump({"startup":self.startup,"tasks":self.tasks,"services":self.services,"processes":self.processes,"winlogon":self.winlogon},f,indent=2,default=str)
        for rn in ("HKCU","HKLM"):_zyntrasec_run(f'reg export "{rn}\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" "backup\\{ts}_{rn}_RUN.reg" /y',shell=True,capture_output=True)
        messagebox.showinfo(APP,"Backup created.")

if __name__=="__main__":
    _zyntrasec_require_admin()
    App().mainloop()
