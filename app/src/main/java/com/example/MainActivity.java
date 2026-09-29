package com.example.ajedrezapk;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;
import chaquopy.chaquopy.JavaPyObject;

public class MainActivity extends AppCompatActivity {

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        webView = new WebView(this);
        setContentView(webView);
        
        // Configurar WebView
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        // Soporte para SharedArrayBuffer (requerido por Stockfish WASM)
        settings.setSharedArrayBufferEnabled(true); 
        
        webView.setWebViewClient(new WebViewClient());

        // Iniciar el servidor Python en segundo plano
        new Thread(() -> {
            try {
                // Importar y ejecutar el script de Python
                JavaPyObject serverModule = JavaPyObject.importModule("ajedrez_servidor");
                serverModule.callAttr("iniciar_servidor_android");
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();

        // Esperar un segundo a que el servidor arranque y luego cargar la URL
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
