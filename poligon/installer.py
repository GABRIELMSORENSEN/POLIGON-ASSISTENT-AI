import hashlib,json,os,threading,urllib.request,zipfile
from pathlib import Path
from . import engine
progress='';running=False

def download(url,dest,expected=None):
    global progress
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and (not expected or hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()==expected):return
    temp=dest.with_suffix(dest.suffix+'.part')
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'POLIGON/2.0'}),timeout=60) as r,temp.open('wb') as f:
        size=int(r.headers.get('Content-Length',0));done=0
        while chunk:=r.read(1024*1024):
            f.write(chunk);done+=len(chunk);progress=f'{dest.name}: {done//1048576} MB'+(f' / {size//1048576} MB' if size else '')
    if expected and hashlib.file_digest(temp.open('rb'),'sha256').hexdigest()!=expected:
        temp.unlink();raise RuntimeError('Download corrompido. Tente novamente.')
    os.replace(temp,dest)

def install():
    global progress,running
    if running:return
    running=True
    def work():
        global progress,running
        try:
            manifest=json.loads((engine.BASE/'models-manifest.json').read_text())
            if os.name=='nt' and not Path(engine.executable()).exists():
                archive=engine.INSTALL/'runtime'/'llama.zip';info=manifest['runtime'];download(info['url'],archive,info['sha256'])
                dest=engine.INSTALL/'runtime'/'llama-windows';dest.mkdir(parents=True,exist_ok=True)
                with zipfile.ZipFile(archive) as z:
                    for item in z.infolist():
                        target=(dest/item.filename).resolve()
                        if not target.is_relative_to(dest.resolve()):raise RuntimeError('Arquivo compactado inválido')
                    z.extractall(dest)
                archive.unlink()
            for name,info in manifest['models'].items():
                if '0.8B' not in name:download(info['url'],engine.model_dir()/name,info['sha256'])
            progress='Instalação concluída. O modelo funciona sem internet.'
        except Exception as e:progress='Falha: '+str(e)
        finally:running=False
    threading.Thread(target=work,daemon=True).start()
