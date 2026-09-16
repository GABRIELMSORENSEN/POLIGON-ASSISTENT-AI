import asyncio, base64, hashlib, io, json, os, re, secrets, subprocess, threading, time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import __version__,state,engine,tools,agent,installer

state.init()
PAIR={'code':'','expires':0};attempts={};tunnel_process=None;tunnel_url=''
@asynccontextmanager
async def lifespan(app):
    agent.STOP.clear();threading.Thread(target=agent.worker,daemon=True,name='agent-worker').start()
    yield
    agent.STOP.set();engine.stop()
    if tunnel_process and tunnel_process.poll() is None:tunnel_process.terminate()
app=FastAPI(title='POLIGON Local',version=__version__,lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)

@app.middleware('http')
async def protection(request,call_next):
    try:length=int(request.headers.get('content-length','0') or 0)
    except ValueError:return JSONResponse({'detail':'Content-Length inválido'},400)
    if length>20*1024*1024:return JSONResponse({'detail':'Limite de 20 MB por requisição'},413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; media-src 'self' blob:; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    if request.url.path.startswith('/api'):response.headers['Cache-Control']='no-store'
    return response

def who(request:Request):
    token=request.headers.get('X-Poligon-Key','')
    if not token and request.headers.get('authorization','').startswith('Bearer '):token=request.headers['authorization'][7:]
    identity=state.auth(token)
    if not identity:raise HTTPException(401,'Conecte este dispositivo usando o código de pareamento do PC.')
    return identity

def owner(identity=Depends(who)):
    if identity!='owner':raise HTTPException(403,'Ajuste disponível apenas no PC proprietário.')
    return identity

@app.post('/api/install')
def install(identity=Depends(owner)):
    installer.install();return {'ok':True}

@app.get('/api/health')
def health():return {'name':'POLIGON','version':__version__,'local_inference':True}

@app.get('/api/status')
def status(identity=Depends(who)):
    return {'install_progress':installer.progress,'version':__version__,'engine':engine.status(),'allow_actions':state.get('allow_actions',True),'owner':identity=='owner','remote_url':tunnel_url,'time':time.time(),'model_dir':str(engine.model_dir()),'pending':len(state.rows("SELECT id FROM tasks WHERE status IN ('queued','running','waiting')")),'memory_count':len(state.rows('SELECT id FROM memories'))}

class TaskIn(BaseModel):
    prompt:str=Field(min_length=1,max_length=12000)
    mode:str='auto'
@app.post('/api/tasks')
def create_task(body:TaskIn,identity=Depends(who)):
    if body.mode not in {'auto','review'}:raise HTTPException(400,'Modo inválido')
    pending=state.rows("SELECT id FROM tasks WHERE status IN ('queued','running','waiting')")
    if len(pending)>=20:raise HTTPException(429,'A fila já tem 20 tarefas. Aguarde concluir.')
    return {'id':state.new_task(body.prompt,identity,body.mode)}
@app.get('/api/tasks')
def tasks(identity=Depends(who)):
    return state.rows('SELECT id,prompt,status,created,updated,result,error,mode FROM tasks ORDER BY created DESC LIMIT 60')
@app.get('/api/tasks/{ident}')
def task(ident:str,identity=Depends(who)):
    t=state.task(ident)
    if not t:raise HTTPException(404,'Tarefa não encontrada')
    return t
@app.post('/api/tasks/{ident}/cancel')
def cancel(ident:str,identity=Depends(who)):
    t=state.task(ident)
    if not t:raise HTTPException(404,'Tarefa não encontrada')
    state.update(ident,cancel=1,status='cancelled' if t['status']=='queued' else t['status']);return {'ok':True}
class Decision(BaseModel):decision:str
@app.post('/api/tasks/{ident}/decision')
def decision(ident:str,body:Decision,identity=Depends(who)):
    if body.decision not in {'approve','reject'}:raise HTTPException(400,'Decisão inválida')
    t=state.task(ident)
    if not t or t['status']!='waiting':raise HTTPException(409,'Nenhuma ação aguardando revisão')
    state.update(ident,decision=body.decision);return {'ok':True}

class ToolIn(BaseModel):
    name:str
    arguments:dict=Field(default_factory=dict)
@app.post('/api/tool')
def tool(body:ToolIn,identity=Depends(who)):
    try:return tools.execute(body.name,body.arguments)
    except Exception as e:raise HTTPException(400,str(e))
@app.get('/api/screen')
def screen(identity=Depends(who)):
    if not state.get('allow_actions',True):raise HTTPException(403,'Acesso ao PC pausado')
    return tools.screenshot()

@app.get('/api/memories')
def memories(identity=Depends(who)):return state.rows('SELECT * FROM memories ORDER BY created DESC')
@app.delete('/api/memories/{ident}')
def delete_memory(ident:str,identity=Depends(who)):
    state.execute('DELETE FROM memories WHERE id=?',(ident,));return {'ok':True}
@app.get('/api/schedules')
def schedules(identity=Depends(who)):return state.rows('SELECT * FROM schedules ORDER BY due')
@app.delete('/api/schedules/{ident}')
def delete_schedule(ident:str,identity=Depends(who)):
    state.execute('DELETE FROM schedules WHERE id=?',(ident,));return {'ok':True}

class SettingsIn(BaseModel):
    allow_actions:bool|None=None
    gpu_layers:int|None=Field(default=None,ge=0,le=999)
    context:int|None=Field(default=None,ge=2048,le=16384)
    model_dir:str|None=None
@app.post('/api/settings')
def settings(body:SettingsIn,identity=Depends(owner)):
    values=body.model_dump(exclude_none=True)
    if 'model_dir' in values:
        if not Path(values['model_dir']).expanduser().is_dir():raise HTTPException(400,'Pasta de modelos não existe')
    if any(k in values for k in ('gpu_layers','context','model_dir')):engine.stop()
    for k,v in values.items():state.set(k,v)
    return {'ok':True}
@app.post('/api/engine/start')
def start_engine(identity=Depends(owner)):
    try:engine.start();return {'ok':True}
    except Exception as e:raise HTTPException(400,str(e))
@app.post('/api/engine/stop')
def stop_engine(identity=Depends(owner)):engine.stop();return {'ok':True}

@app.post('/api/pairing')
def pairing(identity=Depends(owner)):
    PAIR.update(code=str(secrets.randbelow(900000)+100000),expires=time.time()+600)
    return {'code':PAIR['code'],'expires':PAIR['expires'],'url':tunnel_url or f'http://127.0.0.1:{os.environ.get("POLIGON_PORT","8840")}'}
class PairIn(BaseModel):
    code:str=Field(min_length=6,max_length=6)
    name:str=Field(min_length=1,max_length=60)
@app.post('/api/pair')
def pair(body:PairIn,request:Request):
    ip=request.client.host;now=time.time();history=[t for t in attempts.get(ip,[]) if now-t<600]
    if len(history)>=5:raise HTTPException(429,'Muitas tentativas. Aguarde dez minutos.')
    if now>PAIR['expires'] or not secrets.compare_digest(body.code,PAIR['code']):
        attempts[ip]=history+[now];raise HTTPException(401,'Código inválido ou expirado. Gere outro no PC.')
    token=secrets.token_urlsafe(40);ident=secrets.token_hex(10)
    state.execute('INSERT INTO devices VALUES (?,?,?,?,?,0)',(ident,body.name,hashlib.sha256(token.encode()).hexdigest(),now,now));PAIR.update(code='',expires=0)
    return {'token':token,'device':ident,'name':body.name}
@app.get('/api/devices')
def devices(identity=Depends(owner)):
    return state.rows('SELECT id,name,created,last_seen,revoked FROM devices ORDER BY created DESC')
@app.delete('/api/devices/{ident}')
def revoke(ident:str,identity=Depends(owner)):
    state.execute('UPDATE devices SET revoked=1 WHERE id=?',(ident,));return {'ok':True}

@app.post('/api/remote/start')
def start_remote(identity=Depends(owner)):
    global tunnel_process,tunnel_url
    if tunnel_process and tunnel_process.poll() is None:return {'url':tunnel_url,'starting':not bool(tunnel_url)}
    binary=engine.INSTALL/'runtime'/('cloudflared.exe' if os.name=='nt' else 'cloudflared')
    if not binary.exists():raise HTTPException(400,'Componente de conexão remota ausente. Execute scripts/setup.py.')
    tunnel_url=''
    logfile=state.ROOT/'tunnel.log'
    log=logfile.open('w',encoding='utf-8')
    tunnel_process=subprocess.Popen([str(binary),'tunnel','--url','http://127.0.0.1:'+os.environ.get('POLIGON_PORT','8840'),'--no-autoupdate'],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    def wait_url():
        global tunnel_url
        for _ in range(100):
            if not tunnel_process or tunnel_process.poll() is not None:return
            text=logfile.read_text(encoding='utf-8',errors='replace');match=re.search(r'https://[a-z0-9-]+\.trycloudflare\.com',text)
            if match:tunnel_url=match.group(0);return
            time.sleep(.3)
    threading.Thread(target=wait_url,daemon=True).start();return {'starting':True}
@app.post('/api/remote/stop')
def stop_remote(identity=Depends(owner)):
    global tunnel_process,tunnel_url
    if tunnel_process and tunnel_process.poll() is None:tunnel_process.terminate()
    tunnel_process=None;tunnel_url='';return {'ok':True}
@app.get('/api/pairing/qr')
def qr(identity=Depends(owner)):
    if not PAIR['code'] or time.time()>PAIR['expires']:raise HTTPException(400,'Gere um novo código')
    import qrcode
    from urllib.parse import urlencode
    uri='poligon://pair?'+urlencode({'url':tunnel_url or 'http://127.0.0.1:8840','code':PAIR['code']})
    out=io.BytesIO();qrcode.make(uri).save(out,format='PNG');return Response(out.getvalue(),media_type='image/png')

@app.post('/api/upload')
async def upload(file:UploadFile=File(...),identity=Depends(who)):
    folder=state.ROOT/'uploads';folder.mkdir(exist_ok=True)
    name=Path(file.filename or 'arquivo').name;name=re.sub(r'[^\w. -]','_',name)[:100]
    destination=folder/(secrets.token_hex(5)+'-'+name);total=0
    try:
        with destination.open('wb') as out:
            while chunk:=await file.read(65536):
                total+=len(chunk)
                if total>16*1024*1024:raise HTTPException(413,'Arquivo deve ter até 16 MB')
                out.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True);raise
    return {'path':str(destination),'size':total}

WEB=engine.BASE/'web'
@app.get('/')
def home():return FileResponse(WEB/'index.html')
app.mount('/assets',StaticFiles(directory=WEB),name='assets')
