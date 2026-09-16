"""POLIGON 2.0 launcher: opens a real desktop window; inference stays on this machine."""
import argparse, os, sys, threading, time
from pathlib import Path

def main():
    if sys.stdout is None or sys.stderr is None:
        folder=Path(os.environ.get('POLIGON_DATA',Path.home()/'.poligon'));folder.mkdir(parents=True,exist_ok=True)
        stream=(folder/'app.log').open('a',encoding='utf-8',buffering=1)
        sys.stdout=stream;sys.stderr=stream
    parser=argparse.ArgumentParser(description='POLIGON Local')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--port',type=int,default=8840)
    parser.add_argument('--host',default='127.0.0.1')
    args=parser.parse_args();os.environ['POLIGON_PORT']=str(args.port)
    import socket
    guard=socket.socket()
    try:guard.bind(('127.0.0.1',args.port))
    except OSError:
        raise SystemExit('O Poligon já está aberto ou a porta está ocupada.')
    finally:guard.close()
    from poligon import state
    state.init()
    import uvicorn
    from poligon.server import app
    config=uvicorn.Config(app,host=args.host,port=args.port,log_level='warning',access_log=False)
    server=uvicorn.Server(config)
    if args.headless:server.run();return
    worker=threading.Thread(target=server.run,daemon=True);worker.start()
    for _ in range(100):
        if server.started:break
        time.sleep(.1)
    url=f'http://127.0.0.1:{args.port}/#token='+state.get('owner_token')
    try:
        import webview
        webview.create_window('POLIGON · Inteligência local',url,width=1180,height=820,min_size=(760,600),background_color='#0b0d12')
        webview.start()
    except ImportError:
        import webbrowser
        webbrowser.open(url)
        try:
            while worker.is_alive():time.sleep(1)
        except KeyboardInterrupt:pass
    finally:server.should_exit=True;worker.join(timeout=10)

if __name__=='__main__':main()
