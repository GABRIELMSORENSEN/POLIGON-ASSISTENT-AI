package com.poligon.local;
import android.app.*;import android.content.*;import android.os.*;
public class LocalService extends Service {
 public static void begin(Context c){c.startForegroundService(new Intent(c,LocalService.class));}
 public int onStartCommand(Intent i,int flags,int id){if(i!=null&&"STOP".equals(i.getAction())){LocalAgent.get(this).stop();stopSelf();return START_NOT_STICKY;}NotificationManager nm=getSystemService(NotificationManager.class);nm.createNotificationChannel(new NotificationChannel("local","IA local em execução",NotificationManager.IMPORTANCE_LOW));PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE);PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,LocalService.class).setAction("STOP"),PendingIntent.FLAG_IMMUTABLE);Notification n=new Notification.Builder(this,"local").setSmallIcon(com.poligon.local.R.drawable.ic_poligon).setContentTitle("POLIGON · IA local").setContentText("Modelo no dispositivo. Toque em Parar para liberar memória.").setContentIntent(open).setOngoing(true).addAction(new Notification.Action.Builder(null,"Parar",stop).build()).build();startForeground(11,n);return START_NOT_STICKY;}
 public IBinder onBind(Intent i){return null;}
 public void onDestroy(){LocalAgent.get(this).stop();super.onDestroy();}
}
