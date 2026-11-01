"""Shared, local-first memory for Polygon across chats and model adapters."""
import re, secrets, time
from . import state

def init():
    state.execute("""CREATE TABLE IF NOT EXISTS memory_items (
      id TEXT PRIMARY KEY, kind TEXT NOT NULL, scope TEXT NOT NULL,
      project TEXT NOT NULL DEFAULT '', content TEXT NOT NULL,
      source TEXT NOT NULL DEFAULT 'user_or_agent', confidence REAL NOT NULL DEFAULT 0.7,
      status TEXT NOT NULL DEFAULT 'proposed', user_confirmed INTEGER NOT NULL DEFAULT 0,
      sensitivity TEXT NOT NULL DEFAULT 'normal', created REAL NOT NULL, updated REAL NOT NULL
    )""")
    state.execute("CREATE INDEX IF NOT EXISTS idx_memory_scope ON memory_items(scope,project,updated)")

def add(content, kind="note", scope="global", project="", source="user_or_agent",
        confidence=0.7, status="confirmed", user_confirmed=False, sensitivity="normal"):
    init()
    content=str(content).strip()[:4000]
    if not content: raise ValueError("Memória vazia")
    if kind not in {"profile","preference","project_fact","decision","procedure","note","task"}:
        raise ValueError("Tipo de memória inválido")
    if scope not in {"global","project","conversation"}: raise ValueError("Escopo inválido")
    if not 0 <= float(confidence) <= 1: raise ValueError("Confiança deve ficar entre 0 e 1")
    now=time.time(); ident=secrets.token_hex(12)
    state.execute("""INSERT INTO memory_items
      (id,kind,scope,project,content,source,confidence,status,user_confirmed,sensitivity,created,updated)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
      (ident,kind,scope,project[:120],content,source[:240],float(confidence),status,
       int(bool(user_confirmed)),sensitivity,now,now))
    return get(ident)

def get(ident):
    init(); rows=state.rows("SELECT * FROM memory_items WHERE id=?",(ident,))
    return rows[0] if rows else None

def list_items(scope=None, project=None, limit=200):
    init(); sql="SELECT * FROM memory_items WHERE 1=1"; args=[]
    if scope: sql+=" AND scope=?"; args.append(scope)
    if project is not None: sql+=" AND project=?"; args.append(project)
    sql+=" ORDER BY user_confirmed DESC, updated DESC LIMIT ?"; args.append(max(1,min(int(limit),500)))
    return state.rows(sql,tuple(args))

def delete(ident):
    init(); state.execute("DELETE FROM memory_items WHERE id=?",(ident,))

def search(query, project="", limit=12, include_proposed=False):
    init()
    tokens=set(re.findall(r"[a-z0-9_À-ÿ]{3,}",(query or "").lower()))
    if not tokens: return []
    rows=list_items(limit=500)
    ranked=[]
    for item in rows:
        if item["status"]!="confirmed" and not include_proposed: continue
        if item["sensitivity"]!="normal": continue
        if item["scope"]=="project" and item["project"]!=project: continue
        words=set(re.findall(r"[a-z0-9_À-ÿ]{3,}",item["content"].lower()))
        overlap=len(tokens & words)
        if not overlap and item["scope"]!="global": continue
        score=overlap/max(1,len(tokens)) + (0.25 if item["user_confirmed"] else 0)
        if item["scope"]=="global": score+=0.1
        ranked.append((score,item))
    ranked.sort(key=lambda pair:(pair[0],pair[1]["updated"]),reverse=True)
    return [item for score,item in ranked[:max(1,min(limit,30))] if score>0]
