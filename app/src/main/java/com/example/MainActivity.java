package com.example.ajedrezapk;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Inicializar el motor Python (Chaquopy)
        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(this));
            }
        } catch (Exception e) {
            // Si Python falla al arrancar, muestra el error en pantalla
            Toast.makeText(this, "Error al iniciar Python: " + e.getMessage(), Toast.LENGTH_LONG).show();
            return;
        }
        
        webView = new WebView(this);
        setContentView(webView);
        
        // Configurar WebView
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        
        // WebView que muestra errores si los hay (para salir de la pantalla blanca)
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request.getUrl().toString().equals("http://localhost:8000")) {
                    runOnUiThread(() -> {
                        Toast.makeText(MainActivity.this, "Error de conexión. ¿Está corriendo el servidor Python?", Toast.LENGTH_LONG).show();
                    });
                }
            }
        });

        // Iniciar el servidor Python en un hilo en segundo plano
        new Thread(() -> {
            try {
                Python py = Python.getInstance();
                PyObject serverModule = py.getModule("ajedrez_servidor");
                // Llama a la función que añadiste al final de tu script
                serverModule.callAttr("iniciar_servidor_android");
            } catch (Exception e) {
                e.printStackTrace();
                // Si el script de Python falla, muéstralo en pantalla
                runOnUiThread(() -> {
                    Toast.makeText(this, "Error en Python: " + e.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }).start();

        // Esperar 3 segundos a que el servidor Python arranque y luego cargar la URL
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            webView.loadUrl("http://localhost:8000");
        }, 3000); // Aumentado a 3 segundos
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
