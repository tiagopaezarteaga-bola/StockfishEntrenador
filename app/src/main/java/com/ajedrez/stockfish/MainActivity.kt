package com.ajedrez.stockfish

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewAssetLoader.AssetsPathHandler
import fr.axllvy.stockfish.Stockfish
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * Arquitectura del motor:
 *
 *   sfPrincipal  — Stockfish con NUM_HILOS reales. Maneja el juego y el análisis.
 *   sfClasificador — Stockfish independiente con NUM_HILOS reales. Clasifica puzzles
 *                    en background sin interferir con sfPrincipal.
 *
 * Dos instancias separadas = sin mezcla de líneas UCI, sin contención de estado.
 *
 * Puente JS ↔ Kotlin:
 *   JS → window.MotorNativo.enviarComando("p", cmd)   (p = "principal" | "clasificador")
 *   Kotlin → webView.evaluateJavascript("onLineaPrincipal(...)")
 *   Kotlin → webView.evaluateJavascript("onLineaClasificador(...)")
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    private var sfPrincipal: Stockfish?    = null
    private var sfClasificador: Stockfish? = null

    private val motorScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    // ── Puente JS ↔ Kotlin ─────────────────────────────────────────────────
    inner class PuenteMotor {

        /**
         * JS llama: window.MotorNativo.enviarComando("principal",  "go infinite")
         *           window.MotorNativo.enviarComando("clasificador", "go depth 12")
         */
        @JavascriptInterface
        fun enviarComando(instancia: String, cmd: String) {
            motorScope.launch {
                try {
                    when (instancia) {
                        "principal"    -> sfPrincipal?.sendCommand(cmd)
                        "clasificador" -> sfClasificador?.sendCommand(cmd)
                    }
                } catch (e: Exception) {
                    val cb = if (instancia == "clasificador") "onLineaClasificador" else "onLineaPrincipal"
                    enviarLinea(cb, "info string ERROR: ${e.message}")
                }
            }
        }

        @JavascriptInterface
        fun disponible(): Boolean = true
    }

    // ── Enviar una línea UCI al callback JS correspondiente ─────────────────
    private fun enviarLinea(callback: String, linea: String) {
        val quoted = org.json.JSONObject.quote(linea)
        webView.post {
            webView.evaluateJavascript("if(typeof $callback==='function')$callback($quoted);", null)
        }
    }

    // ── Arrancar las dos instancias ─────────────────────────────────────────
    private fun iniciarMotores() {
        motorScope.launch {
            // Motor principal
            try {
                sfPrincipal = Stockfish().also { sf ->
                    sf.start { linea ->
                        if (linea.isNotBlank()) enviarLinea("onLineaPrincipal", linea)
                    }
                }
                enviarLinea("onLineaPrincipal", "nativo_listo")
            } catch (e: Exception) {
                enviarLinea("onLineaPrincipal", "info string ERROR motor principal: ${e.message}")
            }

            // Motor clasificador (instancia completamente separada)
            try {
                sfClasificador = Stockfish().also { sf ->
                    sf.start { linea ->
                        if (linea.isNotBlank()) enviarLinea("onLineaClasificador", linea)
                    }
                }
                enviarLinea("onLineaClasificador", "nativo_listo")
            } catch (e: Exception) {
                enviarLinea("onLineaClasificador", "info string ERROR motor clasificador: ${e.message}")
            }
        }
    }

    // ── Lifecycle ────────────────────────────────────────────────────────────
    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val assetLoader = WebViewAssetLoader.Builder()
            .setDomain("appassets.androidplatform.net")
            .addPathHandler("/assets/", AssetsPathHandler(this))
            .build()

        webView = WebView(this)
        setContentView(webView)

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
        }

        webView.addJavascriptInterface(PuenteMotor(), "MotorNativo")

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                val response = assetLoader.shouldInterceptRequest(request.url) ?: return null
                val headers = HashMap<String, String>()
                response.responseHeaders?.let { headers.putAll(it) }
                headers["Cross-Origin-Opener-Policy"]   = "same-origin"
                headers["Cross-Origin-Embedder-Policy"] = "require-corp"
                headers["Cross-Origin-Resource-Policy"] = "same-origin"
                response.responseHeaders = headers
                return response
            }

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                iniciarMotores()
            }
        }

        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    override fun onDestroy() {
        super.onDestroy()
        try { sfPrincipal?.quit()    } catch (_: Exception) {}
        try { sfClasificador?.quit() } catch (_: Exception) {}
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
