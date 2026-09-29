package com.example.ajedrezapk;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Inicializar el motor Python (Chaquopy)
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
        
        webView = new WebView(this);
        setContentView(webView);
        
        // Configurar WebView
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        // No necesitamos setSharedArrayBufferEnabled, 
        // las cabeceras HTTP de tu servidor Python lo activan automáticamente.
        
        webView.setWebViewClient(new WebViewClient());

        // Iniciar el servidor Python en un hilo en segundo plano
        new Thread(() -> {
            try {
                Python py = Python.getInstance();
                PyObject serverModule = py.getModule("ajedrez_servidor");
                // Llama a la función que añadiste al final de tu script
                serverModule.callAttr("iniciar_servidor_android");
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();

        // Esperar 1.5 segundos a que el servidor Python arranque y luego cargar la URL
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            webView.loadUrl("http://localhost:8000");
        }, 1500);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
