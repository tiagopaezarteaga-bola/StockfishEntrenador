# Ajedrez · Stockfish 19 — APK

App Android (WebView) que envuelve el tablero de ajedrez + Stockfish 19
del proyecto `ajedrez_servidor.py`, con el motor (`stockfish-19.js` +
`stockfish-19.wasm`) precargado dentro del APK. Funciona 100% offline.

## Cómo se genera el APK
No hace falta Android Studio: al hacer `git push` a `main` (o al
disparar el workflow manualmente desde la pestaña **Actions**),
GitHub Actions compila el proyecto y deja el archivo `app-debug.apk`
como artefacto descargable en esa misma ejecución del workflow.

1. Sube este contenido a un repo nuevo en GitHub (ver más abajo).
2. Entra a la pestaña **Actions** del repo → espera a que termine
   "Build APK" (tarda varios minutos porque el .wasm pesa ~99 MB).
3. Abre esa ejecución → sección **Artifacts** → descarga
   `ajedrez-stockfish-apk.zip` → dentro está `app-debug.apk`.
4. Pasa el APK a tu teléfono e instálalo (activa "Instalar apps de
   fuentes desconocidas" para el navegador/gestor de archivos que uses).

## Por qué es tan grande
El .wasm de Stockfish 19 pesa ~99 MB y va sin comprimir dentro del APK
(`androidResources { noCompress += ['wasm','js'] }` en `app/build.gradle`)
para que el motor lo pueda leer directo. Es intencional: la app entera
funciona sin internet, sin pedirle nada al usuario.

## Cómo se resuelve el aislamiento de origen (COOP/COEP)
Stockfish 19 usa `SharedArrayBuffer`, que solo está disponible si la
página se sirve con cabeceras de aislamiento cruzado. `MainActivity.kt`
usa `WebViewAssetLoader` para servir `assets/` como si viniera de
`https://appassets.androidplatform.net/assets/...` y le agrega ahí las
cabeceras `Cross-Origin-Opener-Policy`, `Cross-Origin-Embedder-Policy`
y `Cross-Origin-Resource-Policy`.

## Estructura
```
AjedrezStockfish/
├── .github/workflows/build-apk.yml   ← el que compila el APK
├── build.gradle / settings.gradle / gradle.properties
└── app/
    ├── build.gradle
    ├── proguard-rules.pro
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/com/ajedrez/stockfish/MainActivity.kt
        ├── res/{values,mipmap-xxxhdpi}/...
        └── assets/
            ├── index.html          ← tablero + Stockfish (con auto-carga en APK)
            ├── manifest.json
            ├── icon.png
            ├── stockfish-19.js
            └── stockfish-19.wasm
```
