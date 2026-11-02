"use strict";
const $=id=>document.getElementById(id), native=typeof Android!=="undefined", callbacks=new Map();
let seq=0,token=localStorage.getItem('poligon-token')||'',target=native?'local':'pc',active=null,lastTask='',status={},screenSize=null,polling=false;
const fragment=new URLSearchParams(location.hash.slice(1));if(fragment.has('token')){token=fragment.get('token');localStorage.setItem('poligon-token',token);history.replaceState(null,'',location.pathname)}
function bridge(path,method='GET',body){return new Promise((resolve,reject)=>{const id=String(++seq);callbacks.set(id,{resolve,reject});Android.request(id,JSON.stringify({path,method,body:body||null,target}));setTimeout(()=>{if(callbacks.has(id)){callbacks.delete(id);reject(Error('O dispositivo demorou para responder.'))}},300000)})}
window.nativeResult=(id,result)=>{const c=callbacks.get(id);if(!c)return;callbacks.delete(id);result.error?c.reject(Error(result.error)):c.resolve(result.data)};
async function api(path,method='GET',body){if(native)return bridge(path,method,body);const r=await fetch('/api'+path,{method,headers:{'X-Poligon-Key':token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});let data=await r.json().catch(()=>({detail:'Resposta inválida do servidor'}));if(!r.ok)throw Error(data.detail||'Falha na conexão');return data}
function toast(text){$('toast').textContent=text;$('toast').style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').style.display='none',6500)}
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e}
let recognition=null,dictating=false;
function stopDictation(){if(recognition){try{recognition.stop()}catch(_){}}dictating=false;$('dictate').textContent='🎙 Ditar';$('dictate').setAttribute('aria-pressed','false')}
$('dictate').onclick=()=>{
 const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(!SpeechRecognition){toast('Ditado por voz não está disponível neste navegador. Você ainda pode usar o teclado ou o microfone do sistema.');return}
 if(dictating){stopDictation();return}
 recognition=new SpeechRecognition();recognition.lang='pt-BR';recognition.interimResults=true;recognition.continuous=false;
 recognition.onstart=()=>{dictating=true;$('dictate').textContent='■ Parar ditado';$('dictate').setAttribute('aria-pressed','true')};
 recognition.onresult=e=>{let finalText='';for(let i=e.resultIndex;i<e.results.length;i++)if(e.results[i].isFinal)finalText+=e.results[i][0].transcript+' ';if(finalText){const box=$('prompt');box.value+=(box.value.trim()?' ':'')+finalText.trim();box.dispatchEvent(new Event('input'));}};
 recognition.onerror=e=>{stopDictation();if(e.error!=='aborted')toast('Falha no ditado por voz: '+e.error)};
 recognition.onend=()=>{dictating=false;$('dictate').textContent='🎙 Ditar';$('dictate').setAttribute('aria-pressed','false')};
 try{recognition.start()}catch(e){stopDictation();toast('Não foi possível iniciar o microfone: '+e.message)}
};
$('speak-answer').onclick=()=>{
 if(!('speechSynthesis' in window)){toast('Leitura em voz alta não está disponível neste dispositivo.');return}
 if(window.speechSynthesis.speaking){window.speechSynthesis.cancel();$('speak-answer').textContent='▶ Ouvir resposta';return}
 const text=$('answer').textContent.trim();if(!text){toast('Ainda não há resposta para ouvir.');return}
 const utterance=new SpeechSynthesisUtterance(text);utterance.lang='pt-BR';utterance.rate=1;
 utterance.onend=()=>{$('speak-answer').textContent='▶ Ouvir resposta'};
 utterance.onerror=()=>{$('speak-answer').textContent='▶ Ouvir resposta';toast('Não foi possível reproduzir a resposta.')};
 $('speak-answer').textContent='■ Parar áudio';window.speechSynthesis.cancel();window.speechSynthesis.speak(utterance);
};
async function action(fn){try{await fn()}catch(e){toast(e.message)}}
function page(name){document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id==='page-'+name));document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active',x.dataset.page===name));$('page-title').textContent={assistant:'Assistente',models:'Modelos',remote:'Meu computador',memory:'Memória',schedule:'Agendamentos',settings:'Configurações',studio:'Studio'}[name];if(name==='models')action(loadModelCatalog);if(name==='memory')action(loadMemories);if(name==='schedule')action(loadSchedules);if(name==='remote')action(loadDevices);if(name==='studio')action(loadStudio)}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>page(b.dataset.page));document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>{$('prompt').value=b.dataset.prompt;$('prompt').focus()});
$('new-task').onclick=()=>{active=null;lastTask='';$('welcome').hidden=false;$('task-view').hidden=true;page('assistant');$('prompt').focus()};
$('prompt').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('composer').requestSubmit()}};
$('composer').onsubmit=e=>{e.preventDefault();action(async()=>{const prompt=$('prompt').value.trim();if(!prompt)return;$('send').disabled=true;try{const t=await api('/tasks','POST',{prompt,mode:$('mode').value});active=t.id;lastTask='';$('prompt').value='';await refreshTask();await loadHistory()}finally{$('send').disabled=false}})};
const labels={queued:'Na fila',running:'Executando',waiting:'Sua revisão',succeeded:'Concluído',failed:'Falhou',cancelled:'Interrompido',interrupted:'Sessão interrompida'};
async function refreshTask(){if(!active)return;const id=active,t=await api('/tasks/'+id);if(active!==id)return;const serialized=JSON.stringify(t);if(serialized===lastTask)return;lastTask=serialized;$('welcome').hidden=true;$('task-view').hidden=false;$('request').textContent=t.prompt;$('task-status').textContent=labels[t.status]||t.status;$('cancel-task').hidden=!['queued','running','waiting'].includes(t.status);$('answer').textContent=t.result||t.error||'';const events=$('events');events.replaceChildren();(t.events||[]).forEach(e=>{if(['answer','error'].includes(e.kind))return;const row=node('div',undefined,'event');if(e.detail){const d=node('details');d.append(node('summary',(e.kind==='tool'?'→ ':'✓ ')+e.text),node('pre',JSON.stringify(e.detail,null,2)));row.append(d)}else row.textContent=e.text;events.append(row)});$('approval').hidden=t.status!=='waiting';if(t.status==='waiting'){$('approval').replaceChildren(node('b','Revisar ação'),node('pre',t.approval));for(const [v,label] of [['approve','Executar'],['reject','Recusar']]){const b=node('button',label,'outline');b.onclick=()=>action(async()=>{await api('/tasks/'+id+'/decision','POST',{decision:v});await refreshTask()});$('approval').append(b)}}}
$('cancel-task').onclick=()=>action(async()=>{await api('/tasks/'+active+'/cancel','POST');toast('Interrupção solicitada. Uma ação já iniciada pode precisar terminar.');await refreshTask()});
async function loadHistory(){const list=await api('/tasks');$('history-list').replaceChildren();list.forEach(t=>{const b=node('div',undefined,'history-row');b.tabIndex=0;b.role='button';b.append(node('span',t.prompt),node('span',labels[t.status]||t.status));b.onclick=()=>{active=t.id;lastTask='';action(refreshTask)};b.onkeydown=e=>{if(e.key==='Enter')b.click()};$('history-list').append(b)})}
async function refreshStatus(){status=await api('/status');const e=status.engine,online=status.online||{},provider=online.active_provider||'local',automatic=provider==='auto';$('connection').textContent=native&&target==='local'?'Neste celular · offline':(automatic?'PC · IA automática':(provider!=='local'?'PC · IA online':'PC conectado'));$('engine-badge').textContent=automatic?'✦ IA automática · grátis primeiro':(provider!=='local'?'● IA online · '+provider:(e.ready?'● IA local ativa':'○ Modelo em espera'));$('model-info').replaceChildren(node('b',automatic?'Roteamento gratuito automático':(provider!=='local'?(online.active_model||provider):e.model)),node('p',automatic?'Tenta OpenRouter e Gemini gratuitos; se não responderem, usa a IA local.':(provider!=='local'?'Provedor online selecionado. Novas tarefas usarão o modelo remoto.':(e.model_exists?'Modelo instalado. ':'Modelo ainda não instalado. ')+(e.ready?'Pronto para conversar. ':e.message||'')+(e.vision?' Visão local disponível.':''))));$('model-dir').value=status.model_dir||'';$('gpu-layers').value=e.gpu_layers??0;$('remote-url').textContent=status.remote_url||'Túnel desconectado';$('owner-remote').hidden=!status.owner;$('pair-form').hidden=!native;$('pc-engine-settings').hidden=!status.owner||native;$('pause-actions').hidden=!status.owner;$('pause-actions').textContent=status.allow_actions?'Pausar acesso ao PC':'Retomar acesso ao PC';$('connect-overlay').hidden=true;$('install-progress').textContent=status.install_progress||''}
async function loadMemories(){const list=await api('/memories');renderList('memory-list',list,'Nenhuma memória salva.',m=>[m.text,new Date(m.created*1000).toLocaleString('pt-BR')],'/memories/')}
async function loadSchedules(){const list=await api('/schedules');renderList('schedule-list',list,'Nenhuma tarefa agendada.',s=>[s.prompt,new Date(s.due*1000).toLocaleString('pt-BR')+(s.repeat_seconds?' · Repetição a cada '+Math.round(s.repeat_seconds/60)+' min':'')+(s.enabled?'':' · Finalizada')],'/schedules/')}
function renderList(id,list,empty,format,route){$(id).replaceChildren();if(!list.length){$(id).append(node('div',empty,'empty'));return}for(const item of list){const row=node('div',undefined,'item'),info=node('div'),[title,sub]=format(item);info.append(node('div',title),node('small',sub));const b=node('button','Remover','text-button');b.onclick=()=>action(async()=>{await api(route+item.id,'DELETE');if(id==='memory-list')loadMemories();else loadSchedules()});row.append(info,b);$(id).append(row)}}
let modelCatalogLoaded=false;
async function loadModelCatalog(){
 const root=$('model-catalog');
 if(modelCatalogLoaded)return;
 root.replaceChildren(node('div','Carregando catálogo…','empty'));
 try{
  const response=await fetch('/assets/model-catalog.json',{cache:'no-store'});
  if(!response.ok)throw Error('Catálogo indisponível ('+response.status+').');
  const catalog=await response.json();
  const h=catalog.hardware_profile||{};
  $('model-catalog-notice').replaceChildren(
   node('b','Seu PC: '+(h.cpu||'CPU não identificada')+' · '+(h.ram_gb||'?')+' GB RAM · '+(h.gpu||'GPU não identificada')+' · '+(h.vram_gb||'?')+' GB VRAM'),
   node('p',h.recommendation||'Compatibilidade será verificada ao instalar cada modelo.'),
   node('p',catalog.resource_note||'Consumo de memória varia conforme contexto e runtime.')
  );
  root.replaceChildren();
  const labels={configured_manifest:'Previsto no instalador atual',partially_available:'Parcialmente disponível',catalog_only:'Catálogo — integração pendente',provider_pending:'Provedor — descoberta ao conectar',candidate:'Candidato — precisa validar'};
  for(const provider of catalog.providers||[]){
   const section=node('section',undefined,'provider-card');
   const head=node('div',undefined,'provider-head');
   const title=node('div');
   title.append(node('h3',provider.name),node('p',provider.description||''));
   const mode=node('span',provider.mode==='offline'?'OFFLINE':'ONLINE','provider-mode');
   head.append(title,mode);section.append(head);
   if(provider.docs){
    const a=node('a','Documentação oficial ↗');a.href=provider.docs;a.target='_blank';a.rel='noopener noreferrer';a.className='provider-docs';section.append(a);
   }
   const models=provider.models||[];
   if(!models.length)section.append(node('p','Os modelos serão descobertos no catálogo oficial quando o provedor for conectado.'));
   for(const model of models){
    const row=node('article',undefined,'model-row');
    const top=node('div',undefined,'model-row-top');
    const name=node('div');name.append(node('b',model.name),node('small',model.id));
    top.append(name,node('span',labels[model.status]||model.status,'model-status'));
    row.append(top);
    if(model.tasks&&model.tasks.length)row.append(node('div',model.tasks.join(' · '),'model-tags'));
    const specs=[model.parameters,model.intelligence_level,model.weights_q4_estimate,model.ram_estimate,model.vram_estimate].filter(Boolean);
    if(specs.length)row.append(node('div',specs.join(' · '),'model-specs'));
    if(model.focus)row.append(node('p','Foco: '+model.focus));
    if(model.hardware)row.append(node('p',model.hardware));
    if(model.cost)row.append(node('small',model.cost,'model-cost'));
    section.append(row);
   }
   root.append(section);
  }
  modelCatalogLoaded=true;
 }catch(error){root.replaceChildren(node('div','Não foi possível carregar o catálogo: '+error.message,'empty'))}
}
async function loadDevices(){if(!status.owner)return;const list=await api('/devices');$('devices').replaceChildren();for(const d of list.filter(d=>!d.revoked)){const row=node('div',undefined,'item'),b=node('button','Revogar','text-button');row.append(node('div',d.name));b.onclick=()=>action(async()=>{await api('/devices/'+d.id,'DELETE');await loadDevices()});row.append(b);$('devices').append(row)}}
$('remote-start').onclick=()=>action(async()=>{await api('/remote/start','POST');toast('Abrindo conexão segura…');await refreshStatus()});$('remote-stop').onclick=()=>action(async()=>{await api('/remote/stop','POST');$('pair-details').hidden=true;await refreshStatus()});
$('pair-generate').onclick=()=>action(async()=>{const p=await api('/pairing','POST');$('pair-code').textContent=p.code;$('pair-details').hidden=false;if(native){$('pair-qr').hidden=true}else{const r=await fetch('/api/pairing/qr',{headers:{'X-Poligon-Key':token}});if(!r.ok)throw Error('Falha ao gerar QR');if($('pair-qr').src.startsWith('blob:'))URL.revokeObjectURL($('pair-qr').src);$('pair-qr').src=URL.createObjectURL(await r.blob())}if(!status.remote_url)toast('Ative o acesso remoto antes de parear pela internet.')});
$('pair-form').onsubmit=e=>{e.preventDefault();action(async()=>{if(native){await bridge('/connect','POST',{url:$('pair-url').value,code:$('pair-input').value,name:$('pair-name').value});target='pc';$('target').value='pc'}else{const p=await api('/pair','POST',{code:$('pair-input').value,name:$('pair-name').value});token=p.token;localStorage.setItem('poligon-token',token)}$('pair-input').value='';toast('Dispositivo conectado.');await refreshStatus();await loadHistory();page('assistant')})};
$('go-pair').onclick=()=>{$('connect-overlay').hidden=true;page('remote');$('pair-form').hidden=false;$('owner-remote').hidden=true;$('pair-url').value=location.origin;$('pair-url').closest('label').hidden=!native};
$('screen-refresh').onclick=()=>action(async()=>{const s=await pcTool('screen_capture',{});$('screen').src=s.image;$('screen').hidden=false;screenSize={width:s.width,height:s.height}});
async function pcTool(name,args){if(native)return bridge('/pc-tool','POST',{name,arguments:args});return api('/tool','POST',{name,arguments:args})}
$('screen').onclick=e=>action(async()=>{if(!screenSize)return;const r=e.target.getBoundingClientRect();await pcTool('desktop_click',{x:Math.min(screenSize.width-1,Math.round((e.clientX-r.left)/r.width*screenSize.width)),y:Math.min(screenSize.height-1,Math.round((e.clientY-r.top)/r.height*screenSize.height))});$('screen-refresh').click()});
$('type-remote').onclick=()=>action(async()=>{await pcTool('desktop_type',{text:$('remote-text').value});toast('Texto enviado ao PC.')});document.querySelectorAll('[data-key]').forEach(b=>b.onclick=()=>action(()=>pcTool('desktop_keys',{keys:b.dataset.key.replaceAll(',','+')})));
$('engine-start').onclick=()=>action(async()=>{await api('/engine/start','POST');toast('Carregando modelo local…');await refreshStatus()});$('engine-stop').onclick=()=>action(async()=>{await api('/engine/stop','POST');await refreshStatus()});$('save-settings').onclick=()=>action(async()=>{await api('/settings','POST',{gpu_layers:Number($('gpu-layers').value),model_dir:$('model-dir').value});toast('Configurações salvas.');await refreshStatus()});$('pause-actions').onclick=()=>action(async()=>{await api('/settings','POST',{allow_actions:!status.allow_actions});await refreshStatus()});$('install-model').onclick=()=>action(async()=>{await api('/install','POST');toast('Instalação iniciada. O primeiro download pode demorar.');await refreshStatus()});
$('forget-connection').onclick=()=>action(async()=>{if(native){await bridge('/disconnect','POST');target='local';$('target').value='local';await refreshStatus()}else{localStorage.removeItem('poligon-token');token='';$('connect-overlay').hidden=false}toast('Conexão removida deste dispositivo.')});
$('target').hidden=!native;$('target').onchange=()=>action(async()=>{target=$('target').value;active=null;lastTask='';$('new-task').click();await refreshStatus();await loadHistory()});
$('file').onchange=()=>action(async()=>{const f=$('file').files[0];if(!f)return;if(native)throw Error('Para arquivos no celular, use Compartilhar com o Poligon.');const data=new FormData();data.append('file',f);const r=await fetch('/api/upload',{method:'POST',headers:{'X-Poligon-Key':token},body:data});const v=await r.json();if(!r.ok)throw Error(v.detail);$('prompt').value+='\nArquivo anexado: '+v.path;toast('Arquivo anexado.');$('file').value=''});
window.receivePair=(url,code)=>{page('remote');$('pair-url').value=url;$('pair-input').value=code;$('pair-form').hidden=false};
window.receiveShared=text=>{page('assistant');$('prompt').value=text};
async function tick(){if(polling||document.hidden)return;polling=true;try{await refreshStatus();await refreshTask()}catch(e){$('connection').textContent='Sem conexão';if(!native&&!token)$('connect-overlay').hidden=false}finally{polling=false}}
action(async()=>{await refreshStatus();await loadHistory()});if(!native&&!token)$('connect-overlay').hidden=false;setInterval(tick,2500);document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick()});


async function loadStudio(){
 if(native){document.querySelector('[data-page="studio"]').hidden=true;return}
 const data=await api('/studio/providers');const root=$('studio-providers');root.replaceChildren();
 (data.providers||[]).forEach(p=>{
  const card=node('article',undefined,'studio-provider');card.append(node('b',p.name),node('p',p.note),node('span',p.connected?'Conectado':'Não conectado','pill'));
  const key=node('input');key.type='password';key.autocomplete='off';key.placeholder='Cole sua chave de API';key.setAttribute('aria-label','Chave de API '+p.name);key.maxLength=512;
  const connect=node('button',p.connected?'Atualizar chave':'Conectar','outline');connect.onclick=()=>action(async()=>{if(!key.value.trim())throw Error('Informe a chave de API.');await api('/studio/providers/'+p.id+'/connect','POST',{api_key:key.value.trim()});key.value='';toast(p.name+' conectado com segurança.');await loadStudio()});
  const disconnect=node('button','Desconectar','text-button');disconnect.hidden=!p.connected;disconnect.onclick=()=>action(async()=>{await api('/studio/providers/'+p.id,'DELETE');toast(p.name+' desconectado.');await loadStudio()});
  const docs=node('a','Documentação ↗');docs.href=p.docs;docs.target='_blank';docs.rel='noopener noreferrer';
  card.append(key,connect,disconnect,docs);root.append(card);
 });
}
$('studio-load-voices').onclick=()=>action(async()=>{
 const result=await api('/studio/voices');const select=$('studio-voice');select.replaceChildren();
 (result.voices||[]).forEach(v=>{const option=document.createElement('option');option.value=v.voice_id;option.textContent=v.name+(v.category?' · '+v.category:'');select.append(option)});
 if(!select.options.length)throw Error('Nenhuma voz disponível para esta conta.');
 $('studio-speech-status').textContent=(result.voices||[]).length+' vozes carregadas.';
});
$('studio-speech-form').onsubmit=e=>{e.preventDefault();action(async()=>{
 const voice=$('studio-voice').value;if(!voice)throw Error('Carregue e selecione uma voz primeiro.');
 $('studio-speech-status').textContent='Gerando áudio…';const result=await api('/studio/speech','POST',{text:$('studio-speech-text').value,voice_id:voice,model_id:$('studio-voice-model').value});
 $('studio-audio').src=result.url;$('studio-audio').hidden=false;$('studio-audio-download').href=result.url;$('studio-audio-download').hidden=false;$('studio-speech-status').textContent='Áudio gerado · '+Math.round(result.bytes/1024)+' KB · '+result.characters+' caracteres.';
})};
$('studio-video-form').onsubmit=e=>{e.preventDefault();action(async()=>{
 $('studio-video-status').textContent='Enviando solicitação ao Runway…';$('studio-video-output').replaceChildren();
 const result=await api('/studio/video','POST',{prompt:$('studio-video-prompt').value,model:$('studio-video-model').value,ratio:$('studio-video-ratio').value,duration:Number($('studio-video-duration').value)});
 $('studio-video-task').value=result.task_id;$('studio-video-check').hidden=false;$('studio-video-status').textContent='Tarefa enviada · '+result.task_id+' · status: '+result.status+'.';
})};
$('studio-video-check').onclick=()=>action(async()=>{
 const id=$('studio-video-task').value;if(!id)throw Error('Nenhuma geração ativa.');
 const result=await api('/studio/video/'+encodeURIComponent(id));$('studio-video-status').textContent='Status: '+result.status+(result.failure?' · '+result.failure:'');
 const root=$('studio-video-output');root.replaceChildren();
 (result.output||[]).forEach((url,i)=>{if(typeof url!=='string'||!url.startsWith('https://'))return;const a=node('a','Abrir vídeo gerado '+(i+1)+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';root.append(a)});
 if(result.status==='SUCCEEDED'&&!(result.output||[]).length)$('studio-video-status').textContent+=' · Saída ainda não informada pelo provedor.';
});
if(native){const nav=document.querySelector('[data-page="studio"]');if(nav)nav.hidden=true}
