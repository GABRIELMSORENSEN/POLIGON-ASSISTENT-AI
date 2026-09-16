import subprocess,sys,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--name','POLIGON','--add-data','web;web','--add-data','models-manifest.json;.','--collect-all','webview','--hidden-import','uvicorn.logging','--hidden-import','uvicorn.loops.auto','--hidden-import','uvicorn.protocols.http.auto','--hidden-import','uvicorn.protocols.websockets.auto','--hidden-import','uvicorn.lifespan.on','poligon_assistent.py'],cwd=root,check=True)
dest=root/'dist/POLIGON'
shutil.copytree(root/'runtime',dest/'runtime',dirs_exist_ok=True)
for name in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md']:shutil.copy2(root/name,dest/name)
(root/'release').mkdir(exist_ok=True)
shutil.make_archive(str(root/'release/POLIGON-2.0.0-Windows-x64'),'zip',root/'dist','POLIGON')
print('Windows portable ready')
