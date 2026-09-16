"""Local persistence and pairing. No cloud account or inference credentials."""
import hashlib, json, os, secrets, sqlite3, threading, time
from pathlib import Path
ROOT = Path(os.environ.get("POLIGON_DATA", Path.home()/".poligon"))
ROOT.mkdir(parents=True, exist_ok=True)
LOCK = threading.RLock()
DB = ROOT/"poligon.db"

def db():
    c=sqlite3.connect(DB, timeout=20);c.row_factory=sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL");return c

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS devices (id TEXT PRIMARY KEY,name TEXT NOT NULL,token_hash TEXT NOT NULL,created REAL,last_seen REAL,revoked INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY,prompt TEXT,status TEXT,created REAL,updated REAL,mode TEXT,device TEXT,result TEXT DEFAULT '',error TEXT DEFAULT '',events TEXT DEFAULT '[]',approval TEXT DEFAULT '',decision TEXT DEFAULT '',cancel INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY,text TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS schedules (id TEXT PRIMARY KEY,prompt TEXT,due REAL,repeat_seconds INTEGER DEFAULT 0,enabled INTEGER DEFAULT 1);
        """)
        c.execute("UPDATE tasks SET status='interrupted',error='O aplicativo foi reiniciado. Reenvie para continuar.',updated=? WHERE status IN ('running','waiting')",(time.time(),))
    if not get('owner_token'):set('owner_token',secrets.token_urlsafe(40))
    if not get('engine_key'):set('engine_key',secrets.token_urlsafe(40))
    if get('allow_actions') is None:set('allow_actions',True)

def get(k,default=None):
    with LOCK,db() as c:
        r=c.execute('SELECT value FROM settings WHERE key=?',(k,)).fetchone()
    return json.loads(r[0]) if r else default

def set(k,v):
    with LOCK,db() as c:c.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',(k,json.dumps(v,ensure_ascii=False)))

def rows(sql,args=()):
    with LOCK,db() as c:return [dict(r) for r in c.execute(sql,args)]

def execute(sql,args=()):
    with LOCK,db() as c:c.execute(sql,args)

def auth(token):
    if not token:return None
    if secrets.compare_digest(token,get('owner_token','')):return 'owner'
    digest=hashlib.sha256(token.encode()).hexdigest()
    r=rows('SELECT id FROM devices WHERE token_hash=? AND revoked=0',(digest,))
    if r:
        execute('UPDATE devices SET last_seen=? WHERE id=?',(time.time(),r[0]['id']));return r[0]['id']
    return None

def new_task(prompt,device,mode='auto'):
    ident=secrets.token_hex(12);now=time.time()
    execute('INSERT INTO tasks(id,prompt,status,created,updated,mode,device) VALUES (?,?,?,?,?,?,?)',(ident,prompt,'queued',now,now,mode,device))
    return ident

def task(ident):
    r=rows('SELECT * FROM tasks WHERE id=?',(ident,))
    if not r:return None
    d=r[0];d['events']=json.loads(d['events']);return d

def update(ident,**values):
    allowed={'status','result','error','approval','decision','cancel'}
    if not values.keys()<=allowed:raise ValueError('Invalid task fields')
    values['updated']=time.time()
    execute('UPDATE tasks SET '+','.join(k+'=?' for k in values)+' WHERE id=?',(*values.values(),ident))

def event(ident,kind,text,detail=None):
    with LOCK:
        t=task(ident)
        if not t:return
        events=t['events'];events.append({'kind':kind,'text':text,'detail':detail,'at':time.time()})
        execute('UPDATE tasks SET events=?,updated=? WHERE id=?',(json.dumps(events[-80:],ensure_ascii=False),time.time(),ident))
