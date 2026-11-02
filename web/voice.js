"use strict";
(()=>{
 const $=id=>document.getElementById(id),native=typeof Android!=="undefined";
 const overlay=$("voice-overlay");if(!overlay)return;
 const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
 let session=false,recognition=null,listening=false,waiting=false,lastSpoken="";
 function state(text,mode=""){ $("voice-state").textContent=text;$("voice-orb").className="voice-orb"+(mode?" "+mode:"");}
 function stopMic(){if(native){try{Android.stopVoice()}catch(_){}}if(recognition){try{recognition.onend=null;recognition.stop()}catch(_){}}recognition=null;listening=false;}
 function stopAll(){session=false;waiting=false;stopMic();if("speechSynthesis"in window)window.speechSynthesis.cancel();state("Conversa por voz pausada.");}
 function open(){overlay.hidden=false;state("Converse com o Poligon usando sua voz.");$("voice-transcript").textContent="Toque em começar para falar."}
 function close(){stopAll();overlay.hidden=true}
 function submitTranscript(phrase){
  phrase=(phrase||"").trim();if(!phrase)return;
  if(/^(parar|pare|encerrar|sair do modo voz|desligar voz)[.! ]*$/i.test(phrase)){stopAll();$("voice-transcript").textContent="Modo de voz pausado.";return}
  waiting=true;stopMic();$("voice-transcript").textContent=phrase;state("Entendi. Estou preparando sua resposta…","thinking");$("prompt").value=phrase;$("composer").requestSubmit();
 }
 function listen(){
  if(!session||waiting||listening)return;
  if(native){listening=true;state("Preparando o microfone…","listening");try{Android.startVoice("poligon-voice")}catch(e){listening=false;state("Não foi possível iniciar o microfone: "+e.message)}return}
  if(!SpeechRecognition){state("Este navegador não oferece reconhecimento de voz. Use o botão Ditar no chat ou o microfone do sistema.");return}
  recognition=new SpeechRecognition();recognition.lang="pt-BR";recognition.interimResults=true;recognition.continuous=false;
  recognition.onstart=()=>{listening=true;state("Estou ouvindo você…","listening")};
  recognition.onresult=e=>{let interim="",finalText="";for(let i=e.resultIndex;i<e.results.length;i++){const text=e.results[i][0].transcript;if(e.results[i].isFinal)finalText+=text;else interim+=text}$("voice-transcript").textContent=finalText||interim||"";if(finalText.trim())submitTranscript(finalText)};
  recognition.onerror=e=>{listening=false;recognition=null;state("O microfone encontrou um problema: "+e.error);if(e.error==="not-allowed"||e.error==="service-not-allowed")session=false};
  recognition.onend=()=>{listening=false;recognition=null;if(session&&!waiting&&!overlay.hidden)state("Microfone pausado. Toque em continuar para falar.")};
  try{recognition.start()}catch(e){recognition=null;listening=false;state("Não foi possível iniciar o microfone: "+e.message)}
 }
 function speak(){
  if(!session||!waiting)return;
  const text=$("answer").textContent.trim();if(!text||text===lastSpoken)return;lastSpoken=text;
  if(native){state("Estou respondendo…","speaking");try{Android.speak(text)}catch(e){waiting=false;state("A resposta está no chat. Não consegui reproduzir o áudio.")}return}
  if(!("speechSynthesis"in window)){waiting=false;state("Resposta pronta no chat. A leitura em voz alta não está disponível.");return}
  const utterance=new SpeechSynthesisUtterance(text);utterance.lang="pt-BR";utterance.rate=1.02;utterance.pitch=1;
  const voices=window.speechSynthesis.getVoices();const voice=voices.find(v=>v.lang&&v.lang.toLowerCase()==="pt-br")||voices.find(v=>v.lang&&v.lang.toLowerCase().startsWith("pt"));if(voice)utterance.voice=voice;
  utterance.onstart=()=>state("Estou respondendo…","speaking");
  utterance.onend=()=>{waiting=false;if(session)listen()};
  utterance.onerror=()=>{waiting=false;state("A resposta está no chat. Não consegui reproduzir o áudio.");if(session)listen()};
  window.speechSynthesis.cancel();window.speechSynthesis.speak(utterance);
 }
 window.nativeVoiceState=mode=>{if(mode==="listening"){listening=true;state("Estou ouvindo você…","listening")}};
 window.nativeVoicePartial=text=>{$("voice-transcript").textContent=text||""};
 window.nativeVoiceResult=(id,text)=>{if(id!=="poligon-voice")return;listening=false;submitTranscript(text)};
 window.nativeVoiceError=(id,text)=>{if(id!=="poligon-voice")return;listening=false;state(text||"Falha no reconhecimento de voz.");};
 window.nativeSpeechDone=()=>{waiting=false;if(session)listen()};
 $("voice-open").addEventListener("click",open);$("voice-close").addEventListener("click",close);
 overlay.addEventListener("click",e=>{if(e.target===overlay)close()});
 $("voice-start").addEventListener("click",()=>{if(!native&&!SpeechRecognition){state("Reconhecimento de voz indisponível neste navegador. Use Ditar no chat.");return}session=true;waiting=false;state("Preparando o microfone…");listen()});
 $("voice-stop").addEventListener("click",()=>{waiting=false;stopMic();state("Microfone pausado. Toque em Começar a falar para continuar.")});
 const observer=new MutationObserver(()=>{if(!session||!waiting)return;if($("task-status").textContent==="Concluído"||$("task-status").textContent==="Falhou")speak()});
 observer.observe($("task-status"),{childList:true,characterData:true,subtree:true});
 document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!overlay.hidden)close()});
})();
