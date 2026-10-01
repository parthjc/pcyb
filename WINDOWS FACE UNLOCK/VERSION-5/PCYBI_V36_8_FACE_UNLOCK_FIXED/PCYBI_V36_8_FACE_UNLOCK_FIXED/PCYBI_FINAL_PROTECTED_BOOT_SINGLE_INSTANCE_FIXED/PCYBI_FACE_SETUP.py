import tkinter as tk
from tkinter import simpledialog, messagebox
import threading, time
from common import MODEL, detector, train, set_master_password, has_master_password, DATA_DIR, live_collect_pose

class Setup:
    def __init__(self):
        self.root=tk.Tk(); self.root.title('PCYBI // FACE SETUP')
        self.root.configure(bg='black'); self.root.geometry('760x560'); self.root.resizable(False,False)
        tk.Label(self.root,text='PCYBI // FACE REGISTRATION',fg='#00ff66',bg='black',font=('Segoe UI',26,'bold')).pack(pady=(45,15))
        tk.Label(self.root,text='ONE-TIME OWNER FACE + MASTER PASSWORD SETUP',fg='white',bg='black',font=('Segoe UI',13,'bold')).pack()
        tk.Label(self.root,text='Windows Camera will open automatically.\n5 photos will be captured for more reliable matching.\nBe clearly visible; small beard/hairstyle/clothing changes are supported.',fg='#b8ffcf',bg='black',font=('Segoe UI',12),justify='center').pack(pady=35)
        self.s=tk.StringVar(value='READY')
        tk.Label(self.root,textvariable=self.s,fg='#00ff66',bg='black',font=('Segoe UI',12,'bold'),wraplength=650).pack()
        self.root.after(500, self.start_setup)
    def status(self,x): self.root.after(0,self.s.set,x)
    def ask_password(self):
        while True:
            p=simpledialog.askstring('PCYBI Master Password','Create the emergency master password:',show='*',parent=self.root)
            if p is None: return False
            if len(p)<8:
                messagebox.showwarning('Password too short','Use at least 8 characters.',parent=self.root); continue
            q=simpledialog.askstring('PCYBI Master Password','Confirm the master password:',show='*',parent=self.root)
            if q != p:
                messagebox.showerror('Password mismatch','The passwords do not match.',parent=self.root); continue
            set_master_password(p); return True
    def start_setup(self):
        # Master password is required at the START of setup, before camera registration.
        if MODEL.exists() and has_master_password():
            self.status('FACE + MASTER PASSWORD ALREADY REGISTERED ✓')
            self.root.after(1500, self.root.destroy)
            return
        if not self.ask_password():
            self.status('MASTER PASSWORD REQUIRED — SETUP CANCELLED')
            self.root.after(1200, self.root.destroy)
            return
        self.status('MASTER PASSWORD SET ✓ → STARTING FACE REGISTRATION')
        self.root.after(700, lambda: threading.Thread(target=self.work, daemon=True).start())

    def countdown(self, instruction, seconds=3):
        for n in range(seconds, 0, -1):
            self.status(f'{instruction}\nGET READY... {n}')
            time.sleep(1)
        self.status(f'{instruction}\nCAPTURING NOW...')

    def work(self):
        try:
            d=detector(); faces=[]
            stages=[('LOOK LEFT',2.0),('LOOK RIGHT',2.0),('LOOK CENTER',2.0),('HOLD CENTER — LOOK STRAIGHT',2.0),('HOLD CENTER — STAY STILL',2.0)]
            for i,(instruction,duration) in enumerate(stages,1):
                self.status(f'FACE SETUP {i}/5\n{instruction}\nLIVE VIDEO — automatic capture')
                face=live_collect_pose(d,instruction,seconds=duration,settle=1.0)
                if face is None:
                    self.status(f'NO LIVE FACE CAPTURED — {instruction}\nSETUP NOT COMPLETE')
                    return
                faces.append(face)
                self.status(f'{instruction} ✓\nLIVE VIDEO SAMPLE {i}/5 SAVED')
                time.sleep(.7)
            train(faces)
            try: (DATA_DIR/'security_enabled.flag').write_text('PCYBI_SECURITY_ENABLED\n',encoding='utf-8')
            except Exception: pass
            self.status('5 LIVE VIDEO FACE SAMPLES REGISTERED ✓ → SETUP COMPLETE')
            self.root.after(0,self.finish_complete)
        except Exception as e:
            self.status('SETUP ERROR: '+str(e)[:180])
    def finish_complete(self):
        self.status('FACE + MASTER PASSWORD REGISTERED ✓  SETUP COMPLETE')
        time.sleep(1.5); self.root.destroy()
    def run(self): self.root.mainloop()
if __name__=='__main__': Setup().run()
