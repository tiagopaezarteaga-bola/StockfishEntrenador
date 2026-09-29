package com.example;

import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsIntent;

import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    private static boolean isServerRunning = false; // Evita reiniciar Python

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Iniciar Python solo una vez en la vida del proceso
        if (!isServerRunning) {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }
            } catch (Exception e) {
                Toast.makeText(this, "Error al iniciar Python: " + e.getMessage(), Toast.LENGTH_LONG).show();
                return;
            }

            // Iniciar el servidor Python en segundo plano
            new Thread(() -> {
                try {
                    Python py = Python.getInstance();
                    PyObject serverModule = py.getModule("ajedrez_servidor");
                    String filesDir = getFilesDir().getAbsolutePath();
                    serverModule.callAttr("iniciar_servidor_android", filesDir);
                    isServerRunning = true; // Marcar como arrancado
                } catch (Exception e) {
                    e.printStackTrace();
                    runOnUiThread(() -> {
                        Toast.makeText(this, "Error en Python: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    });
                }
            }).start();

            // Esperar 3 segundos a que el servidor arranque y luego abrir Chrome Custom Tab
            new Handler(Looper.getMainLooper()).postDelayed(() -> {
                abrirJuego();
            }, 3000);
        } else {
            // Si el servidor ya está corriendo, solo abrimos el juego directamente
            abrirJuego();
        }
    }

    private void abrirJuego() {
        String url = "http://localhost:8000";
        CustomTabsIntent.Builder builder = new CustomTabsIntent.Builder();
        builder.setShowTitle(true);
        CustomTabsIntent customTabsIntent = builder.build();
        customTabsIntent.launchUrl(this, Uri.parse(url));
        // NO ponemos finish() aquí, así la app y el servidor se quedan vivos
    }
}
