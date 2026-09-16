import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from poligon import state,installer
state.init();installer.install()
while installer.running:
 print(installer.progress,flush=True);time.sleep(2)
print(installer.progress)
if installer.progress.startswith('Falha'):sys.exit(1)
