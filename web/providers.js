"use strict";
(()=>{
 const $=id=>document.getElementById(id);
 const token=()=>localStorage.getItem("poligon-token")||"";
 const native=typeof Android!=="undefined";
 const names={gemini:"Google Gemini API",openrouter:"OpenRouter",cerebras:"Cerebras Inference"};
 const notes={
  gemini:"Tem camada gratuita com limites por modelo e região. Confira a cota e a política de dados no Google AI Studio.",
  openrouter:"Use apenas variantes :free ou o roteador openrouter/free. O limite gratuito atual pode ser 20 req/min e 50 req/dia; pode mudar.",
  cerebras:"Atenção: o crédito de avaliação pode ser promocional, exigir cartão e expirar. Não é um plano gratuito permanente."
 };
 let models=[];
 async function api(path,method="GET",body){
  const r=await fetch("/api"+path,{method,headers:{"X-Poligon-Key":token(),...(body?{"Content-Type":"application/json"}:{})},body:body?JSON.stringify(body):undefined});
  const data=await r.json().catch(()=>({detail:"Resposta inválida"}));
  if(!r.ok)throw Error(data.detail||"Falha na conexão");
  return data;
 }
 function el(tag,txt,cls){const n=document.createElement(tag);if(txt!==undefined)n.textContent=txt;if(cls)n.className=cls;return n}
 function message(text,error=false){const n=$("provider-message");if(!n)return;n.textContent=text;n.classList.toggle("error",error)}
 function optionList(provider,items,selected){
  models=models.filter(x=>x.provider!==provider);
  for(const item of items)models.push({provider,id:item.id,name:item.name||item.id,note:item.free_note||""});
  renderSelect(selected);
 }
 function renderSelect(selected){
  const s=$("online-model"),previous=selected?selected.provider+"|"+selected.model:s.value;s.replaceChildren();
  if(!models.length){s.append(el("option","Conecte um provedor primeiro"));s.disabled=true;$("online-select").disabled=true;return}
  models.sort((a,b)=>a.provider.localeCompare(b.provider)||a.name.localeCompare(b.name));
  for(const m of models){const o=el("option",names[m.provider]+" · "+m.name);o.value=m.provider+"|"+m.id;s.append(o)}
  s.disabled=false;$("online-select").disabled=false;
  if(previous&&[...s.options].some(o=>o.value===previous))s.value=previous
 }
 async function fetchModels(provider,card){
  const button=card.querySelector("[data-refresh]");
  button.disabled=true;button.textContent="Buscando…";
  try{const result=await api("/providers/"+provider+"/models");optionList(provider,result.models||[]);message((result.models||[]).length+" modelos encontrados em "+names[provider]+". Selecione um e clique em Usar este modelo.");}
  catch(e){message(e.message,true)}
  finally{button.disabled=false;button.textContent="Atualizar modelos"}
 }
 async function load(){
  const root=$("provider-cards");if(!root)return;
  if(native){root.replaceChildren(el("p","Conecte os provedores na versão Windows do Poligon. Depois, escolha IA do PC no seletor do chat do celular para usar o modelo online configurado.","empty"));return}
  try{
   const overview=await api("/providers");root.replaceChildren();models=[];
   for(const p of overview.providers||[]){
    const card=el("article",undefined,"provider-card online-provider");
    const head=el("div",undefined,"online-provider-head");
    const info=el("div");info.append(el("h3",names[p.id]||p.name),el("p",notes[p.id]||p.free_note||""));
    const state=el("span",p.connected?"Conectado":"Não conectado","provider-state");head.append(info,state);card.append(head);
    const controls=el("div",undefined,"provider-controls");
    const key=el("input");key.type="password";key.autocomplete="off";key.placeholder=p.connected?"Chave salva no cofre do sistema":"Cole sua chave de API";key.setAttribute("aria-label","Chave API "+p.name);
    const connect=el("button",p.connected?"Atualizar conexão":"Conectar","outline");connect.type="button";
    connect.onclick=async()=>{
     if(!key.value.trim()){message("Cole a chave de API de "+p.name+".",true);key.focus();return}
     connect.disabled=true;connect.textContent="Validando chave…";
     try{const result=await api("/providers/"+p.id+"/connect","POST",{api_key:key.value.trim()});key.value="";state.textContent="Conectado";state.classList.add("connected");key.placeholder="Chave salva no cofre do sistema";optionList(p.id,result.models||[]);message("Chave validada. "+(result.models||[]).length+" modelos encontrados. Escolha um modelo e ative.");}
     catch(e){message(e.message,true)}
     finally{connect.disabled=false;connect.textContent="Atualizar conexão"}
    };
    const refresh=el("button","Atualizar modelos","outline");refresh.type="button";refresh.dataset.refresh="1";refresh.onclick=()=>fetchModels(p.id,card);
    controls.append(key,connect,refresh);
    if(p.connected){const disconnect=el("button","Desconectar","text-button");disconnect.type="button";disconnect.onclick=async()=>{disconnect.disabled=true;try{await api("/providers/"+p.id,"DELETE");models=models.filter(x=>x.provider!==p.id);renderSelect();message(p.name+" desconectado. A IA local voltou a ser o padrão.");await load()}catch(e){message(e.message,true)}finally{disconnect.disabled=false}};controls.append(disconnect)}
    card.append(controls);root.append(card);
    if(p.connected){try{const r=await api("/providers/"+p.id+"/models");optionList(p.id,r.models||[],overview.active_provider===p.id?{provider:p.id,model:overview.active_model}:null)}catch(e){message(e.message,true)}}
   }
   if(overview.active_provider==="local")message("IA offline ativa. Conecte um provedor e selecione um modelo para usar IA online.");
   else message("Modelo online selecionado: "+overview.active_provider+" · "+overview.active_model);
  }catch(e){root.replaceChildren(el("p","Não foi possível carregar os provedores: "+e.message,"empty"));message(e.message,true)}
 }
 $("online-select")?.addEventListener("click",async()=>{
  const value=$("online-model").value;if(!value||!value.includes("|"))return;
  const [provider,...rest]=value.split("|"),model=rest.join("|");
  const b=$("online-select");b.disabled=true;
  try{await api("/providers/select","POST",{provider,model});message("Modelo ativo: "+names[provider]+" · "+model+". Novas tarefas usarão este provedor.");const badge=document.getElementById("engine-badge");if(badge)badge.textContent="● IA online · "+provider;}
  catch(e){message(e.message,true)}finally{b.disabled=false}
 });
 $("online-local")?.addEventListener("click",async()=>{
  const b=$("online-local");b.disabled=true;
  try{await api("/providers/local","POST");message("IA local selecionada. As próximas tarefas serão executadas offline.");const badge=document.getElementById("engine-badge");if(badge)badge.textContent="○ IA local";}
  catch(e){message(e.message,true)}finally{b.disabled=false}
 });
 document.querySelector('[data-page="models"]')?.addEventListener("click",load);
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",load);else load();
})();
