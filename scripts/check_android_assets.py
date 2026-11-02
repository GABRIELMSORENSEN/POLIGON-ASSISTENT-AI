from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
ANDROID = ROOT / "android/app/src/main/assets/web"
FILES = ("index.html", "app.js", "style.css", "logo.svg", "providers.js", "voice.js", "model-catalog.json")
missing = []
for name in FILES:
    source = WEB / name
    target = ANDROID / name
    if not source.is_file() or not target.is_file():
        missing.append(f"{name}: arquivo ausente")
    elif source.read_bytes() != target.read_bytes():
        missing.append(f"{name}: cópia Android desatualizada")
if missing:
    print("\n".join(missing))
    sys.exit(1)
print(f"Assets Android sincronizados ({len(FILES)} arquivos).")
