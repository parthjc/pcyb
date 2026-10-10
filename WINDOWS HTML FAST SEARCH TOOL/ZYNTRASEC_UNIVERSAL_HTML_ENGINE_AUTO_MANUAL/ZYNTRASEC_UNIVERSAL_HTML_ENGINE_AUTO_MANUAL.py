import os, re, json, sqlite3, threading, webbrowser, urllib.parse, http.server, socketserver
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from html.parser import HTMLParser

APP_TITLE = "ZYNTRASEC Universal HTML Engine"
VIEWER = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ZYNTRASEC Indexed Report</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e8eef8;font:14px/1.45 "Segoe UI",Arial,sans-serif}
header{padding:18px 22px;background:#15243a;border-bottom:1px solid #26364e}h1{margin:0;color:#54e38e;font-size:22px}header p{margin:5px 0 0;color:#b7c5d8}
main{padding:16px;max-width:1900px;margin:auto}.bar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;background:#111c2e;padding:12px;border:1px solid #26364e;border-radius:10px;position:sticky;top:0;z-index:4}
input,select,button{font:inherit;padding:9px;border-radius:7px;border:1px solid #3b4c65;background:#0b1424;color:#e8eef8}input{flex:1;min-width:220px}button{cursor:pointer}button:disabled{opacity:.4}
#status{margin:12px 2px;color:#b7c5d8}.wrap{overflow:auto;max-height:calc(100vh - 235px);border:1px solid #26364e;border-radius:9px}
table{border-collapse:collapse;width:100%}th,td{padding:9px 11px;text-align:left;vertical-align:top;border-bottom:1px solid #26364e;min-width:100px;max-width:420px;overflow-wrap:anywhere}th{position:sticky;top:0;background:#1a2a42}tr:nth-child(even) td{background:#111e31}.pager{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:12px}
</style></head><body><header><h1>ZYNTRASEC // INDEXED HTML REPORT</h1><p>SQLite-backed local search • paginated results</p></header><main>
<div class="bar"><input id="q" type="search" placeholder="Search report..." autocomplete="off"><label>Rows/page <select id="size"><option>100</option><option selected>250</option><option>500</option><option>1000</option></select></label><button id="go">Search</button><button id="clear">Clear</button></div>
<div id="status">Connecting to local index…</div><div class="wrap"><table><thead id="head"></thead><tbody id="body"></tbody></table></div>
<div class="pager"><button id="prev">Previous</button><span id="page"></span><button id="next">Next</button></div></main>
<script>
let page=1,headers=[],timer;const $=x=>document.getElementById(x);
function esc(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function load(){try{const q=$('q').value.trim(),size=+$('size').value||250;const r=await fetch('/api/search?q='+encodeURIComponent(q)+'&page='+page+'&size='+size);if(!r.ok)throw Error();const d=await r.json();headers=d.headers||[];
if(!$('head').dataset.ready){$('head').innerHTML='<tr>'+headers.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr>';$('head').dataset.ready='1';}
$('body').innerHTML=(d.rows||[]).map(row=>'<tr>'+headers.map((_,i)=>'<td>'+esc(row[i]||'')+'</td>').join('')+'</tr>').join('');
const total=d.total||0,pages=Math.max(1,Math.ceil(total/size));$('status').textContent=total.toLocaleString()+' matching records';$('page').textContent='Page '+page+' / '+pages+' • '+(total?(page-1)*size+1:0)+'–'+Math.min(page*size,total);$('prev').disabled=page<=1;$('next').disabled=page>=pages;
}catch(e){$('status').textContent='Local index not available. Keep ZYNTRASEC open and reopen this viewer.';}}
function search(){page=1;load()}$('go').onclick=search;$('q').addEventListener('keydown',e=>{if(e.key==='Enter')search()});$('q').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,250)});$('size').onchange=()=>{page=1;load()};$('prev').onclick=()=>{page--;load()};$('next').onclick=()=>{page++;load()};$('clear').onclick=()=>{$('q').value='';search()};load();
</script></body></html>"""

class Parser(HTMLParser):
    def __init__(self,conn):
        super().__init__(convert_charrefs=True);self.conn=conn;self.depth=0;self.tid=-1;self.counts={}
        self.row=None;self.cell=None;self.celltag="";self.skip=0;self.row_no=0
    def handle_starttag(self,tag,attrs):
        tag=tag.lower()
        if tag in ("script","style","noscript"):self.skip+=1;return
        if self.skip:return
        if tag=="table":
            if self.depth==0:self.tid+=1;self.counts[self.tid]=0;self.row_no=0
            self.depth+=1;return
        if self.depth!=1:return
        if tag=="tr":self.row=[]
        elif tag in ("td","th") and self.row is not None:self.cell=[];self.celltag=tag
        elif tag=="br" and self.cell is not None:self.cell.append(" ")
    def handle_endtag(self,tag):
        tag=tag.lower()
        if tag in ("script","style","noscript") and self.skip:self.skip-=1;return
        if self.skip:return
        if tag=="table" and self.depth:self.depth-=1;return
        if self.depth!=1:return
        if tag in ("td","th") and self.cell is not None:
            self.row.append({"v":" ".join("".join(self.cell).split()),"h":self.celltag=="th"});self.cell=None
        elif tag=="tr" and self.row is not None:
            if self.row:
                self.conn.execute("INSERT INTO raw VALUES(?,?,?,?)",(self.tid,self.row_no,json.dumps([c["v"] for c in self.row],ensure_ascii=False),int(any(c["h"] for c in self.row))))
                self.counts[self.tid]+=1;self.row_no+=1
            self.row=None
    def handle_data(self,data):
        if not self.skip and self.depth==1 and self.cell is not None:self.cell.append(data)

def build_index(src,db,progress):
    if os.path.exists(db):
        try:os.remove(db)
        except PermissionError:raise RuntimeError("Database is in use. Close the indexed viewer and try again.")
    con=sqlite3.connect(db)
    try:
        con.execute("PRAGMA journal_mode=WAL");con.execute("PRAGMA synchronous=NORMAL")
        con.execute("CREATE TABLE raw(tid INTEGER,rn INTEGER,cells TEXT,header INTEGER)")
        parser=Parser(con);total=os.path.getsize(src);read=0
        with open(src,"r",encoding="utf-8-sig",errors="replace") as f:
            while True:
                chunk=f.read(1024*1024)
                if not chunk:break
                parser.feed(chunk);read+=len(chunk)
                if read%(8*1024*1024)<1024*1024:con.commit();progress(read,total)
        parser.close();con.commit()
        candidates={k:v for k,v in parser.counts.items() if v}
        if not candidates:raise RuntimeError("No standard HTML table found. This report may use JavaScript or div-based rows.")
        tid=max(candidates,key=candidates.get)
        raw=con.execute("SELECT rn,cells,header FROM raw WHERE tid=? ORDER BY rn",(tid,)).fetchall()
        if len(raw)<2:raise RuntimeError("The largest table has fewer than two rows.")
        first=json.loads(raw[0][1])
        if raw[0][2]:headers=[x or f"Column {i+1}" for i,x in enumerate(first)];body=raw[1:]
        else:
            width=max(len(json.loads(x[1])) for x in raw);headers=[f"Column {i+1}" for i in range(width)];body=raw
        con.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT)")
        con.execute("CREATE TABLE records(id INTEGER PRIMARY KEY,cells TEXT,search_text TEXT)")
        con.execute("INSERT INTO meta VALUES('headers',?)",(json.dumps(headers,ensure_ascii=False),))
        try:con.execute("CREATE VIRTUAL TABLE fts USING fts5(search_text,content='records',content_rowid='id')");hasfts=True
        except sqlite3.OperationalError:hasfts=False
        n=0
        for item in body:
            vals=json.loads(item[1])
            if not any(str(v).strip() for v in vals):continue
            vals+=[""]*max(0,len(headers)-len(vals));vals=vals[:len(headers)]
            s=" ".join(str(v) for v in vals)
            cur=con.execute("INSERT INTO records(cells,search_text) VALUES(?,?)",(json.dumps(vals,ensure_ascii=False,separators=(",",":")),s))
            if hasfts:con.execute("INSERT INTO fts(rowid,search_text) VALUES(?,?)",(cur.lastrowid,s))
            n+=1
            if n%1000==0:con.commit()
        con.execute("INSERT INTO meta VALUES('count',?)",(str(n),));con.execute("INSERT INTO meta VALUES('fts',?)",("1" if hasfts else "0",))
        con.execute("DROP TABLE raw");con.commit()
        return n,len(headers),hasfts
    finally:con.close()

class ServerHandler(http.server.BaseHTTPRequestHandler):
    db=None
    def log_message(self,*a):pass
    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        if u.path=="/":
            b=VIEWER.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b);return
        if u.path!="/api/search":self.send_error(404);return
        try:
            args=urllib.parse.parse_qs(u.query);term=args.get("q",[""])[0][:200];page=max(1,int(args.get("page",["1"])[0]));size=min(1000,max(1,int(args.get("size",["250"])[0])))
            c=sqlite3.connect(self.db);headers=json.loads(c.execute("SELECT value FROM meta WHERE key='headers'").fetchone()[0]);fts=c.execute("SELECT value FROM meta WHERE key='fts'").fetchone()[0]=="1"
            if not term:
                total=c.execute("SELECT COUNT(*) FROM records").fetchone()[0];rows=c.execute("SELECT cells FROM records ORDER BY id LIMIT ? OFFSET ?",(size,(page-1)*size)).fetchall()
            elif fts and len(term.split())==1 and re.fullmatch(r"[\w\-]+",term,re.UNICODE):
                termq=term.replace('"','""')+'*';total=c.execute("SELECT COUNT(*) FROM fts WHERE fts MATCH ?",(termq,)).fetchone()[0]
                rows=c.execute("SELECT records.cells FROM fts JOIN records ON records.id=fts.rowid WHERE fts MATCH ? ORDER BY records.id LIMIT ? OFFSET ?",(termq,size,(page-1)*size)).fetchall()
            else:
                like="%"+term.replace("%","\\%").replace("_","\\_")+"%"
                total=c.execute("SELECT COUNT(*) FROM records WHERE search_text LIKE ? ESCAPE '\\'",(like,)).fetchone()[0]
                rows=c.execute("SELECT cells FROM records WHERE search_text LIKE ? ESCAPE '\\' ORDER BY id LIMIT ? OFFSET ?",(like,size,(page-1)*size)).fetchall()
            c.close();b=json.dumps({"headers":headers,"rows":[json.loads(x[0]) for x in rows],"total":total},ensure_ascii=False).encode()
            self.send_response(200);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
        except Exception as e:
            b=json.dumps({"error":str(e)}).encode();self.send_response(500);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)

class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title(APP_TITLE);self.geometry("850x690");self.minsize(740,580);self.configure(bg="#0b1220")
        self.src=tk.StringVar();self.out=tk.StringVar();self.status=tk.StringVar(value="Choose an HTML file. Auto mode builds the index and opens the viewer.")
        self.server=None;self.db=None;self.busy=False;self.make_ui()
    def make_ui(self):
        tk.Label(self,text="ZYNTRASEC",bg="#0b1220",fg="#54e38e",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=24,pady=(18,0))
        tk.Label(self,text="UNIVERSAL HTML ENGINE",bg="#0b1220",fg="#e8eef8",font=("Segoe UI",22,"bold")).pack(anchor="w",padx=24)
        tk.Label(self,text="AUTO WORKFLOW + MANUAL CONTROLS",bg="#0b1220",fg="#aab9cd").pack(anchor="w",padx=24,pady=(2,16))
        p=tk.Frame(self,bg="#111c2e",padx=16,pady=14);p.pack(fill="x",padx=24)
        tk.Label(p,text="SOURCE HTML FILE",bg="#111c2e",fg="#e8eef8").grid(row=0,column=0,sticky="w")
        ttk.Entry(p,textvariable=self.src).grid(row=1,column=0,sticky="ew",pady=(5,12));ttk.Button(p,text="Browse HTML...",command=self.pick_src).grid(row=1,column=1,padx=(10,0),pady=(5,12))
        tk.Label(p,text="OUTPUT FOLDER",bg="#111c2e",fg="#e8eef8").grid(row=2,column=0,sticky="w")
        ttk.Entry(p,textvariable=self.out).grid(row=3,column=0,sticky="ew",pady=(5,5));ttk.Button(p,text="Choose...",command=self.pick_out).grid(row=3,column=1,padx=(10,0),pady=(5,5));p.grid_columnconfigure(0,weight=1)
        tk.Label(self,text="ONE-CLICK AUTO MODE",bg="#0b1220",fg="#54e38e",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=24,pady=(14,3))
        self.auto_btn=ttk.Button(self,text="AUTO: BUILD INDEX + OPEN VIEWER",command=self.auto_run);self.auto_btn.pack(anchor="w",padx=24)
        tk.Label(self,text="MANUAL MODE",bg="#0b1220",fg="#54e38e",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=24,pady=(14,3))
        row=tk.Frame(self,bg="#0b1220");row.pack(fill="x",padx=24)
        ttk.Button(row,text="1. OPEN ORIGINAL HTML",command=self.open_original).pack(side="left",padx=(0,8))
        ttk.Button(row,text="2. BUILD / REBUILD INDEX",command=self.build_manual).pack(side="left",padx=(0,8))
        ttk.Button(row,text="3. OPEN INDEXED VIEWER",command=self.open_viewer).pack(side="left")
        tk.Label(self,textvariable=self.status,bg="#0b1220",fg="#e8eef8",wraplength=790,justify="left",anchor="w").pack(fill="x",padx=24,pady=16)
        tk.Label(self,text="Original HTML is never modified. Indexed mode supports standard HTML tables; JavaScript/div-based reports may need a specialized extractor.",bg="#0b1220",fg="#9eacc1",font=("Segoe UI",9),wraplength=790,justify="left").pack(anchor="w",padx=24)
    def pick_src(self):
        p=filedialog.askopenfilename(filetypes=[("HTML files","*.html *.htm"),("HTML and all files","*.html *.htm"),("All files","*.*")])
        if p:
            self.src.set(p)
            if not self.out.get():self.out.set(str(Path(p).with_name(Path(p).stem+"_indexed")))
    def pick_out(self):
        p=filedialog.askdirectory()
        if p:self.out.set(p)
    def validate(self):
        src=self.src.get().strip();out=self.out.get().strip()
        if not src or not os.path.isfile(src):messagebox.showerror("Select HTML","Select the original .html or .htm file in SOURCE HTML FILE. Do not select .sqlite.");return None
        if Path(src).suffix.lower() not in (".html",".htm"):messagebox.showerror("Wrong file type","SOURCE must be an .html or .htm file, not a SQLite database.");return None
        if not out:messagebox.showerror("Output folder","Choose an output folder.");return None
        os.makedirs(out,exist_ok=True)
        if os.path.abspath(src)==os.path.abspath(out):messagebox.showerror("Output folder","Choose a folder, not the source file.");return None
        return src,out
    def open_original(self):
        v=self.validate()
        if not v:return
        webbrowser.open(Path(v[0]).resolve().as_uri());self.status.set("Original HTML opened in browser.")
    def auto_run(self):
        v=self.validate()
        if not v:return
        self.start_build(v[0],v[1],auto=True)
    def build_manual(self):
        v=self.validate()
        if not v:return
        self.start_build(v[0],v[1],auto=False)
    def start_build(self,src,out,auto):
        if self.busy:return
        self.busy=True;self.auto_btn.configure(state="disabled");self.status.set("Indexing report… please wait. Progress will update below.")
        db=os.path.join(out,"zyntrasec_index.sqlite")
        threading.Thread(target=self.worker,args=(src,db,auto),daemon=True).start()
    def worker(self,src,db,auto):
        try:
            def progress(a,b):self.after(0,lambda:self.status.set(f"Parsing HTML: {a*100//max(1,b)}%"))
            n,cols,fts=build_index(src,db,progress);self.db=db
            self.after(0,lambda:self.done(n,cols,fts,auto))
        except Exception as e:self.after(0,lambda:self.failed(str(e)))
    def done(self,n,cols,fts,auto):
        self.busy=False;self.auto_btn.configure(state="normal")
        self.status.set(f"Index complete: {n:,} records • {cols} columns • FTS5 {'enabled' if fts else 'fallback'}.\nDatabase: {self.db}")
        messagebox.showinfo("Index complete",f"Records indexed: {n:,}\nColumns: {cols}\nNow opening indexed viewer." if auto else f"Records indexed: {n:,}\nColumns: {cols}\nUse OPEN INDEXED VIEWER when ready.")
        if auto:self.open_viewer()
    def failed(self,msg):
        self.busy=False;self.auto_btn.configure(state="normal");self.status.set("Indexing failed: "+msg);messagebox.showerror("Indexing failed",msg)
    def open_viewer(self):
        db=self.db
        if not db:
            out=self.out.get().strip()
            candidate=os.path.join(out,"zyntrasec_index.sqlite") if out else ""
            if candidate and os.path.isfile(candidate):db=candidate;self.db=db
        if not db or not os.path.isfile(db):messagebox.showerror("No index","First use AUTO mode or BUILD / REBUILD INDEX.");return
        try:
            if self.server is None or getattr(self.server,"db_path",None)!=db:
                if self.server:
                    self.server.shutdown();self.server.server_close()
                handler=type("BoundHandler",(ServerHandler,),{"db":db})
                self.server=socketserver.ThreadingTCPServer(("127.0.0.1",0),handler);self.server.daemon_threads=True;self.server.db_path=db
                threading.Thread(target=self.server.serve_forever,daemon=True).start()
            webbrowser.open(f"http://127.0.0.1:{self.server.server_address[1]}/")
            self.status.set("Indexed viewer opened. Keep this app running while using it.")
        except Exception as e:messagebox.showerror("Viewer error",str(e))
    def close(self):
        try:
            if self.server:self.server.shutdown();self.server.server_close()
        except Exception:pass
        self.destroy()
if __name__=="__main__":
    app=App();app.protocol("WM_DELETE_WINDOW",app.close);app.mainloop()
