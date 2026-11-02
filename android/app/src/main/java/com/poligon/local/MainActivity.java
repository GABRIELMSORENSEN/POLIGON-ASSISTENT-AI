package com.poligon.local;
import android.app.*;import android.os.*;import android.content.*;import android.content.pm.PackageManager;import android.Manifest;import android.net.Uri;import android.webkit.*;import android.view.*;import android.speech.*;import android.speech.tts.*;import org.json.*;import java.io.*;import java.util.*;import java.util.concurrent.*;
public class MainActivity extends Activity {
 private WebView web;private final ExecutorService pool=Executors.newFixedThreadPool(4);private boolean loaded=false;
 private SpeechRecognizer recognizer;private TextToSpeech tts;private String pendingVoiceId="";
 public void onCreate(Bundle b){super.onCreate(b);getWindow().setStatusBarColor(0xff111318);getWindow().setNavigationBarColor(0xff171a1f);web=new WebView(this);web.setBackgroundColor(0xff111318);setContentView(web);web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(false);web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);web.addJavascriptInterface(new Bridge(),"Android");
 web.setWebViewClient(new WebViewClient(){
 public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !r.getUrl().toString().startsWith("https://app.poligon.local/");}
 public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){try{Uri u=r.getUrl();if(!"app.poligon.local".equals(u.getHost()))return blocked();String path=u.getPath();String name=path.equals("/")?"index.html":path.startsWith("/assets/")?path.substring(8):"";if(!name.matches("[a-zA-Z0-9_.-]+"))return blocked();String mime=name.endsWith(".js")?"application/javascript":name.endsWith(".css")?"text/css":name.endsWith(".svg")?"image/svg+xml":"text/html";Map<String,String> h=new HashMap<>();h.put("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'");return new WebResourceResponse(mime,"UTF-8",200,"OK",h,getAssets().open("web/"+name));}catch(Exception e){return blocked();}}
 public void onPageFinished(WebView v,String url){loaded=true;deliverIntent(getIntent());}
 });web.loadUrl("https://app.poligon.local/");initTts();if(Build.VERSION.SDK_INT>=33&&checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=0)requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},7);
 }
 private WebResourceResponse blocked(){return new WebResourceResponse("text/plain","UTF-8",403,"Forbidden",new HashMap<>(),new ByteArrayInputStream(new byte[0]));}
 private void js(String code){runOnUiThread(()->{if(web!=null)web.evaluateJavascript(code,null);});}
 private void voiceResult(String id,String text){js("window.nativeVoiceResult&&window.nativeVoiceResult("+JSONObject.quote(id)+","+JSONObject.quote(text)+")");}
 private void voiceError(String id,String text){js("window.nativeVoiceError&&window.nativeVoiceError("+JSONObject.quote(id)+","+JSONObject.quote(text)+")");}
 private void initTts(){tts=new TextToSpeech(this,status->{if(status==TextToSpeech.SUCCESS){tts.setLanguage(Locale.forLanguageTag("pt-BR"));tts.setOnUtteranceProgressListener(new UtteranceProgressListener(){public void onStart(String id){}public void onDone(String id){js("window.nativeSpeechDone&&window.nativeSpeechDone()");}public void onError(String id){js("window.nativeSpeechDone&&window.nativeSpeechDone()");}});}});}
 private void startVoice(String id){
  if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){pendingVoiceId=id;requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},8);return;}
  if(!SpeechRecognizer.isRecognitionAvailable(this)){voiceError(id,"Reconhecimento de voz indisponível no Android.");return;}
  stopVoice();
  recognizer=SpeechRecognizer.createSpeechRecognizer(this);
  recognizer.setRecognitionListener(new RecognitionListener(){
   public void onReadyForSpeech(Bundle b){js("window.nativeVoiceState&&window.nativeVoiceState('listening')");}
   public void onBeginningOfSpeech(){}public void onRmsChanged(float v){}public void onBufferReceived(byte[] b){}public void onEndOfSpeech(){}
   public void onError(int error){voiceError(id,"Reconhecimento de voz: "+errorName(error));}
   public void onResults(Bundle b){ArrayList<String> a=b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);voiceResult(id,a==null||a.isEmpty()?"":a.get(0));}
   public void onPartialResults(Bundle b){ArrayList<String> a=b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);if(a!=null&&!a.isEmpty())js("window.nativeVoicePartial&&window.nativeVoicePartial("+JSONObject.quote(a.get(0))+")");}
   public void onEvent(int e,Bundle b){}
  });
  Intent intent=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE,"pt-BR");intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,"pt-BR");intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE,true);intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS,true);intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1);
  recognizer.startListening(intent);
 }
 private String errorName(int code){switch(code){case SpeechRecognizer.ERROR_AUDIO:return "erro de áudio";case SpeechRecognizer.ERROR_CLIENT:return "erro do cliente";case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:return "permissão de microfone ausente";case SpeechRecognizer.ERROR_NETWORK:return "erro de rede";case SpeechRecognizer.ERROR_NETWORK_TIMEOUT:return "tempo de rede esgotado";case SpeechRecognizer.ERROR_NO_MATCH:return "não entendi a fala";case SpeechRecognizer.ERROR_RECOGNIZER_BUSY:return "reconhecedor ocupado";case SpeechRecognizer.ERROR_SPEECH_TIMEOUT:return "nenhuma fala detectada";default:return "código "+code;}}
 private void stopVoice(){if(recognizer!=null){try{recognizer.cancel();recognizer.destroy();}catch(Exception ignored){}recognizer=null;}}
 private void speakText(String text){if(tts==null){initTts();}if(tts!=null){if(tts.isSpeaking())tts.stop();tts.speak(text,TextToSpeech.QUEUE_FLUSH,null,"poligon-voice");}else js("window.nativeSpeechDone&&window.nativeSpeechDone()");}
 @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] grantResults){super.onRequestPermissionsResult(requestCode,permissions,grantResults);if(requestCode==8){String id=pendingVoiceId;pendingVoiceId="";if(grantResults.length>0&&grantResults[0]==PackageManager.PERMISSION_GRANTED)startVoice(id);else voiceError(id,"Permissão de microfone negada.");}}
 protected void onNewIntent(Intent i){super.onNewIntent(i);setIntent(i);if(loaded)deliverIntent(i);}
 private void deliverIntent(Intent i){Uri u=i.getData();if(u!=null&&"poligon".equals(u.getScheme())&&"pair".equals(u.getHost()))web.evaluateJavascript("window.receivePair("+JSONObject.quote(u.getQueryParameter("url"))+","+JSONObject.quote(u.getQueryParameter("code"))+")",null);else if(Intent.ACTION_SEND.equals(i.getAction()))web.evaluateJavascript("window.receiveShared("+JSONObject.quote(i.getStringExtra(Intent.EXTRA_TEXT))+ ")",null);}
 class Bridge { @JavascriptInterface public void request(String id,String raw){pool.execute(()->{JSONObject out=new JSONObject();try{JSONObject r=new JSONObject(raw);Object data=LocalAgent.get(MainActivity.this).request(r);out.put("data",data);}catch(Exception e){try{out.put("error",e.getMessage()==null?e.toString():e.getMessage());}catch(Exception ignored){}}final String script="window.nativeResult("+JSONObject.quote(id)+","+out+")";runOnUiThread(()->web.evaluateJavascript(script,null));});}
  @JavascriptInterface public void startVoice(String id){runOnUiThread(()->startVoice(id));}
  @JavascriptInterface public void stopVoice(){runOnUiThread(()->MainActivity.this.stopVoice());}
  @JavascriptInterface public void speak(String text){runOnUiThread(()->speakText(text));}
 }
 @Override public void onBackPressed(){web.evaluateJavascript("document.querySelector('[data-page=assistant]').click()",null);}
 protected void onDestroy(){stopVoice();if(tts!=null){tts.stop();tts.shutdown();}web.removeJavascriptInterface("Android");web.destroy();pool.shutdown();super.onDestroy();}
}
