"""Private llama.cpp process on loopback. Downloaded models are used locally."""
import json, os, platform, subprocess, sys, threading, time
from pathlib import Path
import httpx
from . import state
BASE=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
INSTALL=Path(sys.executable).parent if getattr(sys,'frozen',False) else BASE
PORT=int(os.environ.get('POLIGON_ENGINE_PORT','8841'))
URL=f'http://127.0.0.1:{PORT}'
process=None
mutex=threading.Lock()
progress='Pronto para carregar o modelo local'

def model_dir():return Path(state.get('model_dir',str(INSTALL/'models')))

def headers():return {'Authorization':'Bearer '+state.get('engine_key')}

def executable():
    custom=state.get('llama_executable','')
    if custom and Path(custom).is_file():return custom
    if os.name=='nt':return str(INSTALL/'runtime/llama-windows/llama-server.exe')
    import shutil
    return shutil.which('llama-server') or str(INSTALL/'runtime/llama-server')

def status():
    ready=False
    try:ready=httpx.get(URL+'/v1/models',headers=headers(),timeout=1).status_code==200
    except Exception:pass
    return {'ready':ready,'model':state.get('model','Qwen3.5-4B-Q4_K_M.gguf'),'model_exists':(model_dir()/state.get('model','Qwen3.5-4B-Q4_K_M.gguf')).is_file(),'runtime_exists':Path(executable()).is_file(),'message':progress,'gpu_layers':state.get('gpu_layers',99),'vision':(model_dir()/'mmproj-Qwen3.5-4B-F16.gguf').exists()}

def start():
    global process,progress
    with mutex:
        if status()['ready']:return
        if process and process.poll() is None:return
        model=model_dir()/state.get('model','Qwen3.5-4B-Q4_K_M.gguf')
        if not model.is_file():raise RuntimeError('Modelo local ausente. Abra Configurações e instale os modelos.')
        binary=executable()
        if not Path(binary).is_file():raise RuntimeError('Motor llama.cpp ausente. Execute a instalação dos componentes locais.')
        args=[binary,'-m',str(model),'--host','127.0.0.1','--port',str(PORT),'-c',str(state.get('context',8192)),'-ngl',str(state.get('gpu_layers',99)),'--parallel','1','--jinja','--reasoning','off','--api-key',state.get('engine_key')]
        projector=model_dir()/'mmproj-Qwen3.5-4B-F16.gguf'
        if projector.exists() and '4B' in model.name:args+=['--mmproj',str(projector)]
        log=(state.ROOT/'engine.log').open('w',encoding='utf-8')
        process=subprocess.Popen(args,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        progress='Carregando o modelo na memória…'

def ensure(timeout=120):
    global progress
    start();deadline=time.time()+timeout
    while time.time()<deadline:
        if status()['ready']:progress='Inferência local ativa';return
        if process and process.poll() is not None:
            tail=(state.ROOT/'engine.log').read_text(encoding='utf-8',errors='replace')[-1200:]
            raise RuntimeError('O motor local encerrou. Tente GPU = 0 nas configurações. '+tail)
        time.sleep(.5)
    raise RuntimeError('O modelo ainda está carregando. Tente novamente em alguns instantes.')

def stop():
    global process,progress
    if process and process.poll() is None:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill()
    process=None;progress='Motor local pausado'

def chat(messages,tools=None,max_tokens=1024):
    ensure()
    body={'messages':messages,'temperature':.2,'max_tokens':max_tokens,'chat_template_kwargs':{'enable_thinking':False}}
    if tools:body.update(tools=tools,tool_choice='auto')
    with httpx.Client(timeout=240) as client:
        r=client.post(URL+'/v1/chat/completions',headers=headers(),json=body)
        if r.status_code>=400:raise RuntimeError('Inferência local: '+r.text[:500])
        return r.json()['choices'][0]['message']
