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
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.io.File
import java.io.PrintWriter

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    private var procPrincipal: Process?    = null
    private var procClasificador: Process? = null

    private var stdinPrincipal: PrintWriter?    = null
    private var stdinClasificador: PrintWriter? = null

    private val motorScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    inner class PuenteMotor {

        @JavascriptInterface
        fun enviarComando(instancia: String, cmd: String) {
            try {
                when (instancia) {
                    "principal" -> { stdinPrincipal?.println(cmd); stdinPrincipal?.flush() }
                    "clasificador" -> { stdinClasificador?.println(cmd); stdinClasificador?.flush() }
                }
            } catch (e: Exception) {
                val cb = if (instancia == "clasificador") "onLineaClasificador" else "onLineaPrincipal"
                enviarLinea(cb, "info string ERROR: ${e.message}")
            }
        }

        @JavascriptInterface
        fun disponible(): Boolean = true
    }

    private fun enviarLinea(callback: String, linea: String) {
        val quoted = org.json.JSONObject.quote(linea)
        webView.post {
            webView.evaluateJavascript("if(typeof $callback==='function')$callback($quoted);", null)
        }
    }

    private fun prepararBinario(): File {
        val destino = File(filesDir, "stockfish")
        if (!destino.exists()) {
            assets.open("stockfish").use { entrada ->
                destino.outputStream().use { salida ->
                    entrada.copyTo(salida)
                }
            }
        }
        destino.setExecutable(true, true)
        return destino
    }

    private fun lanzarMotor(binario: File, callback: String): Pair<Process, PrintWriter> {
        val proceso = ProcessBuilder(binario.absolutePath)
            .redirectErrorStream(false)
            .start()

        val stdin = PrintWriter(proceso.outputStream.bufferedWriter(), false)

        motorScope.launch {
            var listoEnviado = false
            proceso.inputStream.bufferedReader().forEachLine { linea ->
                if (linea.isNotBlank()) {
                    if (!listoEnviado && linea.trim() == "uciok") {
                        listoEnviado = true
                        enviarLinea(callback, "nativo_listo")
                    }
                    enviarLinea(callback, linea)
                }
            }
        }

        stdin.println("uci")
        stdin.flush()

        return Pair(proceso, stdin)
    }

    private fun iniciarMotores() {
        motorScope.launch {
            try {
                val binario = prepararBinario()

                val (pp, sp) = lanzarMotor(binario, "onLineaPrincipal")
                procPrincipal  = pp
                stdinPrincipal = sp
                enviarLinea("onLineaPrincipal", "nativo_listo")

                val (pc, sc) = lanzarMotor(binario, "onLineaClasificador")
                procClasificador  = pc
                stdinClasificador = sc
                enviarLinea("onLineaClasificador", "nativo_listo")

            } catch (e: Exception) {
                enviarLinea("onLineaPrincipal",    "info string ERROR inicio: ${e.message}")
                enviarLinea("onLineaClasificador", "info string ERROR inicio: ${e.message}")
            }
        }
    }

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
            javaScriptEnabled    = true
            domStorageEnabled    = true
            allowFileAccess      = false
            allowContentAccess   = false
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
        try { stdinPrincipal?.println("quit") }    catch (_: Exception) {}
        try { stdinClasificador?.println("quit") } catch (_: Exception) {}
        try { procPrincipal?.destroy() }           catch (_: Exception) {}
        try { procClasificador?.destroy() }        catch (_: Exception) {}
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
