import os, sys, time, subprocess, json, secrets, hashlib, ctypes
from pathlib import Path
import cv2
import numpy as np
try:
    from pywinauto import Desktop, mouse
except Exception:
    Desktop = None
    mouse = None

PROGRAMDATA = Path(os.getenv('PROGRAMDATA', str(Path.home())))
DATA_DIR = PROGRAMDATA / 'PCYBI' / 'SecurityData'
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    os.system(f'attrib +h +s "{DATA_DIR.parent}" >nul 2>&1')
except Exception:
    pass
MODEL = DATA_DIR / 'face_model.yml'
PASSWORD_FILE = DATA_DIR / 'master_password.json'
DATA_DIR.mkdir(parents=True, exist_ok=True)


def resource_path(name):
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    for p in (base/'data'/name, base/name, Path(__file__).resolve().parent/'data'/name):
        if p.exists(): return p
    return None


def detector():
    p = resource_path('haarcascade_frontalface_default.xml')
    if not p: raise FileNotFoundError('Face detector missing')
    d = cv2.CascadeClassifier(str(p))
    if d.empty(): raise RuntimeError('Face detector could not be loaded')
    return d


def eye_detector():
    p = resource_path('haarcascade_eye.xml')
    if not p: raise FileNotFoundError('Eye detector missing')
    d = cv2.CascadeClassifier(str(p))
    if d.empty(): raise RuntimeError('Eye detector could not be loaded')
    return d


def camera_window():
    if Desktop is None: return None
    try:
        for w in Desktop(backend='uia').windows():
            if 'camera' in (w.window_text() or '').strip().lower(): return w
    except Exception: pass
    return None


def open_camera():
    subprocess.Popen(['explorer.exe','microsoft.windows.camera:'], shell=False)


def close_camera():
    w = camera_window()
    if w:
        try: w.close(); return
        except Exception: pass
        try: w.set_focus(); w.type_keys('%{F4}')
        except Exception: pass


def _win32_topmost(hwnd, top=True):
    try:
        user32=ctypes.windll.user32
        HWND_TOPMOST=-1
        HWND_NOTOPMOST=-2
        SWP_NOSIZE=0x0001
        SWP_NOMOVE=0x0002
        SWP_NOACTIVATE=0x0010
        flags=SWP_NOSIZE|SWP_NOMOVE|SWP_NOACTIVATE
        user32.SetWindowPos(int(hwnd), HWND_TOPMOST if top else HWND_NOTOPMOST, 0,0,0,0, flags)
        return True
    except Exception:
        return False

def focus_camera():
    w = camera_window()
    if not w: return None
    for a in ('restore','maximize','set_focus'):
        try: getattr(w,a)()
        except Exception: pass
    try:
        hwnd=int(w.handle)
        _win32_topmost(hwnd, True)
        user32=ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        _win32_topmost(hwnd, True)
    except Exception: pass
    return w


def shutter():
    w = focus_camera()
    if not w: return False
    try:
        for c in w.descendants(control_type='Button'):
            name=(c.window_text() or '').strip().lower()
            if name in ('take photo','take picture') or name.startswith('take photo ') or name.startswith('take picture '):
                try: c.invoke()
                except Exception: c.click_input()
                return True
    except Exception: pass
    try:
        w.set_focus(); w.type_keys('{SPACE}'); return True
    except Exception: pass
    if mouse:
        try:
            r=w.rectangle()
            for rx,ry in ((.955,.52),(.955,.50),(.90,.52),(.88,.50)):
                mouse.click(coords=(int(r.left+r.width()*rx), int(r.top+r.height()*ry)))
                time.sleep(.25)
            return True
        except Exception: pass
    return False


def camera_roll_snapshot():
    folder=Path.home()/'Pictures'/'Camera Roll'
    if not folder.exists(): return set()
    try:
        return {p.resolve() for p in folder.iterdir() if p.suffix.lower() in ('.jpg','.jpeg','.png','.bmp')}
    except OSError:
        return set()

def newest_photo(before_files):
    folder=Path.home()/'Pictures'/'Camera Roll'
    if not folder.exists(): return None
    out=[]
    try:
        for p in folder.iterdir():
            if p.suffix.lower() in ('.jpg','.jpeg','.png','.bmp') and p.resolve() not in before_files:
                out.append(p)
    except OSError:
        return None
    if not out: return None
    return max(out,key=lambda p:p.stat().st_mtime)


def capture(status, overlay=None):
    # Keep the PCYBI fullscreen overlay active so the desktop/taskbar never becomes visible.
    # Windows Camera is temporarily placed above the PCYBI overlay for shutter interaction.
    if overlay: overlay(True)
    status('OPENING WINDOWS CAMERA...')
    open_camera()
    deadline=time.time()+10
    w=None
    while time.time()<deadline:
        w=focus_camera()
        if w: break
        time.sleep(.35)
    if not w:
        if overlay: overlay(True)
        return None
    time.sleep(1.5)
    before_files=camera_roll_snapshot()
    for attempt in range(1,7):
        status(f'AUTO CAPTURE #{attempt} → CAMERA SHUTTER...')
        shutter()
        end=time.time()+7
        while time.time()<end:
            p=newest_photo(before_files)
            if p:
                if overlay: overlay(True)
                return p
            time.sleep(.25)
        focus_camera(); time.sleep(.4)
    if overlay: overlay(True)
    return None


def detect_face(path,d):
    img=cv2.imread(str(path))
    if img is None: return None
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    candidates=[]
    # More tolerant detection for different lighting, beard, hairstyle and camera exposure.
    for g in (gray, cv2.equalizeHist(gray)):
        for scale, neighbors, size in ((1.05,3,(60,60)),(1.08,4,(70,70)),(1.12,4,(90,90))):
            try:
                faces=d.detectMultiScale(g,scaleFactor=scale,minNeighbors=neighbors,minSize=size)
                candidates.extend(list(faces))
            except Exception:
                pass
    if not candidates: return None
    x,y,w,h=max(candidates,key=lambda r:r[2]*r[3])
    # Add a small margin so the recognizer gets stable facial context.
    mx,my=int(w*0.10),int(h*0.10)
    x=max(0,x-mx); y=max(0,y-my); w=min(img.shape[1]-x,w+2*mx); h=min(img.shape[0]-y,h+2*my)
    face=gray[y:y+h,x:x+w]
    return cv2.equalizeHist(cv2.resize(face,(200,200),interpolation=cv2.INTER_AREA))



def detect_face_info(path,d):
    img=cv2.imread(str(path))
    if img is None: return None
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    candidates=[]
    for g in (gray, cv2.equalizeHist(gray)):
        for scale, neighbors, size in ((1.05,3,(60,60)),(1.08,4,(70,70)),(1.12,4,(90,90))):
            try: candidates.extend(list(d.detectMultiScale(g,scaleFactor=scale,minNeighbors=neighbors,minSize=size)))
            except Exception: pass
    if not candidates: return None
    x,y,w,h=max(candidates,key=lambda r:r[2]*r[3]); mx,my=int(w*.10),int(h*.10)
    x=max(0,x-mx); y=max(0,y-my); w=min(img.shape[1]-x,w+2*mx); h=min(img.shape[0]-y,h+2*my)
    face=gray[y:y+h,x:x+w]
    return cv2.equalizeHist(cv2.resize(face,(200,200),interpolation=cv2.INTER_AREA)), (x,y,w,h), img.shape[1], img.shape[0]

def train(faces):
    rec=cv2.face.LBPHFaceRecognizer_create()
    images=[np.ascontiguousarray(f,dtype=np.uint8) for f in faces]
    labels=np.zeros(len(images),dtype=np.int32)
    rec.train(images,labels)
    rec.write(str(MODEL))

def cleanup_setup_photo(path):
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


def verify(face, threshold=65.0):
    # Stricter threshold than the legacy 90 setting. The model contains 5
    # registration samples, so normal lighting/appearance variation remains
    # supported while making unrelated faces much less likely to pass.
    rec=cv2.face.LBPHFaceRecognizer_create(); rec.read(str(MODEL))
    label,conf=rec.predict(np.ascontiguousarray(face,dtype=np.uint8))
    return label==0 and conf<=threshold, conf


def eye_count(face_gray, eyes):
    h,w=face_gray.shape[:2]
    upper=face_gray[:max(1,int(h*0.62)), :]
    try:
        found=eyes.detectMultiScale(upper, 1.08, 4, minSize=(18,18))
        return len(found)
    except Exception:
        return 0


def blink_sequence_ok(open_face, closed_face, open2_face, eyes):
    # Require an open -> closed -> open sequence. A single still photo shown
    # to the camera cannot satisfy both open and closed states.
    a=eye_count(open_face, eyes)
    b=eye_count(closed_face, eyes)
    c=eye_count(open2_face, eyes)
    return a >= 1 and b == 0 and c >= 1




# ---------------- SECURITY STATE / AUDIT ----------------
AUTH_STATE = DATA_DIR / 'auth_state.json'
AUDIT_LOG = DATA_DIR / 'security_audit.log'
AUDIT_STATE = DATA_DIR / 'security_audit_state.json'

def _atomic_json(path, obj):
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2), encoding='utf-8')
    os.replace(tmp, path)

def load_auth_state():
    try:
        obj=json.loads(AUTH_STATE.read_text(encoding='utf-8'))
        return {'failures':int(obj.get('failures',0)), 'cooldown_until':float(obj.get('cooldown_until',0))}
    except Exception:
        return {'failures':0,'cooldown_until':0.0}

def save_auth_state(state):
    _atomic_json(AUTH_STATE, {'failures':int(state.get('failures',0)), 'cooldown_until':float(state.get('cooldown_until',0))})

def clear_auth_state():
    save_auth_state({'failures':0,'cooldown_until':0})

def audit(event, detail=''):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        prev='0'*64
        try:
            prev=json.loads(AUDIT_STATE.read_text(encoding='utf-8')).get('last_hash',prev)
        except Exception:
            pass
        line=f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}|{event}|{detail}|{prev}"
        digest=hashlib.sha256(line.encode('utf-8')).hexdigest()
        with open(AUDIT_LOG,'a',encoding='utf-8') as f:
            f.write(f"{line}|{digest}\n")
        _atomic_json(AUDIT_STATE, {'last_hash':digest})
    except Exception:
        pass

def audit_verify():
    try:
        if not AUDIT_LOG.exists(): return True, 0
        prev='0'*64; count=0
        for raw in AUDIT_LOG.read_text(encoding='utf-8').splitlines():
            parts=raw.rsplit('|',1)
            if len(parts)!=2: return False,count
            line,digest=parts
            if not line.endswith('|'+prev): return False,count
            if hashlib.sha256(line.encode('utf-8')).hexdigest()!=digest: return False,count
            prev=digest; count+=1
        return True,count
    except Exception:
        return False,0


def set_master_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 300_000)
    PASSWORD_FILE.write_text(json.dumps({
        'algorithm':'PBKDF2-HMAC-SHA256', 'iterations':300000,
        'salt':salt.hex(), 'hash':digest.hex()
    }), encoding='utf-8')
    try: os.chmod(PASSWORD_FILE, 0o600)
    except Exception: pass
    audit('MASTER_PASSWORD_SET')


def has_master_password():
    return PASSWORD_FILE.exists()


def verify_master_password(password):
    try:
        obj=json.loads(PASSWORD_FILE.read_text(encoding='utf-8'))
        salt=bytes.fromhex(obj['salt'])
        expected=bytes.fromhex(obj['hash'])
        digest=hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(obj.get('iterations',300000)))
        return secrets.compare_digest(digest, expected)
    except Exception:
        return False


# ---------------- LIVE VIDEO AUTHENTICATION ----------------
def open_live_camera(index=0):
    cap=cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap=cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError('Webcam could not be opened')
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
    except Exception:
        pass
    return cap

def _live_window_setup(title='PCYBI // LIVE FACE VERIFICATION'):
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    try:
        cv2.setWindowProperty(title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    except Exception:
        try: cv2.resizeWindow(title, 1100, 700)
        except Exception: pass
    try: cv2.setWindowProperty(title, cv2.WND_PROP_TOPMOST, 1)
    except Exception: pass
    return title

def _draw_live(frame, instruction, countdown=None, ok_text=None):
    img=frame.copy()
    h,w=img.shape[:2]
    overlay=img.copy()
    cv2.rectangle(overlay,(0,0),(w,105),(0,0,0),-1)
    img=cv2.addWeighted(overlay,0.55,img,0.45,0)
    cv2.putText(img, 'PCYBI // LIVE AUTHENTICATION',(30,38),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,255,102),2,cv2.LINE_AA)
    cv2.putText(img, instruction,(30,78),cv2.FONT_HERSHEY_SIMPLEX,0.85,(255,255,255),2,cv2.LINE_AA)
    if countdown is not None:
        cv2.putText(img,str(countdown),(w-100,85),cv2.FONT_HERSHEY_SIMPLEX,2.2,(0,255,102),4,cv2.LINE_AA)
    if ok_text:
        cv2.putText(img,ok_text,(30,h-35),cv2.FONT_HERSHEY_SIMPLEX,0.75,(0,255,102),2,cv2.LINE_AA)
    return img

def live_collect_pose(det, instruction, seconds=2.0, settle=1.0, title='PCYBI // LIVE FACE SETUP'):
    cap=open_live_camera(); _live_window_setup(title)
    try:
        start=time.time(); deadline=start+settle+seconds; last_face=None
        while time.time()<deadline:
            ok,frame=cap.read()
            if not ok: continue
            remaining=max(0, int(deadline-time.time())+1)
            display=_draw_live(frame,instruction,remaining)
            cv2.imshow(title,display)
            if cv2.waitKey(1)&0xFF==27: return None
            if time.time() >= start+settle:
                info=detect_face_info_frame(frame,det)
                if info: last_face=info[0]
        return last_face
    finally:
        cap.release(); cv2.destroyWindow(title)
        try: cv2.destroyAllWindows()
        except Exception: pass

def detect_face_info_frame(img,d):
    if img is None: return None
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    candidates=[]
    for g in (gray,cv2.equalizeHist(gray)):
        for scale,neighbors,size in ((1.05,3,(60,60)),(1.08,4,(70,70)),(1.12,4,(90,90))):
            try: candidates.extend(list(d.detectMultiScale(g,scaleFactor=scale,minNeighbors=neighbors,minSize=size)))
            except Exception: pass
    if not candidates: return None
    x,y,w,h=max(candidates,key=lambda r:r[2]*r[3]); mx,my=int(w*.10),int(h*.10)
    x=max(0,x-mx); y=max(0,y-my); w=min(img.shape[1]-x,w+2*mx); h=min(img.shape[0]-y,h+2*my)
    face=cv2.cvtColor(img[y:y+h,x:x+w],cv2.COLOR_BGR2GRAY)
    return cv2.equalizeHist(cv2.resize(face,(200,200),interpolation=cv2.INTER_AREA)),(x,y,w,h),img.shape[1],img.shape[0]

def live_authenticate(det, eyes, challenge=None, verify_fn=None, seconds=3.5, title='PCYBI // LIVE FACE VERIFICATION'):
    """Passive live-video authentication.

    No mandatory blink/head-direction challenge. We collect consecutive webcam
    frames, require repeated identity matches, and apply a conservative
    temporal-motion heuristic so a single static image is less likely to pass.
    This is a software heuristic, not hardware-backed anti-spoofing.
    """
    if verify_fn is None:
        verify_fn = verify
    cap = open_live_camera()
    _live_window_setup(title)
    records=[]
    start=time.time()
    deadline=start+seconds
    previous_roi=None
    motion_scores=[]
    try:
        while time.time() < deadline:
            ok, frame = cap.read()
            if not ok:
                continue
            info = detect_face_info_frame(frame, det)
            matched=False; conf=999.0; face=None; box=None
            if info:
                face, box, fw, fh = info
                matched, conf = verify_fn(face, threshold=65.0) if verify_fn is verify else verify_fn(face)
                x,y,w,h=box
                roi=frame[max(0,y):min(frame.shape[0],y+h), max(0,x):min(frame.shape[1],x+w)]
                if roi.size:
                    gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
                    gray=cv2.resize(gray,(96,96),interpolation=cv2.INTER_AREA)
                    if previous_roi is not None:
                        motion_scores.append(float(cv2.absdiff(gray,previous_roi).mean()))
                    previous_roi=gray
                records.append((face,box,conf,matched))
            remain=max(0,int(deadline-time.time())+1)
            display=_draw_live(frame,'LOOK AT THE CAMERA — HOLD NATURALLY',remain,
                               'LIVE VIDEO — checking identity and natural movement')
            if info:
                x,y,w,h=info[1]
                cv2.rectangle(display,(x,y),(x+w,y+h),(0,255,102),2)
            cv2.imshow(title,display)
            if cv2.waitKey(1)&0xFF==27:
                return None
        valid=[r for r in records if r[3] and r[2] <= 65.0]
        # Require repeated identity matches, but tolerate normal webcam frame drops.
        identity_ok = len(valid) >= 6 and len(valid) >= max(6, int(len(records)*0.55))
        # Use a gentler temporal-motion check. Small natural movements are common
        # and some cameras produce very stable frames, so motion is a supporting
        # signal rather than a hard gate.
        if len(motion_scores) >= 4:
            moving=sum(1 for m in motion_scores if m >= 0.45)
            motion_ok = moving >= 2 or (max(motion_scores)-min(motion_scores)) >= 0.35
        else:
            motion_ok=True
        live_ok = identity_ok and motion_ok
        return live_ok, valid, records
    finally:
        cap.release()
        try: cv2.destroyWindow(title)
        except Exception: pass
        try: cv2.destroyAllWindows()
        except Exception: pass

