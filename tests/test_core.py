import os,tempfile,unittest,json
from pathlib import Path
_temp=tempfile.TemporaryDirectory();os.environ['POLIGON_DATA']=_temp.name
from poligon import state,tools
from poligon.server import app,PAIR
from fastapi.testclient import TestClient
class CoreTests(unittest.TestCase):
 def setUp(self):self.client=TestClient(app);self.headers={'X-Poligon-Key':state.get('owner_token')};state.set('allow_actions',True)
 def test_protected_routes(self):
  self.assertEqual(self.client.get('/api/tasks').status_code,401)
  self.assertEqual(self.client.post('/api/tool',json={'name':'system_info'}).status_code,401)
 def test_pair_single_use_revoke_and_owner_scope(self):
  p=self.client.post('/api/pairing',headers=self.headers).json()
  r=self.client.post('/api/pair',json={'name':'test phone','code':p['code']});self.assertEqual(r.status_code,200);d=r.json();h={'X-Poligon-Key':d['token']}
  self.assertEqual(self.client.get('/api/tasks',headers=h).status_code,200)
  self.assertEqual(self.client.post('/api/settings',headers=h,json={'allow_actions':False}).status_code,403)
  self.assertEqual(self.client.post('/api/pair',json={'name':'reuse','code':p['code']}).status_code,401)
  self.client.delete('/api/devices/'+d['device'],headers=self.headers)
  self.assertEqual(self.client.get('/api/tasks',headers=h).status_code,401)
 def test_real_file_backup_and_read(self):
  p=Path(_temp.name)/'test.txt';tools.execute('write_file',{'path':str(p),'content':'primeira versão'})
  r=tools.execute('write_file',{'path':str(p),'content':'segunda versão'})
  self.assertEqual(Path(r['backup']).read_text(encoding='utf-8'),'primeira versão')
  self.assertEqual(tools.execute('read_file',{'path':str(p)})['text'],'segunda versão')
 def test_pause_blocks_read_write_and_screen(self):
  state.set('allow_actions',False)
  for name,args in [('screen_capture',{}),('list_files',{'path':'~'}),('write_file',{'path':str(Path(_temp.name)/'no.txt'),'content':'no'})]:
   with self.assertRaises(PermissionError):tools.execute(name,args)
 def test_real_shell_failure_is_reported(self):
  r=tools.execute('run_shell',{'command':'Write-Output POLIGON_TEST; exit 7' if os.name=='nt' else 'echo POLIGON_TEST; exit 7','cwd':_temp.name})
  self.assertEqual(r['exit_code'],7);self.assertIn('POLIGON_TEST',r['output'])
 def test_memory_and_future_schedule(self):
  import datetime
  tools.execute('remember',{'text':'teste persistente'})
  self.assertTrue(any(x['text']=='teste persistente' for x in state.rows('SELECT * FROM memories')))
  when=(datetime.datetime.now().astimezone()+datetime.timedelta(hours=1)).isoformat()
  r=tools.execute('schedule_task',{'prompt':'teste','when':when})
  self.assertTrue(state.rows('SELECT * FROM schedules WHERE id=?',(r['scheduled'],)))
 def test_invalid_body_and_unknown_tool(self):
  self.assertEqual(self.client.post('/api/tasks',headers=self.headers,json={'prompt':''}).status_code,422)
  self.assertEqual(self.client.post('/api/tool',headers=self.headers,json={'name':'invented'}).status_code,400)
if __name__=='__main__':unittest.main()
