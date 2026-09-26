package com.ajedrez.stockfish

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewAssetLoader.AssetsPathHandler

/**
 * Actividad única: una WebView a pantalla completa que carga index.html
 * desde app/src/main/assets/ (donde también viven stockfish-19.js,
 * stockfish-19.wasm, manifest.json e icon.png).
 *
 * Stockfish 19 usa SharedArrayBuffer (hilos). Los navegadores -y WebView-
 * solo lo habilitan si el documento está servido con aislamiento de
 * origen (COOP/COEP). WebViewAssetLoader sirve los assets como si
 * vinieran de https://appassets.androidplatform.net/assets/..., y aquí
 * le añadimos esas tres cabeceras a cada respuesta.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

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

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                val response = assetLoader.shouldInterceptRequest(request.url) ?: return null
                val headers = HashMap<String, String>()
                response.responseHeaders?.let { headers.putAll(it) }
                headers["Cross-Origin-Opener-Policy"] = "same-origin"
                headers["Cross-Origin-Embedder-Policy"] = "require-corp"
                headers["Cross-Origin-Resource-Policy"] = "same-origin"
                response.responseHeaders = headers
                return response
            }
        }

        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
