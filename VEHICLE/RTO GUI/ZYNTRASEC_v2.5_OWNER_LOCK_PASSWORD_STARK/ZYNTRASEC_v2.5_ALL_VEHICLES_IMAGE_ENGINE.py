#!/usr/bin/env python3
# ZYNTRASEC SECURITY
# v2.5 ALL VEHICLES IMAGE ENGINE BUILD - Vehicle Information Dashboard GUI
# FINAL FIXED - IMAGE VISIBLE ON SCREEN

import os,re,json,sqlite3,html,time,threading,random,hashlib,base64,getpass,ctypes,ctypes.wintypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from urllib.parse import urlparse,parse_qs,quote

HOST=os.getenv("HOST","127.0.0.1")
PORT=int(os.getenv("PORT","8000"))
RAPIDAPI_KEY=os.getenv("RAPIDAPI_KEY","").strip()

APIS=[
 {"name":"Vehicle Info Free API","url":"https://vehicleinfobyterabaap.vercel.app/lookup","param":"rc","headers":{}},
 {"name":"RTO Search Free","url":"https://www.rtosearch.in/api/get_details.php","param":"vehicle_no","headers":{}},
 {"name":"RTO Vehicle Info (RapidAPI)","url":"https://rto-vehicle-information-india-api.p.rapidapi.com/rc_v2.php","param":"registration_no",
  "headers":{"x-rapidapi-host":"rto-vehicle-information-india-api.p.rapidapi.com","Content-Type":"application/json"}}
]

SENSITIVE=("father","address","phone","mobile","email","engine","chassis","aadhar","aadhaar","bank","financier")

AUTH_FILE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"zyntrasec_owner.sec")
AUTH_TOKEN=None; AUTH_TOKEN_LOCK=threading.Lock(); AUTH_FAILS=0; AUTH_LOCKOUT_UNTIL=0.0
AUTH_MAX_FAILS=5; AUTH_LOCKOUT_SECONDS=60
class DATA_BLOB(ctypes.Structure):
 _fields_=[("cbData",ctypes.wintypes.DWORD),("pbData",ctypes.POINTER(ctypes.c_byte))]
def _dpapi_protect(data):
 if os.name!="nt": raise RuntimeError("Windows required")
 fn=ctypes.windll.crypt32.CryptProtectData; fn.argtypes=[ctypes.POINTER(DATA_BLOB),ctypes.wintypes.LPCWSTR,ctypes.POINTER(DATA_BLOB),ctypes.c_void_p,ctypes.c_void_p,ctypes.wintypes.DWORD,ctypes.POINTER(DATA_BLOB)];fn.restype=ctypes.wintypes.BOOL
 buf=(ctypes.c_byte*len(data)).from_buffer_copy(data); inp=DATA_BLOB(len(data),buf); out=DATA_BLOB()
 if not fn(ctypes.byref(inp),"ZYNTRASEC Owner Security",None,None,None,0,ctypes.byref(out)): raise ctypes.WinError()
 try:return ctypes.string_at(out.pbData,out.cbData)
 finally:ctypes.windll.kernel32.LocalFree(out.pbData)
def _dpapi_unprotect(data):
 if os.name!="nt": raise RuntimeError("Windows required")
 fn=ctypes.windll.crypt32.CryptUnprotectData; fn.argtypes=[ctypes.POINTER(DATA_BLOB),ctypes.POINTER(ctypes.wintypes.LPWSTR),ctypes.POINTER(DATA_BLOB),ctypes.c_void_p,ctypes.c_void_p,ctypes.wintypes.DWORD,ctypes.POINTER(DATA_BLOB)];fn.restype=ctypes.wintypes.BOOL
 buf=(ctypes.c_byte*len(data)).from_buffer_copy(data); inp=DATA_BLOB(len(data),buf); out=DATA_BLOB()
 if not fn(ctypes.byref(inp),None,None,None,None,0,ctypes.byref(out)): raise ctypes.WinError()
 try:return ctypes.string_at(out.pbData,out.cbData)
 finally:ctypes.windll.kernel32.LocalFree(out.pbData)
def _machine_identity():
 guid=""
 try:
  import winreg
  with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Cryptography") as k: guid=str(winreg.QueryValueEx(k,"MachineGuid")[0])
 except Exception: pass
 return hashlib.sha256((guid+"|"+os.environ.get("USERNAME","")+"|"+os.environ.get("COMPUTERNAME","")).encode()).hexdigest()
def _save_owner_password(password):
 salt=os.urandom(32); h=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,250000,32)
 rec={"v":1,"machine":_machine_identity(),"salt":base64.b64encode(salt).decode(),"hash":base64.b64encode(h).decode()}
 tmp=AUTH_FILE+".tmp"
 with open(tmp,"wb") as f:f.write(base64.b64encode(_dpapi_protect(json.dumps(rec,separators=(",",":")).encode())))
 os.replace(tmp,AUTH_FILE)
def _load_owner():
 with open(AUTH_FILE,"rb") as f:return json.loads(_dpapi_unprotect(base64.b64decode(f.read())).decode())
def _verify_owner(password):
 global AUTH_FAILS,AUTH_LOCKOUT_UNTIL
 now=time.time()
 if now<AUTH_LOCKOUT_UNTIL:return False,int(AUTH_LOCKOUT_UNTIL-now)
 try:
  rec=_load_owner()
  if rec.get("machine")!=_machine_identity():return False,"machine_mismatch"
  actual=hashlib.pbkdf2_hmac("sha256",password.encode(),base64.b64decode(rec["salt"]),250000,32)
  if actual==base64.b64decode(rec["hash"]):AUTH_FAILS=0;return True,0
 except Exception:return False,"security_error"
 AUTH_FAILS+=1
 if AUTH_FAILS>=AUTH_MAX_FAILS:AUTH_FAILS=0;AUTH_LOCKOUT_UNTIL=now+AUTH_LOCKOUT_SECONDS;return False,AUTH_LOCKOUT_SECONDS
 return False,AUTH_MAX_FAILS-AUTH_FAILS
def _new_session():return base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
def _is_auth(h):
 if not AUTH_TOKEN:return False
 return any(k.strip()=="ZYNTRASEC_SESSION" and v==AUTH_TOKEN for k,_,v in (x.partition("=") for x in h.headers.get("Cookie","").split(";")))
def _security_setup():
 if os.name!="nt":raise RuntimeError("ZYNTRASEC owner lock requires Windows")
 if os.path.exists(AUTH_FILE):
  rec=_load_owner()
  if rec.get("machine")!=_machine_identity():raise RuntimeError("Owner security belongs to another Windows machine/user")
  return
 # Owner password is provisioned by the owner of this distribution.
 # Only the salted PBKDF2 verifier is embedded; the plaintext password is not stored.
 _PROVISIONED_SALT=base64.b64decode("lv8OXnnErxHHuabIfhakl3D0TVotXMAmaoWqAvCA0rY=")
 _PROVISIONED_HASH=base64.b64decode("isImYmnGOYN4K/UZMSlu0GAGAo94oczG6cFNPJzp918=")
 rec={"v":1,"machine":_machine_identity(),"salt":base64.b64encode(_PROVISIONED_SALT).decode(),"hash":base64.b64encode(_PROVISIONED_HASH).decode()}
 tmp=AUTH_FILE+".tmp"
 with open(tmp,"wb") as f:f.write(base64.b64encode(_dpapi_protect(json.dumps(rec,separators=(",",":")).encode())))
 os.replace(tmp,AUTH_FILE)
 print("\nZYNTRASEC owner security initialized for this Windows user/machine.")
 print("Use the owner password supplied with your secured package.")
 return

def valid_rc(rc):
 s=re.sub(r"[^A-Z0-9]","",rc.upper())
 return bool(re.match(r"^(AP|AR|AS|BR|CG|GA|GJ|HR|HP|JK|JH|KA|KL|MP|MH|MN|ML|MZ|NL|OD|OR|PB|RJ|SK|TN|TR|UP|WB|AN|CH|DN|DD|DL|LD|PY|TS|TG|LA)\d{1,2}[A-Z]{1,3}\d{4}$",s))

def flatten(x,p=""):
 out={}
 if isinstance(x,dict):
  for k,v in x.items():
   n=f"{p}_{k}" if p else str(k)
   if isinstance(v,(dict,list)):out.update(flatten(v,n))
   else:out[n]=v
 elif isinstance(x,list):
  for i,v in enumerate(x):
   n=f"{p}_{i}" if p else str(i)
   if isinstance(v,(dict,list)):out.update(flatten(v,n))
   else:out[n]=v
 return out

def is_sensitive(k):
 k=str(k).lower().replace("-","_")
 return any(w in k for w in SENSITIVE)

def safe_result(raw):
 out={}
 for k,v in flatten(raw).items():
  out[k.lower()]="[MASKED — sensitive field]" if is_sensitive(k) else v
 return out

def api_get(api,rc):
 headers=dict(api["headers"])
 if api["name"].startswith("RTO Vehicle Info"):
  if not RAPIDAPI_KEY:return {"error":"RapidAPI key not configured"}
  headers["x-rapidapi-key"]=RAPIDAPI_KEY
 url=api["url"]+"?"+api["param"]+"="+quote(rc)
 try:
  with urlopen(Request(url,headers=headers,method="GET"),timeout=12) as r:
   if r.status!=200:return {"error":f"HTTP {r.status}"}
   body=r.read().decode("utf-8","replace")
   try:return json.loads(body)
   except:return {"error":"API returned non-JSON data"}
 except HTTPError as e:return {"error":f"HTTP {e.code}"}
 except URLError as e:return {"error":f"Connection error: {e.reason}"}
 except TimeoutError:return {"error":"Timeout"}
 except Exception as e:return {"error":str(e)}

def lookup(rc):
 rc=re.sub(r"[^A-Z0-9]","",rc.upper())
 
 for api in APIS:
  raw=api_get(api,rc)
  if isinstance(raw,dict) and "error" not in raw and raw:
   payload=raw
   for key in ("data","result","vehicle","vehicle_details","details"):
    if isinstance(raw.get(key),dict) and raw.get(key):
     payload=raw[key]; break
   return {"ok":True,"api":api["name"],"data":safe_result(payload),"timestamp":datetime.now().isoformat(timespec="seconds")}
  elif isinstance(raw,list) and raw:
   return {"ok":True,"api":api["name"],"data":safe_result({"results":raw}),"timestamp":datetime.now().isoformat(timespec="seconds")}
 
 return {"ok":False,"error":"All APIs failed. Check your internet connection.","rapidapi_configured":bool(RAPIDAPI_KEY)}

DB="zyntrasec_gui_history.db"
def initdb():
 c=sqlite3.connect(DB)
 c.execute("CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT,rc TEXT,api TEXT,status TEXT,created TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS favorites(id INTEGER PRIMARY KEY AUTOINCREMENT,rc TEXT UNIQUE,created TEXT)")
 c.commit();c.close()
def history():
 c=sqlite3.connect(DB);r=c.execute("SELECT rc,api,status,created FROM history ORDER BY id DESC LIMIT 50").fetchall();c.close()
 return [{"rc":a,"api":b,"status":d,"created":e} for a,b,d,e in r]
def add_history(rc,api,status):
 c=sqlite3.connect(DB);c.execute("INSERT INTO history(rc,api,status,created) VALUES(?,?,?,?)",(rc,api,status,datetime.now().isoformat(timespec="seconds")));c.commit();c.close()
def favorites():
 c=sqlite3.connect(DB);r=c.execute("SELECT rc,created FROM favorites ORDER BY id DESC").fetchall();c.close()
 return [{"rc":a,"created":b} for a,b in r]
def add_favorite(rc):
 c=sqlite3.connect(DB);c.execute("INSERT OR IGNORE INTO favorites(rc,created) VALUES(?,?)",(rc,datetime.now().isoformat(timespec="seconds")));c.commit();c.close()

IMAGE_CACHE = {}
IMAGE_CACHE_TTL = 6 * 3600
IMAGE_CACHE_LOCK = threading.Lock()



def clean_vehicle_model(raw_model, raw_make=""):
    """Turn noisy RTO model strings into image-search-friendly model names."""
    s = str(raw_model or "").strip()
    if not s:
        return ""
    # Remove registration/variant noise commonly returned by RTO sources.
    s = re.sub(r'\([^)]*\)', ' ', s)          # e.g. LIMITED(0)
    s = re.sub(r'\bLIMITED\b', ' ', s, flags=re.I)
    s = re.sub(r'\bLTD\.?\b', ' ', s, flags=re.I)
    s = re.sub(r'\bPRIVATE\b', ' ', s, flags=re.I)
    s = re.sub(r'\bPVT\.?\b', ' ', s, flags=re.I)
    s = re.sub(r'\bINDIA\b', ' ', s, flags=re.I)
    s = re.sub(r'\bAUTOMOBILES?\b', ' ', s, flags=re.I)
    s = re.sub(r'\bAT\b', ' ', s, flags=re.I)
    s = re.sub(r'\bMT\b', ' ', s, flags=re.I)
    s = re.sub(r'\bCVT\b', ' ', s, flags=re.I)
    s = re.sub(r'\bAMT\b', ' ', s, flags=re.I)
    s = re.sub(r'[_|]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip(' -_/')
    return s


def image_search_terms(make, model, body_type=""):
    """Generate several safe, model-focused queries for cars, bikes, scooters, trucks and buses."""
    make = re.sub(r'\s+', ' ', str(make or '')).strip()
    model = clean_vehicle_model(model, make)
    body = re.sub(r'\s+', ' ', str(body_type or '')).strip()
    terms = []
    base = " ".join(x for x in [make, model] if x).strip()
    if base:
        terms += [
            f'"{base}" vehicle',
            f'{base} car' if not re.search(r'bike|motorcycle|scooter', body, re.I) else f'{base} motorcycle',
            f'{base} India'
        ]
    if model:
        terms += [f'"{model}"', f'{model} official']
    # De-duplicate while preserving order.
    seen=set()
    return [q for q in terms if q and not (q.lower() in seen or seen.add(q.lower()))]

def vehicle_image(query, manufacturer=None, model=None):
    """Find model-relevant public vehicle images. Returns several ranked candidates."""
    query = str(query or "").strip()
    manufacturer = str(manufacturer or "").strip()
    model = str(model or "").strip()

    def clean(v):
        v = re.sub(r"\([^)]*\)", " ", v or "", flags=re.I)
        v = re.sub(r"\b(MOTORCYCLE AND SCOOTER INDIA|AUTOMOBILES?|MOTORCYCLE|SCOOTER|INDIA|PRIVATE|PUBLIC|LIMITED|LTD|PVT|CORP|CORPORATION|COMPANY)\b", " ", v, flags=re.I)
        return re.sub(r"\s+", " ", v).strip()

    brands = ["Royal Enfield","Maruti Suzuki","Mercedes-Benz","Mercedes Benz","Land Rover","Ashok Leyland","Force Motors","Mahindra","Volkswagen","Hero","Honda","Bajaj","TVS","Yamaha","Suzuki","Tata","Hyundai","Kia","Toyota","Ola","Ather","KTM","BMW","Audi","Skoda","Nissan","Renault","MG","Jeep","Isuzu","Volvo","Jawa","Aprilia","Piaggio","Lexus","Porsche","Ducati","Triumph","Benelli","Harley Davidson"]
    aliases = {
        "splendor pro":"Hero Splendor Pro", "splendor":"Hero Splendor", "maestro":"Hero Maestro",
        "maestro edge":"Hero Maestro Edge", "activa":"Honda Activa", "activa 3g":"Honda Activa 3G",
        "activa 4g":"Honda Activa 4G", "activa 5g":"Honda Activa 5G", "activa 6g":"Honda Activa 6G",
        "livo":"Honda Livo", "livo drum":"Honda Livo Drum", "shine":"Honda Shine",
        "passion":"Hero Passion", "passion pro":"Hero Passion Pro", "hf deluxe":"Hero HF Deluxe",
        "jupiter":"TVS Jupiter", "ntorq":"TVS Ntorq", "apache":"TVS Apache", "access":"Suzuki Access",
        "pulsar":"Bajaj Pulsar", "platina":"Bajaj Platina", "chetak":"Bajaj Chetak",
        "fzs":"Yamaha FZS", "fz":"Yamaha FZ", "ray zr":"Yamaha Ray ZR",
        "swift":"Maruti Suzuki Swift", "baleno":"Maruti Suzuki Baleno", "alto":"Maruti Suzuki Alto",
        "wagon r":"Maruti Suzuki Wagon R", "brezza":"Maruti Suzuki Brezza", "nexon":"Tata Nexon",
        "punch":"Tata Punch", "tiago":"Tata Tiago", "thar":"Mahindra Thar", "scorpio":"Mahindra Scorpio",
    }
    low = manufacturer.lower()
    brand = next((b for b in sorted(brands,key=len,reverse=True) if b.lower() in low), "")
    clean_model = clean(model)
    qclean = clean(query)
    if not clean_model or clean_model.lower() in {"n/a","na","unknown","-"}:
        clean_model = qclean
    # Remove legal maker wording and known brand from model text.
    if brand:
        clean_model = re.sub(r"\b"+re.escape(brand)+r"\b", " ", clean_model, flags=re.I)
        clean_model = re.sub(r"\s+", " ", clean_model).strip()
    # If model itself is a known alias, use the canonical model phrase.
    canonical = aliases.get(clean_model.lower(), "")
    if canonical:
        if not brand: brand = canonical.split()[0]
        clean_model = " ".join(canonical.split()[1:])
    if not brand and clean_model:
        for b in sorted(brands,key=len,reverse=True):
            if re.search(r"\b"+re.escape(b)+r"\b", clean_model, re.I):
                brand=b; clean_model=re.sub(r"\b"+re.escape(b)+r"\b"," ",clean_model,flags=re.I).strip(); break

    mlow=clean_model.lower()
    body_type = "motorcycle"
    if any(x in mlow for x in ("scooter","activa","maestro","jupiter","access","chetak","dio","ntorq","ray")): body_type="scooter"
    elif any(x in mlow for x in ("car","sedan","hatchback","suv","swift","baleno","creta","nexon","thar","scorpio","punch","tiago","alto","brezza","wagon r")): body_type="car"

    identity = " ".join(x for x in [brand, clean_model] if x).strip()
    search_query = " ".join(x for x in [identity, body_type] if x).strip() or query or "vehicle"
    cache_key = re.sub(r"\s+"," ",identity.lower()).strip()
    now=time.time()
    with IMAGE_CACHE_LOCK:
        cached=IMAGE_CACHE.get(cache_key)
        if cached and now-cached[0] < IMAGE_CACHE_TTL:
            return cached[1]

    model_tokens=[x for x in re.sub(r"[^a-z0-9]+"," ",clean_model.lower()).split() if len(x)>=2]
    brand_tokens=[x for x in re.sub(r"[^a-z0-9]+"," ",brand.lower()).split() if len(x)>=2]
    bad={"person","portrait","painting","book","wine","flower","animal","aircraft","ship","train","map","logo","flag","pdf","cecil","dreeme","toy","miniature","drawing","illustration"}

    def relevance(title, url="", query_used=""):
        hay=re.sub(r"[^a-z0-9]+"," ",(str(title)+" "+str(url)).lower()); words=set(hay.split()); score=0
        # Model is the strongest identity signal.
        for t in model_tokens:
            if t in words: score += 18
        if len(model_tokens)>=2 and " ".join(model_tokens) in hay: score += 35
        for t in brand_tokens:
            if t in words: score += 9
        if brand and brand.lower() in hay: score += 12
        if body_type in hay: score += 4
        if words & bad: score -= 80
        # Reward image URLs/titles that look like actual vehicle photos.
        if any(x in hay for x in ("motorcycle","scooter","vehicle","car","bike")): score += 4
        return score

    candidates=[]
    queries=[]
    if identity:
        queries += [f'"{identity}" {body_type}', f'{identity} India {body_type}', f'{identity} {body_type} photo']
    elif clean_model:
        queries += [f'"{clean_model}" {body_type}', f'{clean_model} India {body_type}']
    else: queries=[search_query]

    def add(u,title,source,query_used):
        if not (u and re.match(r"^https?://",u,re.I)): return
        score=relevance(title,u,query_used)
        candidates.append((score,u,title,source))

    # Wikimedia: use short retries and stop hammering it after a connection reset.
    # Some Windows networks/proxies forcibly reset Wikimedia connections (WinError 10054).
    wikimedia_ok = True
    try:
        for sq in queries[:3]:
            if not wikimedia_ok:
                break
            api_url=("https://commons.wikimedia.org/w/api.php?action=query&format=json&origin=*"
                     "&generator=search&gsrnamespace=6&gsrlimit=25&gsrsearch="+quote(sq)+
                     "&prop=imageinfo&iiprop=url&iiurlwidth=1000")
            success = False
            for attempt in range(2):
                try:
                    req=Request(api_url,headers={
                        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 Chrome/131 Safari/537.36 ZYNTRASEC/2.3",
                        "Accept":"application/json,text/plain,*/*",
                        "Connection":"close"
                    })
                    with urlopen(req,timeout=7) as r:
                        data=json.loads(r.read().decode("utf-8","replace"))
                    success = True
                    break
                except (URLError, HTTPError, ConnectionResetError, TimeoutError, OSError) as e:
                    msg=str(e)
                    if "10054" in msg or "forcibly closed" in msg.lower():
                        print("[image] Wikimedia connection reset - switching source")
                        wikimedia_ok=False
                        break
                    if attempt == 0:
                        time.sleep(0.7 + random.random()*0.4)
                    else:
                        print("[image] Wikimedia:",e)
            if not success:
                continue
            for page in data.get("query",{}).get("pages",{}).values():
                info=(page.get("imageinfo") or [{}])[0]
                u=info.get("thumburl") or info.get("url")
                add(u,page.get("title","").replace("File:","").strip(),"Wikimedia Commons",sq)
    except Exception as e:
        print("[image] Wikimedia:",e)

    # Bing: collect real source URLs and thumbnails; html.unescape is imported above.
    try:
        for sq in queries[:2]:
            bing="https://www.bing.com/images/search?q="+quote(sq)
            req=Request(bing,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"})
            with urlopen(req,timeout=10) as r: page=r.read().decode("utf-8","ignore")
            for m in re.finditer(r'<a[^>]+class="iusc"[^>]+m="([^"]+)"',page,re.I):
                try: meta=json.loads(html.unescape(m.group(1)).replace('&quot;','"'))
                except Exception: continue
                add(meta.get("turl") or meta.get("murl"),meta.get("t") or meta.get("purl") or (identity+" thumbnail"),"Bing Images",sq)
    except Exception as e: print("[image] Bing:",e)

    # Google thumbnails are last resort only.
    try:
        sq=queries[0]
        google="https://www.google.com/search?tbm=isch&q="+quote(sq)
        req=Request(google,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"})
        with urlopen(req,timeout=10) as r: page=r.read().decode("utf-8","ignore")
        for m in re.finditer(r'https://encrypted-tbn[0-9]*\\?[^"\\ ]+',page):
            u=html.unescape(m.group(0)).replace('\\u003d','=').replace('\\u0026','&')
            add(u,identity+" vehicle thumbnail","Google Images",sq)
            if sum(1 for x in candidates if x[3]=="Google Images")>=10: break
    except Exception as e: print("[image] Google:",e)

    # Deduplicate, sort and only accept candidates with strong model evidence.
    candidates.sort(key=lambda x:x[0],reverse=True); final=[]; seen=set()
    for score,u,title,source in candidates:
        if u in seen: continue
        seen.add(u)
        if score >= 25:
            final.append({"image":u,"title":title,"source":source,"score":score})
        if len(final)>=8: break

    if not final:
        result={"ok":False,"message":"No sufficiently model-matched image found","title":search_query,"search":search_query}
    else:
        result={"ok":True,"image":final[0]["image"],"title":search_query,"source":final[0]["source"],"matched_file":final[0]["title"],"candidates":final}
    with IMAGE_CACHE_LOCK: IMAGE_CACHE[cache_key]=(now,result)
    return result


# ============== HTML CONTENT - IMAGE VISIBLE FIX ==============
HTML=r'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>VEHICLE INFORMATION — ZYNTRASEC</title>
<style>
*{box-sizing:border-box}
:root{
 --bg:#020706;--panel:#04110d;--panel2:#061914;--line:#0b3b2d;
 --green:#2dff83;--green2:#12d66f;--cyan:#15e9c0;--text:#d5e4df;
 --muted:#78938c;--red:#ff5365;--amber:#b6a66f
}
html,body{margin:0;min-height:100%;background:#010504;color:var(--text);font-family:Consolas,"Courier New",monospace}
body{background:
 radial-gradient(circle at 72% 20%,rgba(15,100,70,.13),transparent 35%),
 linear-gradient(180deg,#020806,#010504)}
button,input{font:inherit}
.app{min-height:100vh;display:grid;grid-template-columns:235px 1fr}
.sidebar{border-right:1px solid var(--line);padding:13px 11px;background:linear-gradient(180deg,#03100c,#020806);position:relative}
.brand{height:86px;padding:8px 8px 0;color:var(--green);display:flex;gap:12px;align-items:center}
.brand-icon{font-size:40px;text-shadow:0 0 12px #18ff82}
.brand h1{font-size:28px;margin:0;letter-spacing:1px}.brand p{font-size:12px;margin:5px 0 0;color:#9ab2ac}
.nav-title{color:var(--green);font-weight:bold;border:1px solid var(--line);border-bottom:0;padding:14px 17px 10px;background:#06150f;font-size:15px}
.nav{height:52px;border:1px solid var(--line);border-top:0;padding:0 15px;display:flex;align-items:center;gap:13px;color:#c2d0cc;cursor:pointer;background:#03100d;font-size:15px}
.nav:hover,.nav.active{background:#073020;color:var(--green);box-shadow:inset 3px 0 0 var(--green)}
.nav .ico{width:20px;color:var(--green);text-align:center;font-size:17px}
.system{position:absolute;left:11px;right:11px;bottom:12px;border:1px solid var(--line);padding:13px 16px;background:#03100d}
.system h3{margin:0 0 12px;color:var(--green);font-size:16px}
.sysrow{display:flex;justify-content:space-between;font-size:14px;margin:9px 0;color:#7d9690}.sysrow b{color:var(--green)}
.main{min-width:0;padding:2px 12px 16px}
.topbar{height:auto;min-height:96px;border:1px solid var(--line);display:grid;grid-template-columns:1fr 230px;gap:10px;align-items:center;padding:10px 12px;background:#03100c}
.searchline{display:grid;grid-template-columns:1fr 100px 120px;gap:10px}
.searchline input{height:58px;background:#020806;border:1px solid #0d563e;color:#d9e7e3;outline:none;padding:0 15px;font-size:17px;border-radius:4px;text-transform:uppercase}
.searchline input::placeholder{text-transform:none}
.btn{height:58px;border:1px solid #0d563e;background:#061710;color:var(--green);cursor:pointer;font-weight:bold;font-size:16px;border-radius:4px}
.btn:hover{background:#0a2b1c}.stop{border-color:#8c2636;color:#ff6473}
.online{height:76px;border:1px solid var(--line);padding:10px 14px}
.online small{color:#8da49e;font-size:13px}.online strong{display:block;color:var(--green);font-size:20px;margin:5px 0}.online p{margin:0;color:#718780;font-size:12px}
.workspace{display:grid;grid-template-columns:minmax(540px,1.7fr) minmax(350px,1fr);gap:10px;margin-top:9px}
.left,.right{min-width:0}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.card{border:1px solid var(--line);background:#03110d;min-height:88px;padding:16px}
.card .big{font-size:20px;color:var(--green);font-weight:bold}.card .desc{font-size:14px;color:#718b84;margin-top:8px}
.section{border:1px solid var(--line);background:#03100d;margin-top:9px}
.section-title{height:50px;border-bottom:1px solid var(--line);padding:0 15px;display:flex;align-items:center;color:var(--green);font-weight:bold;font-size:17px}
.content{padding:12px}
.summary{border:1px solid #0a4533;padding:15px;background:#041710;min-height:83px}
.summary-top{display:flex;justify-content:space-between;gap:10px;color:var(--green);font-weight:bold;font-size:16px}
.summary p{color:#8ba29c;font-size:14px;margin:10px 0 0}
.smart-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;margin-top:12px;border:1px solid #0a3b2d}
.smart-grid>div{min-height:50px;padding:10px 12px;border-right:1px solid #0a3025;border-bottom:1px solid #0a3025;background:#03120d}
.smart-grid>div:nth-child(even){border-right:0}
.smart-grid b{display:block;color:var(--green);font-size:13px;margin-bottom:5px}
.smart-grid span{display:block;color:#d0ddd9;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.twocol{display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid #0a3b2d;margin-top:9px}
.detail{display:grid;grid-template-columns:1fr 1fr;min-height:46px;border-bottom:1px solid #0a3025}
.detail:nth-child(odd){border-right:1px solid #0a3025}
.detail:last-child,.detail:nth-last-child(2){border-bottom:0}
.detail .label{padding:11px 10px;color:var(--green);font-size:14px;font-weight:bold}
.detail .val{padding:11px 8px;color:#c6d5d1;font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.more{border:1px solid #0a3b2d;margin-top:9px;padding:15px;color:#839b94;font-size:15px;cursor:pointer}

/* ===== IMAGE BOX - FIXED FOR VISIBILITY ===== */
.imagebox{height:400px;border:1px solid #0a4533;background:#020a08;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center}
.corner{position:absolute;width:34px;height:34px;border-color:var(--green);border-style:solid;z-index:5}
.c1{left:15px;top:15px;border-width:3px 0 0 3px}.c2{right:15px;top:15px;border-width:3px 3px 0 0}.c3{left:15px;bottom:15px;border-width:0 0 3px 3px}.c4{right:15px;bottom:15px;border-width:0 3px 3px 0}

/* IMAGE VISIBLE - FORCED DISPLAY */
.vehicle-img{
    max-width:95%;
    max-height:90%;
    object-fit:contain;
    display:none;
    margin:auto;
    border-radius:8px;
    box-shadow:0 0 30px rgba(45,255,131,0.2);
    z-index:2;
    position:relative;
}
.vehicle-img.visible{
    display:block !important;
}
.vehicle-img.hidden{
    display:none !important;
}

.placeholder{
    text-align:center;
    color:#7d9991;
    font-size:15px;
    z-index:2;
    position:relative;
}
.placeholder .car{
    font-size:85px;
    color:var(--green);
    margin-bottom:16px;
    text-shadow:0 0 20px rgba(40,255,130,.45);
}
.placeholder.visible{
    display:block !important;
}
.placeholder.hidden{
    display:none !important;
}

.model{position:absolute;bottom:13px;left:0;right:0;text-align:center;color:#b7cbc5;font-size:14px;z-index:10;background:rgba(0,0,0,0.7);padding:8px}

.actions .action{height:54px;border-bottom:1px solid #0a3025;display:flex;align-items:center;padding:0 14px;justify-content:space-between;color:#c7d7d2;font-size:15px;cursor:pointer}
.actions .action:hover{background:#072016;color:var(--green)}
.telemetry{height:150px;overflow:auto;color:var(--green);font-size:14px;line-height:1.55;padding:12px;border:1px solid #0a3b2d;background:#020907}
.notice{color:#a99768;background:#17150c;border:1px solid #574923;padding:10px;font-size:14px}
.image-controls{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
.image-btn{padding:7px 16px;border:1px solid #0d563e;background:#061710;color:var(--green);cursor:pointer;font-size:13px;border-radius:4px}
.image-btn:hover{background:#0a2b1c}
.image-source{font-size:12px;color:#5a7a72;margin-top:4px;text-align:center}
.image-status{font-size:13px;color:#2dff83;margin-top:4px;text-align:center}


/* ===== ZYNTRASEC 5.0 RESPONSIVE POLISH ===== */
img{max-width:100%;height:auto}
button,.btn,.image-btn{touch-action:manipulation;min-height:44px}
.workspace,.cards,.twocol,.smart-grid{min-width:0}
.imagebox{width:100%;overflow:hidden;display:flex;align-items:center;justify-content:center;position:relative}
@media (max-width:900px){
 .workspace{display:flex;flex-direction:column}.left,.right{width:100%;max-width:100%}
 .cards{grid-template-columns:repeat(3,minmax(0,1fr))}
 .searchline{grid-template-columns:minmax(0,1fr) auto auto}
 .searchline input{min-width:0}.online{width:100%}
}
@media (max-width:600px){
 .cards{grid-template-columns:1fr 1fr}.cards .card:last-child{display:none}
 .searchline{grid-template-columns:1fr 72px 76px}
 .imagebox{min-height:230px;height:72vw;max-height:340px}
 .vehicle-img{width:auto!important;height:auto!important;max-width:92%!important;max-height:82%!important}
 .content{overflow:hidden}.smart-grid span,.detail .val{white-space:normal;overflow-wrap:anywhere}
}
@media (max-width:380px){
 .searchline{grid-template-columns:1fr 64px 68px}.searchline input,.btn{font-size:10px;padding:0 6px}
 .cards{grid-template-columns:1fr}.cards .card:last-child{display:block}
 .imagebox{min-height:210px}
}

@media (max-width:1200px){
 .app{grid-template-columns:210px minmax(0,1fr)}
 .workspace{grid-template-columns:minmax(0,1fr) minmax(300px,42%)}
 .searchline{grid-template-columns:minmax(0,1fr) 92px 108px}
 .card{padding:13px}
}
@media (max-width:900px){
 html,body{width:100%;overflow-x:hidden}
 .app{display:block;min-height:100vh}
 .sidebar{position:sticky;top:0;z-index:50;width:100%;border-right:0;border-bottom:1px solid var(--line);padding:7px 8px;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}
 .brand{display:flex;height:48px;padding:0 4px;margin-bottom:5px}
 .brand-icon{font-size:26px}.brand h1{font-size:19px}.brand p{font-size:8px;margin-top:2px}
 .nav-title{display:none}
 .nav{display:inline-flex;width:auto;height:38px;border:1px solid var(--line);margin:2px 3px 2px 0;padding:0 10px;gap:7px;font-size:11px;vertical-align:middle}
 .nav .ico{width:auto;font-size:13px}
 .system{display:none}
 .main{padding:8px;min-width:0}
 .topbar{grid-template-columns:1fr;height:auto;min-height:0;gap:8px;padding:9px}
 .searchline{grid-template-columns:minmax(0,1fr) 88px 96px;gap:7px}
 .searchline input,.btn{height:46px;font-size:13px}
 .online{height:auto;min-height:68px;padding:9px 11px}
 .online strong{font-size:16px}
 .workspace{grid-template-columns:1fr;gap:8px}
 .cards{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
 .card{min-height:76px;padding:11px}.card .big{font-size:16px}.card .desc{font-size:11px;margin-top:5px}
 .section-title{height:44px;font-size:14px;padding:0 11px}.content{padding:9px}
 .summary{padding:11px}.summary-top{font-size:13px}.summary p{font-size:11px}
 .smart-grid>div{min-height:46px;padding:8px}.smart-grid b{font-size:11px}.smart-grid span{font-size:12px}
 .twocol{grid-template-columns:1fr}
 .detail:nth-child(odd){border-right:0}
 .detail:last-child,.detail:nth-last-child(2){border-bottom:1px solid #0a3025}
 .detail .label{font-size:12px;padding:9px}.detail .val{font-size:12px;padding:9px}
 .imagebox{height:min(58vw,360px);min-height:240px}
 .vehicle-img{max-width:88%;max-height:78%}
 .placeholder .car{font-size:65px}
 .actions .action{height:46px;font-size:12px;padding:0 10px}
 .telemetry{height:120px;font-size:11px}
}
@media (max-width:600px){
 .brand{height:42px}.brand h1{font-size:17px}.brand p{font-size:7px}
 .nav{height:34px;padding:0 8px;font-size:10px}
 .main{padding:5px}
 .searchline{grid-template-columns:1fr 74px 78px;gap:5px}
 .searchline input,.btn{height:42px;font-size:11px;padding:0 9px}
 .cards{grid-template-columns:1fr 1fr}.cards .card:last-child{display:none}
 .card{min-height:68px}.card .big{font-size:14px}.card .desc{font-size:10px}
 .imagebox{height:72vw;min-height:220px;max-height:310px}
 .model{font-size:11px;padding:6px;bottom:7px}
 .image-controls{gap:5px}.image-btn{padding:6px 9px;font-size:10px}
 .section-title{font-size:13px}.notice{font-size:11px}
}
@media (max-width:380px){
 .brand{display:none}
 .sidebar{padding:5px}
 .nav{height:32px;font-size:9px;padding:0 7px}
 .searchline{grid-template-columns:1fr 62px 68px}
 .searchline input,.btn{height:40px;font-size:10px}
 .cards{gap:4px}.card{padding:8px}.card .big{font-size:12px}.card .desc{font-size:9px}
 .content{padding:7px}.imagebox{min-height:200px}
 .detail .label,.detail .val{font-size:11px;padding:8px}
}

/* ===== ZYNTRASEC v2.2 RESPONSIVE OVERRIDES ===== */
html{overflow-x:hidden}
body{width:100%;overflow-x:hidden}
.app{width:100%;min-width:0}
main,.main,.content,.workspace{min-width:0;max-width:100%}
img,video,canvas{max-width:100%}
input,button,select,textarea{max-width:100%}
.vehicle-img{width:100%;max-width:100%;height:auto;object-fit:contain;display:block}
@media(max-width:1100px){
 .app{grid-template-columns:190px minmax(0,1fr)!important}
 .sidebar{padding:10px 8px!important}
 .brand h1{font-size:22px!important}.brand-icon{font-size:32px!important}
 .nav{padding-left:10px!important;padding-right:10px!important}
}
@media(max-width:820px){
 .app{display:block!important;min-height:100vh}
 .sidebar{position:relative!important;width:100%!important;height:auto!important;border-right:0!important;border-bottom:1px solid var(--line);padding:8px!important}
 .brand{height:auto!important;min-height:58px}
 .system{position:static!important;margin:8px 0 0}
 .nav-title{padding:9px 12px!important}
 .nav{height:42px!important;display:inline-flex!important;width:auto!important;margin:3px 2px!important;border:1px solid var(--line)!important;border-radius:7px;padding:0 10px!important}
 .main,main,.content,.workspace{width:100%!important;padding:10px!important;overflow-x:hidden!important}
}
@media(max-width:600px){
 .main,main,.content,.workspace{padding:8px!important}
 .brand h1{font-size:19px!important}.brand p{font-size:10px!important}.brand-icon{font-size:27px!important}
 .nav{font-size:12px!important;gap:7px!important;height:38px!important}.nav .ico{width:15px!important;font-size:14px!important}
 .vehicle-img{min-height:160px;max-height:42vh}
 .search-row,.searchbar,.toolbar,.actions{width:100%!important;flex-wrap:wrap!important}
 .search-row input,.searchbar input,input#rc{width:100%!important;min-width:0!important;font-size:16px!important}
 button{min-height:40px}
 table{display:block;width:100%;overflow-x:auto}
}
@media(max-width:400px){
 .main,main,.content,.workspace{padding:6px!important}
 .brand{gap:7px!important}.brand h1{font-size:17px!important}
 .vehicle-img{min-height:130px;max-height:38vh}
}

</style>
</head>
<body><div id="ownerLock" style="position:fixed;inset:0;background:#0b0f14;z-index:99999;display:flex;align-items:center;justify-content:center;font-family:Arial"><div style="width:min(420px,90vw);padding:28px;border:1px solid #2b3440;border-radius:16px;background:#111821;color:#fff"><h2>ZYNTRASEC OWNER LOCK</h2><p>Authorized Windows user only.</p><input id="ownerPassword" type="password" autocomplete="current-password" placeholder="Owner password" style="width:100%;box-sizing:border-box;padding:12px"><button id="ownerLogin" style="width:100%;margin-top:12px;padding:12px">UNLOCK</button><div id="ownerMsg" style="margin-top:12px;color:#ff9b9b"></div></div></div>
<div class="app">
<aside class="sidebar">
 <div class="brand"><div class="brand-icon">▱</div><div><h1>ZYNTRASEC</h1><p>VEHICLE INFORMATION DASHBOARD</p></div></div>
 <div class="nav-title">CONTROL MATRIX</div>
 <div class="nav active" onclick="focusSearch()"><span class="ico">⌂</span>DASHBOARD</div>
 <div class="nav" onclick="focusSearch()"><span class="ico">⌕</span>VEHICLE LOOKUP</div>
 <div class="nav" onclick="rtoInfo()"><span class="ico">▤</span>RTO INFORMATION</div>
 <div class="nav" onclick="vinInfo()"><span class="ico">▥</span>VIN DECODER</div>
 <div class="nav" onclick="plateCheck()"><span class="ico">▣</span>NUMBER PLATE CHECK</div>
 <div class="nav" onclick="showHistory()"><span class="ico">◷</span>SEARCH HISTORY</div>
 <div class="nav" onclick="showFavorites()"><span class="ico">☆</span>FAVORITES</div>
 <div class="nav" onclick="settings()"><span class="ico">⚙</span>SETTINGS</div>
 <div class="nav" onclick="apiConsole()"><span class="ico">&lt;/&gt;</span>API CONSOLE</div>
 <div class="nav" onclick="about()"><span class="ico">ⓘ</span>ABOUT</div>
 <div class="system">
  <h3>SYSTEM INFO</h3>
  <div class="sysrow">VERSION <b>2.1.0</b></div><div class="sysrow">PLATFORM <b id="platform">WEB</b></div>
  <div class="sysrow">UPTIME <b id="uptime">00:00:00</b></div><div class="sysrow">USER <b>OPERATOR</b></div>
  <div class="sysrow">MODE <b>PROFESSIONAL</b></div>
 </div>
</aside>

<main class="main">
 <header class="topbar">
  <div class="searchline">
   <input id="rc" placeholder="ENTER VEHICLE NUMBER / CHASSIS / ENGINE NO." autocomplete="off" style="text-transform:uppercase">
   <button class="btn stop" onclick="stopSearch()">▣ STOP</button>
   <button class="btn" onclick="searchRC()">⌕ SEARCH</button>
  </div>
  <div class="online"><small>SYSTEM STATUS</small><strong><span class="status-dot">●</span> ONLINE</strong><p>RESPONSE TIME &lt; 1.2s<br>CACHE : SYNC</p></div>
 </header>

 <div class="workspace">
  <section class="left">
   <div class="cards">
    <div class="card"><div class="big">◎ <span id="target">NO TARGET</span></div><div class="desc" id="targetDesc">Search for vehicle details</div></div>
    <div class="card"><div class="big">✓ <span id="ready">READY</span></div><div class="desc">System is ready for lookup</div></div>
    <div class="card"><div class="big">⌁ <span id="api">RTO ONLINE</span></div><div class="desc">Connected to RTO server</div></div>
   </div>

   <div class="section">
    <div class="section-title">▣ VEHICLE INTELLIGENCE</div>
    <div class="content">
     <div class="summary">
      <div class="summary-top"><span>SMART VEHICLE SUMMARY</span><span id="cache">🚗 — Cache: 0 / 1000</span></div>
      <p id="summaryText">Perform a vehicle lookup to generate an intelligent summary.</p>
      <div class="smart-grid">
       <div><b>REGISTRATION NO</b><span id="s_reg">N/A</span></div>
       <div><b>REGISTRATION DATE</b><span id="s_date">N/A</span></div>
       <div><b>MANUFACTURER</b><span id="s_maker">N/A</span></div>
       <div><b>MODEL</b><span id="s_model">N/A</span></div>
       <div><b>VEHICLE CLASS</b><span id="s_class">N/A</span></div>
       <div><b>FUEL TYPE</b><span id="s_fuel">N/A</span></div>
       <div><b>RTO</b><span id="s_rto">N/A</span></div>
       <div><b>REGISTERED STATE</b><span id="s_state">N/A</span></div>
       <div><b>FITNESS UPTO</b><span id="s_fitness">N/A</span></div>
       <div><b>INSURANCE</b><span id="s_insurance">N/A</span></div>
       <div><b>INSURANCE COMPANY</b><span id="s_insurer">N/A</span></div>
       <div><b>POLICY UPTO</b><span id="s_policy">N/A</span></div>
       <div><b>PUC STATUS</b><span id="s_puc">N/A</span></div>
       <div><b>ROAD TAX UPTO</b><span id="s_tax">N/A</span></div>
       <div><b>PERMIT</b><span id="s_permit">N/A</span></div>
       <div><b>STATUS</b><span id="s_status">N/A</span></div>
       <div><b>COLOR</b><span id="s_color">N/A</span></div>
       <div><b>SEATS</b><span id="s_seats">N/A</span></div>
       <div><b>ENGINE CC</b><span id="s_cc">N/A</span></div>
       <div><b>MANUFACTURE YEAR</b><span id="s_year">N/A</span></div>
      </div>
     </div>
     <div class="twocol">
      <div class="detail"><div class="label">♟ OWNER(S)</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▥ MFR DETAIL NO</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">⌖ CITY</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▱ POL. MODEL</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▣ FITNESS Upto</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▣ INSURANCE STATUS</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">⛽ FUEL TYPE</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▤ POL NO</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">♢ INSURANCE COMPANY</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▣ POL UPTO</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▤ INSURANCE NO</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▤ PERMIT</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▣ INSURANCE Upto</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">⌖ REGISTERED RTO</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">♟ OWNER NAME</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">▣ REGISTRATION DATE</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">♜ OWNER BANK</div><div class="val">N/A</div></div>
      <div class="detail"><div class="label">₹ TAX UPTO</div><div class="val">N/A</div></div>
     </div>
     <div class="more" onclick="toggleFields()">⊕ &nbsp; ADDITIONAL INFORMATION <span style="float:right">⌄</span></div>
    </div>
   </div>

  </section>

  <aside class="right">
   <div class="section" style="margin-top:0">
    <div class="section-title">▧ VEHICLE IMAGE</div>
    <div class="content">
     <div class="imagebox" id="imageBox">
      <div class="corner c1"></div><div class="corner c2"></div><div class="corner c3"></div><div class="corner c4"></div>
      <img id="vehicleImg" class="vehicle-img hidden" alt="Vehicle model image">
      <div id="placeholder" class="placeholder visible"><div class="car">♧</div>MODEL: STAGE NOT FOUND<br><br>IMAGE : NOT AVAILABLE<br><br>Please enter a valid vehicle number to fetch image from model database</div>
      <div id="modelName" class="model">MODEL: STAGE NOT FOUND</div>
     </div>
     <div id="imageSource" class="image-source"></div>
     <div id="imageStatus" class="image-status"></div>
     <div class="image-controls">
      <button class="image-btn" onclick="refreshImage()">⟳ REFRESH IMAGE</button>
      <button class="image-btn" onclick="tryAlternateImage()">↺ TRY ALTERNATE</button>
      <button class="image-btn" onclick="tryGoogleImage()">🔍 GOOGLE SEARCH</button>
     </div>
    </div>
   </div>

   <div class="section actions">
    <div class="section-title">⚙ QUICK ACTIONS</div>
    <div class="action" onclick="exportReport()">☁ EXPORT REPORT <span>›</span></div>
    <div class="action" onclick="exportJSON()">▤ EXPORT JSON <span>›</span></div>
    <div class="action" onclick="copyResult()">▣ COPY RESULT <span>›</span></div>
    <div class="action" onclick="favorite()">☆ ADD TO FAVORITES <span>›</span></div>
    <div class="action" onclick="qrReport()">⚒ QR CODE REPORT <span>›</span></div>
   </div>

   <div class="section">
    <div class="section-title">⌁ SYSTEM TELEMETRY</div>
    <div class="telemetry" id="telemetry">[15:42:01] Vehicle lookup system initialized<br>[15:42:02] RTO database connected<br>[15:42:05] Loading vehicle modules...<br>[15:42:07] Ready for user input<br>[15:42:10] System status: ONLINE<br>&gt; _</div>
   </div>
  </aside>
 </div>
</main>
</div>

<script>
let lastData=null, stopped=false, started=Date.now();
let lastImageQuery=null, lastSearchRC=null, lastImageSource="";

const q=s=>document.querySelector(s);
function esc(x){return String(x??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
function log(t){let d=new Date(),s=d.toTimeString().slice(0,8);q("#telemetry").innerHTML+=`<br>[${s}] ${esc(t)}`;q("#telemetry").scrollTop=99999}
function focusSearch(){q("#rc").focus()}
function stopSearch(){stopped=true;q("#ready").textContent="STOPPED";log("Lookup stopped by operator")}
function label(k){return k.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase())}
function normKey(k){return String(k).toLowerCase().replace(/[^a-z0-9]/g,"")}
function get(d,keys){
 const map={};
 for(const [k,v] of Object.entries(d||{})) map[normKey(k)]=v;
 for(const k of keys){const nk=normKey(k);if(map[nk]!==undefined&&map[nk]!==null&&map[nk]!==""&&map[nk]!=="N/A")return map[nk]}
 return "N/A";
}
function setDetails(d){
 const vals=[
  get(d,["owner","owner_name","owners"]),get(d,["mfr_detail_no","manufacturer_detail_no"]),
  get(d,["city","city_name"]),get(d,["pol_model","policy_model"]),
  get(d,["fitness_upto","fitness_valid_till"]),get(d,["insurance_status","insurance"]),
  get(d,["fuel_type","fuel"]),get(d,["policy_no","insurance_policy_no"]),
  get(d,["insurance_company","insurer"]),get(d,["policy_upto","insurance_upto","insurance_valid_till"]),
  get(d,["insurance_no","insurance_policy_no"]),get(d,["permit","permit_status"]),
  get(d,["insurance_upto","insurance_valid_till"]),get(d,["rto","rto_office","registered_rto"]),
  get(d,["owner_name","owner"]),get(d,["registration_date","reg_date"]),
  get(d,["owner_bank","financier"]),get(d,["tax_upto","road_tax_upto","tax_valid_till"])
 ];
 document.querySelectorAll(".detail .val").forEach((e,i)=>e.textContent=String(vals[i]).slice(0,80));
}
async function searchRC(){
 stopped=false;
 let rc = q("#rc").value.trim().toUpperCase();
 q("#rc").value = rc;
 if(!rc)return alert("Enter vehicle number");
 lastSearchRC=rc;
 q("#target").textContent=rc;q("#targetDesc").textContent="Searching for vehicle details";q("#ready").textContent="BUSY";q("#api").textContent="CONNECTING";log("Searching "+rc+" ...");
 try{
  const r=await fetch("/api/lookup?rc="+encodeURIComponent(rc),{cache:"no-store"});
   const text=await r.text(); let d; try{d=JSON.parse(text)}catch(e){d={ok:false,error:"Server returned invalid JSON",http_status:r.status,raw:text.slice(0,500)}}
   log("HTTP "+r.status+" received"); if(stopped)return;
  if(!d.ok){q("#ready").textContent="ERROR";q("#api").textContent="ERROR";q("#summaryText").textContent=(d.error||"Lookup failed")+(d.body?" | "+d.body:"");log("Lookup failed: "+(d.error||"Unknown error"));return}
  lastData=d; q("#ready").textContent="READY";q("#api").textContent="RTO ONLINE";q("#targetDesc").textContent="Vehicle details loaded";
  setDetails(d.data); updateSmartSummary(d.data,rc); log("Fields received: "+Object.keys(d.data||{}).length); 
  await loadVehicleImage(d.data,rc);
  q("#summaryText").textContent=buildSummary(d.data,rc);log("Lookup successful via "+d.api);
 }catch(e){q("#ready").textContent="ERROR";q("#api").textContent="OFFLINE";q("#summaryText").textContent="Browser request failed: "+e.message;log("Request error: "+e.message)}
}
function buildSummary(d,rc){
 let make=get(d,["maker","manufacturer","make","model_name"]);
 let model=get(d,["model","maker_model","maker model"]);
 let fuel=get(d,["fuel","fuel_type","fueltype"]);
 let rto=get(d,["rto","rto_office","registered_rto"]);
 return `${rc} • ${make} ${model} • Fuel: ${fuel} • RTO: ${rto}`.replace(/N\/A/g,"Unknown");
}
function updateSmartSummary(d,rc){
 const v=(keys)=>get(d,keys);
 const set=(id,val)=>q(id).textContent=String(val??"N/A");
 
 let regDate = v(["registration_date","reg_date"]);
 if (regDate !== "N/A" && regDate !== "Unknown") {
   try {
     let parts = regDate.split(/[-/]/);
     if (parts.length === 3) {
       let day = parseInt(parts[0]);
       if (day > 31) { day = 30; regDate = `${day.toString().padStart(2, '0')}-${parts[1]}-${parts[2]}`; }
     }
   } catch(e) {}
 }
 
 let maker = v(["maker","manufacturer","make","model_name"]);
 if (maker !== "N/A" && maker !== "Unknown") {
   maker = maker.replace(/\s*\([^)]*\)\s*/g, " ").replace(/\s*P\.?\s*LTD\.?\s*/g, " ").trim();
 }
 
 set("#s_reg",v(["registration_no","registration_number","reg_no"])==="N/A"?rc:v(["registration_no","registration_number","reg_no"]));
 set("#s_date",regDate);
 set("#s_maker",maker);
 set("#s_model",v(["model","maker_model","maker model"]));
 set("#s_class",v(["vehicle_class","vehicle_class_description","class"]));
 set("#s_fuel",v(["fuel","fuel_type","fueltype"]));
 set("#s_rto",v(["rto","rto_office","registered_rto"]));
 set("#s_state",v(["registered_state","state"]));
 set("#s_fitness",v(["fitness_upto","fitness_valid_till"]));
 set("#s_insurance",v(["insurance_status","insurance","insurance_expiry","insurance_upto"]));
 set("#s_insurer",v(["insurance_company","insurer"]));
 set("#s_policy",v(["policy_upto","insurance_upto","insurance_expiry","insurance_valid_till"]));
 set("#s_puc",v(["puc","puc_status","puc_valid_till"]));
 set("#s_tax",v(["tax_upto","road_tax_upto","tax_valid_till"]));
 set("#s_permit",v(["permit","permit_status"]));
 set("#s_status",v(["status","vehicle_status","rc_status"]));
 set("#s_color",v(["color","vehicle_color"]));
 set("#s_seats",v(["seats","seat_capacity"]));
 set("#s_cc",v(["engine_cc","cubic_capacity","cc"]));
 set("#s_year",v(["manufacture_year","manufacturing_year","mfg_year"]));
 q("#summaryText").textContent=buildSummary(d,rc);
}
async function loadVehicleImage(d, rc) {
    let make = get(d, ["maker", "manufacturer", "make", "model_name"]);
    let model = get(d, ["model", "maker_model", "maker model"]);
    // Remove RTO suffix/noise such as LIMITED(0) AT before image search.
    model = (model||"").replace(/\([^)]*\)/g," ").replace(/\bLIMITED\b/gi," ")
      .replace(/\bAT\b/gi," ").replace(/\bMT\b/gi," ").replace(/\s+/g," ").trim();
    let cleanMake = (make||"").replace(/\s*\([^)]*\)\s*/g," ").trim();
    let query = model && !["N/A","Unknown"].includes(model) ? ((cleanMake && !["N/A","Unknown"].includes(cleanMake) ? cleanMake+" " : "") + model + " vehicle") : (cleanMake||rc);
    let displayModel = model && !["N/A","Unknown"].includes(model) ? model : (cleanMake||rc);
    const img=document.getElementById('vehicleImg'), ph=document.getElementById('placeholder');
    const name=document.getElementById('modelName'); name.textContent="MODEL: "+displayModel.toUpperCase();
    lastImageQuery=query; img.className="vehicle-img hidden"; img.style.display="none"; ph.className="placeholder visible"; ph.style.display="block";
    document.getElementById('imageSource').textContent=""; document.getElementById('imageStatus').textContent="⏳ Finding model image…";
    if(!query.trim()) return;
    try{
      const r=await fetch("/api/vehicle-image?q="+encodeURIComponent(query)+"&make="+encodeURIComponent(make||"")+"&model="+encodeURIComponent(model||""),{cache:"no-store"});
      const x=await r.json();
      if(!x.ok || !x.candidates?.length) throw new Error("No model image found in public sources");
      const candidates=x.candidates; let idx=0;
      const tryNext=()=>{
        if(idx>=candidates.length){
          ph.className="placeholder visible"; ph.style.display="block"; ph.innerHTML='<div class="car">🚗</div>IMAGE NOT AVAILABLE<br><small>Strong model match not found</small>';
          document.getElementById('imageStatus').textContent="⚠️ No public model image found"; return;
        }
        const c=candidates[idx++];
        const proxy="/api/image-proxy?url="+encodeURIComponent(c.image);
        img.onerror=()=>{
          img.onerror=null;
          img.onload=null;
          setTimeout(()=>{
            img.onload=()=>{
              ph.className="placeholder hidden"; ph.style.display="none";
              img.className="vehicle-img visible"; img.style.display="block";
              img.style.maxWidth="95%"; img.style.maxHeight="90%";
              img.style.objectFit="contain"; img.style.margin="auto"; img.style.borderRadius="8px";
              document.getElementById('imageSource').textContent="📷 "+c.source;
              document.getElementById('imageStatus').textContent="✅ Model-matched image loaded";
              lastImageSource=c.source;
            };
            img.onerror=tryNext;
            img.src=c.image;
          },30);
        };
        img.onload=()=>{
          ph.className="placeholder hidden"; ph.style.display="none"; img.className="vehicle-img visible"; img.style.display="block";
          img.style.maxWidth="95%"; img.style.maxHeight="90%"; img.style.objectFit="contain"; img.style.margin="auto"; img.style.borderRadius="8px";
          document.getElementById('imageSource').textContent="📷 "+c.source;
          document.getElementById('imageStatus').textContent="✅ Model-matched image loaded"; lastImageSource=c.source;
        };
        img.src=proxy;
      };
      tryNext();
    }catch(e){
      ph.className="placeholder visible"; ph.style.display="block"; ph.innerHTML='<div class="car">🚗</div>IMAGE SEARCH TEMPORARILY FAILED<br><small>Model search retry available</small>';
      document.getElementById('imageStatus').textContent="⚠️ "+e.message; log("Image error: "+e.message);
    }
}

function tryGoogleImage(){
 if(lastImageQuery){
  window.open("https://www.google.com/search?q="+encodeURIComponent(lastImageQuery+" vehicle")+"&tbm=isch", "_blank");
  log("Opened Google Image Search for: "+lastImageQuery);
 } else {
  alert("Please search a vehicle first");
 }
}
function exportJSON(){if(!lastData)return alert("Search a vehicle first");download(new Blob([JSON.stringify(lastData,null,2)],{type:"application/json"}),"ZYNTRASEC_RC.json")}
function exportReport(){if(!lastData)return alert("Search a vehicle first");let t="ZYNTRASEC SECURITY — VEHICLE REPORT\\n==========================================\\n";t+="RC: "+q("#rc").value+"\\nAPI: "+lastData.api+"\\nTIME: "+lastData.timestamp+"\\n\\n";for(const[k,v]of Object.entries(lastData.data||{}))t+=label(k)+": "+(typeof v==="object"?JSON.stringify(v):v)+"\\n";download(new Blob([t],{type:"text/plain"}),"ZYNTRASEC_Vehicle_Report.txt")}
function copyResult(){if(!lastData)return alert("Search first");navigator.clipboard.writeText(JSON.stringify(lastData.data,null,2)).then(()=>alert("Copied"))}
function download(b,n){let a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=n;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
async function favorite(){let rc=q("#rc").value.trim().toUpperCase();if(!rc)return alert("Search first");await fetch("/api/favorite",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rc})});log("Added "+rc+" to favorites")}
async function showHistory(){
 let d=await(await fetch("/api/history")).json();
 let msg=d.length?d.map(x=>`${x.rc} | ${x.api||"-"} | ${x.status} | ${x.created}`).join("\n"):"No search history.";
 alert("SEARCH HISTORY\\n\\n"+msg);
}
async function showFavorites(){
 let d=await(await fetch("/api/favorites")).json();
 let msg=d.length?d.map(x=>`${x.rc} | ${x.created}`).join("\n"):"No favorites.";
 alert("FAVORITES\\n\\n"+msg);
}
function toggleFields(){q(".summary").scrollIntoView({behavior:"smooth"})}
function rtoInfo(){alert("RTO fields are populated from the authorized API response.")}
function vinInfo(){alert("VIN decoding needs a VIN and an authorized VIN data source.")}
function plateCheck(){alert(q("#rc").value.trim()?"Vehicle number entered: "+q("#rc").value.trim():"Enter a vehicle number first.")}
function settings(){alert("Settings: API credentials are loaded server-side from environment variables.")}
function apiConsole(){alert("API Console: configured API sources are used server-side.")}
function qrReport(){alert("QR report generation can be added with a QR library; the current build keeps the GUI dependency-free.")}
function about(){alert("ZYNTRASEC Security — Vehicle Information Dashboard\\nVersion 2.1.0\\nPrivacy mode enabled.")}
function updateUptime(){let s=Math.floor((Date.now()-started)/1000);q("#uptime").textContent=[Math.floor(s/3600),Math.floor(s%3600/60),s%60].map(x=>String(x).padStart(2,"0")).join(":")}
setInterval(updateUptime,1000);
q("#rc").addEventListener("keydown",e=>{if(e.key==="Enter")searchRC()});
q("#rc").addEventListener("input", function(e) {
    let start = this.selectionStart;
    let end = this.selectionEnd;
    this.value = this.value.toUpperCase();
    this.setSelectionRange(start, end);
});
</script>
<script>(async()=>{const l=document.getElementById("ownerLock"),p=document.getElementById("ownerPassword"),b=document.getElementById("ownerLogin"),m=document.getElementById("ownerMsg");function unlockUI(){l.style.display="none";document.body.style.overflow="";}async function check(){try{const r=await fetch("/api/auth-status",{cache:"no-store",credentials:"same-origin"}),d=await r.json();if(d.ok){unlockUI();return true}}catch(e){}return false}async function go(){b.disabled=true;m.textContent="Checking...";try{const r=await fetch("/api/login",{method:"POST",headers:{"Content-Type":"application/json"},credentials:"same-origin",body:JSON.stringify({password:p.value})}),d=await r.json();if(d.ok){unlockUI();p.value="";m.textContent="";window.dispatchEvent(new Event("zyntrasec-unlocked"));}else m.textContent=d.error||"Unlock failed"}catch(e){m.textContent="Security service unavailable"}finally{b.disabled=false}}if(!(await check())){l.style.display="flex";p.focus()}b.onclick=go;p.onkeydown=e=>{if(e.key==="Enter")go()}})();</script></body>
</html>'''

ALLOWED_IMAGE_HOSTS = {
    "upload.wikimedia.org", "commons.wikimedia.org",
    "encrypted-tbn0.gstatic.com", "encrypted-tbn1.gstatic.com",
    "encrypted-tbn2.gstatic.com", "encrypted-tbn3.gstatic.com",
}

def allowed_image_host(host):
    host=(host or "").lower().split(":")[0]
    return host in ALLOWED_IMAGE_HOSTS or (host.endswith(".mm.bing.net") and host.startswith("tse"))

def fetch_image_bytes(image_url):
    """Download only from known public image/CDN hosts and return bytes + content type."""
    p=urlparse(image_url)
    if p.scheme not in ("http", "https") or not allowed_image_host(p.netloc):
        return None, None
    req=Request(image_url,headers={
        "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
        "Accept":"image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    })
    with urlopen(req,timeout=15) as r:
        data=r.read(8*1024*1024+1)
        if len(data)>8*1024*1024:
            return None,None
        ctype=(r.headers.get("Content-Type") or "image/jpeg").split(";")[0].strip().lower()
        if not ctype.startswith("image/"):
            return None,None
        return data,ctype

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def _auth_denied(self):self.send_json({"ok":False,"error":"Owner authentication required"},401)
 def send_json(self,d,status=200):
  try:
   b=json.dumps(d,ensure_ascii=False).encode("utf-8")
   self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.send_header("Cache-Control","no-store");self.end_headers()
   try:
    self.wfile.write(b)
   except (BrokenPipeError, ConnectionResetError):
    return;self.wfile.flush()
  except (BrokenPipeError,ConnectionResetError):
   pass
  except Exception as e:
   print("[send_json]",e)
 def do_GET(self):
  u=urlparse(self.path)
  if u.path.startswith("/api/") and u.path not in ("/api/login","/api/auth-status") and not _is_auth(self):self._auth_denied();return
  if u.path=="/":
   b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers()
   try:
    self.wfile.write(b)
   except (BrokenPipeError, ConnectionResetError):
    return;return
  if u.path=="/api/status":self.send_json({"online":True,"configured":bool(RAPIDAPI_KEY),"sources":len(APIS)});return
  if u.path=="/api/auth-status":self.send_json({"ok":_is_auth(self)});return
  if u.path=="/api/history":self.send_json(history());return
  if u.path=="/api/favorites":self.send_json(favorites());return
  if u.path=="/api/image-proxy":
   target=parse_qs(u.query).get("url",[""])[0].strip()
   try:
    data,ctype=fetch_image_bytes(target)
    if not data:
     self.send_response(404);self.end_headers();return
    self.send_response(200);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(data)));self.send_header("Cache-Control","public, max-age=86400");self.end_headers();self.wfile.write(data)
   except (BrokenPipeError,ConnectionResetError):
    pass
   except Exception as e:
    print("[image-proxy]",e)
    try:self.send_response(502);self.end_headers()
    except Exception:pass
   return
  if u.path=="/api/vehicle-image":
   params=parse_qs(u.query)
   q=params.get("q",[""])[0].strip()
   make=params.get("make",[""])[0].strip()
   model=params.get("model",[""])[0].strip()
   self.send_json(vehicle_image(q, make, model) if (q or make or model) else {"ok":False});return
  if u.path=="/api/lookup":
   rc=parse_qs(u.query).get("rc",[""])[0].strip().upper()
   if not valid_rc(rc):self.send_json({"ok":False,"error":"Invalid Indian RC format. Example: GJ05AB1234"},400);return
   d=lookup(rc);add_history(rc,d.get("api"),"SUCCESS" if d.get("ok") else "FAILED");self.send_json(d,200 if d.get("ok") else 502);return
  self.send_json({"error":"Not found"},404)
 def do_POST(self):
  global AUTH_TOKEN
  path=urlparse(self.path).path
  if path=="/api/login":
   try:
    n=int(self.headers.get("Content-Length","0"));body=json.loads(self.rfile.read(n) or b"{}");ok,info=_verify_owner(str(body.get("password","")))
    if ok:
     AUTH_TOKEN=_new_session();self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Set-Cookie",f"ZYNTRASEC_SESSION={AUTH_TOKEN}; HttpOnly; Path=/; SameSite=Strict");self.end_headers();self.wfile.write(b"{\"ok\":true}");return
    msg="Owner security belongs to another Windows machine/user." if info=="machine_mismatch" else (f"Too many failed attempts. Try again in {info} seconds." if isinstance(info,int) and info>=60 else (f"Invalid password. Attempts remaining: {info}" if isinstance(info,int) else "Security validation failed."))
    self.send_json({"ok":False,"error":msg},401);return
   except Exception:self.send_json({"ok":False,"error":"Invalid security request"},400);return
  if not _is_auth(self):self._auth_denied();return
  if path=="/api/favorite":
   n=int(self.headers.get("Content-Length","0"));body=json.loads(self.rfile.read(n) or b"{}")
   rc=re.sub(r"[^A-Z0-9]","",str(body.get("rc","")).upper())
   if rc:add_favorite(rc)
   self.send_json({"ok":True});return
  self.send_json({"error":"Not found"},404)

if __name__=="__main__":
 _security_setup()
 initdb()
 print("="*60)
 print(" ZYNTRASEC VEHICLE INFORMATION DASHBOARD v2.1.0")
 print(" URL: http://%s:%s"%(HOST,PORT))
 print(" RAPIDAPI:", "CONFIGURED" if RAPIDAPI_KEY else "NOT CONFIGURED")
 print("="*60)
 print(" ✅ IMAGE VISIBILITY: FIXED")
 print(" ✅ Image now shows on screen")
 print(" ✅ Placeholder hides when image loads")
 print("="*60)
 print("\n Press Ctrl+C to stop the server")
 print("="*60)
 ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
