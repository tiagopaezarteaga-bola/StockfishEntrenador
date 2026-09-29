#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor local para "Ajedrez · Stockfish".

Uso:   python ajedrez_servidor.py          (puerto 8000)
       python ajedrez_servidor.py 8080     (otro puerto)
Luego abre  http://localhost:8000  en el navegador y sube
stockfish.js y stockfish.wasm en la pantalla de carga.

Por qué existe: Stockfish usa hilos (SharedArrayBuffer) y el navegador
solo lo permite si la página se sirve con las cabeceras COOP/COEP.
Este archivo lleva el HTML del juego dentro y las añade automáticamente.
Todo funciona sin internet; solo escucha en tu propio dispositivo.
"""
import sys
import json
import base64
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Puerto fijo: si cambia, el icono de "Agregar a pantalla de inicio" queda
# apuntando a una URL muerta. Antes de instalar el icono, deja este numero
# fijo y liberalo (cierra cualquier otra instancia del servidor).
PUERTO_FIJO = 8000

# Icono 512x512 PNG (peon simple), incrustado para mantener el .py como
# archivo unico. Se sirve en /icon.png y lo referencia manifest.json.
ICON_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAIAAAB7GkOtAAANdUlEQVR4nO3cTZIcRRKG4WRMp9ASY4fADDa6iI6pi7CBBbDDOAuLMqtpE6I76ycz3P17nu2AyAqF/I3IUs8379//uAGQ53+rHwCANQQAIJQAAIQSAIBQAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAKAEACCUAAKEEACCUAACEEgCAUAIAEEoAAEIJAEAoAQAIJQAAoQQAIJQAAIQSAIBQAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAqHerH6Co377/efUjAM/005+/rn6Ecr55//7H1c+wnnEPgSQhNwCGPnCVGYO4AJj7wCuiShAUAKMf2CkkA/MDYO4Dd5tdgskBMPqBp5iagZkBMPqBp5uXgYE/CGb6A0eYN1tG3QDm/fYABY25CswJwHOn/w9//f3EXw1Y7vfvvn3irzajARMC8JTRb+JDlKf0oHsG2gfgwelv7kO4B0vQugG9A3D39Df3gS/cXYK+DegaAKMfOEJUBloG4I7pb+4DN7mjBO0a0O/nAEx/4AR3zI12fxO92Q3g1vU1+oEH3XoVaHQP6BSAm6a/0Q880U0Z6NKANq+ATH9goZumSpd3QT0CYPoDy81rQINXQPvX0egHTrD/dVDxd0E9bgB7mP7AOcZMm+oB2Hn8H/P7AbSwc+YUfxFUOgCmP1DWgAbUDYDpDxTXvQF1A7CH6Q+s1XoKFQ3AnmC2XndgjD2zqOYloGIATH+gl6YNqBgAAE5QLgCO/0BHHS8BtQJg+gN9tWtArQC8yfQHKus1owoFoFQYAQ5SZ9YVCsCbeqUVyNRoUlUJQJ0kAhytyMSrEoA3NYoqEK7LvOoRgC6rCXDRYmqVCECR2xDAaSrMvRIBAOB86wPwZgZb3KQAvvDm7Fp+CVgfAACWqB4Ax3+gr+ITbHEAlt+AABZaOwOr3wAAOEjpABS/PQG8qfIcKx0AAI6zMgC+AABYOAnr3gAq35sA9is7zeoGAIBDCQBAKAEACCUAAKGWBeD1L77LfmcCcIfXZ9qqvwjkBgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAKAEACCUAAKEEACCUAACEEgCAUAIAEEoAAEIJAEAoAQAIJQAAoQQAIJQAAIQSAIBQAgAQSgAAQr1b/QBwkj9++bz/H/7w8dNxTwJFCABj3TTxX/939YCRBIBRHhn6O39ZMWAMAWCCg+b+6/8tJaA7AaC3M0f/V//TMkBfAkBXC0f/SzJAXwJAP0VG/0syQEcCQCcFR/9LMkAvAkAPxUf/SzJAF34SmAYaTf+rjs9MGjcASms9Rl0FKM4NgLpaT/+rGZ+CkQSAoibNzUmfhUm8AqKckePS6yAKcgOglpHT/2r2p6MdAaCQhPmY8BnpQgCoImcy5nxSihMASkibiWmfl5oEgPUyp2Hmp6YUAWCx5DmY/NmpQAAAQgkAKzkCWwEWEgCWMfsurAOrCABrmHovWQ2WEACAUALAAg68/2ZNOJ8AcDaT7r9YGU4mAAChBIBTOeS+zvpwJgEACCUAnMfxdg+rxGkEACCUAHASB9v9rBXnEACAUALAGRxpb2XFOIEAAIQSAA7nMHsf68bRBAAglAAAhBIAjuU9xiOsHocSAIBQAgAQSgAAQgkAB/IK+3HWkOMIAEAoAQAIJQAAoQQAIJQAcBTfXj6LleQgAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAKAEACCUAAKEEACCUAHCUDx8/rX6EIawkBxEAgFACABBKAABCCQBAKAHgQL69fJw15DgCABBKAABCCQBAKAHgWF5hP8LqcSgBAAglAAChBIDDeY9xH+vG0QQAIJQAcAaH2VtZMU4gAAChBICTONLuZ604hwAAhBIAzuNgu4dV4jQCABBKADiV4+3rrA9nEgCAUALA2Rxy/4uV4WQCwAIm3b9ZE84nAAChBIA1HHhfshosIQAsY+pdWAdWEQBWMvusAAsJAEAoAWCx5CNw8menAgFgvcw5mPmpKUUAKCFtGqZ9XmoSAKrImYk5n5TiBIBCEiZjwmekCwGgltnzcfano513qx8AvnSZkn/88nn1gzyT0U9BbgAUNWliTvosTCIA1DVjbs74FIzkFRCltX4dZPRTnBsADXScpB2fmTRuAPTQ6Cpg9NOFANBJ8QwY/fQiAPRTMANGPx0JAF0VyYDRT18CQG8LM2D0050AMMF1Fp9QAnOfMQSAUV5O5yfGwNBnJAFgrC+m9k09MPFJIACkMNPhC34SGCCUAACEEgCAUAIAEEoAAEIJAEAoAQAIJQAAoQQAIJQAAIQSAIBQAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAKAEACCUAAKEEACCUAACEEgCAUAIAEEoAAEIJAEAoAQAIJQAAoQQAIJQAAIQSAIBQAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAKAEACCUAAKEEACCUAACEEgCAUAIAEEoAAEIJAEAoAQAIJQAAoQQAIJQAAIQSAIBQAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABDq3eoH4Gx//PJ59SNQ14ePn1Y/AudxAwAIJQBZHP95nR0SRQAAQglAEIc79rBPcggAQCgBAAglACnc69nPbgkhAAChBCCCAx23smcSCABAKAEACCUA87nLcx87ZzwBAAglAMM5xPEI+2c2AQAIJQAAoQRgMvd3HmcXDSYAAKEEYCwHN57FXppKAABCCQBAKAGYyZ2d57KjRhIAgFACMJDDGkewr+YRAIBQAgAQSgCmcU/nOHbXMAIAEEoARnFA42j22CQCABBKAABCCcAc7uacw04bQwAAQgnAEA5lnMl+m0EAAEIJAEAoAZjAfZzz2XUDCABAKAFoz0GMVey97gQAIJQAAIQSgN7cwVnLDmxNAABCCUBjDl9UYB/2JQAAoQQAIJQAdOXeTR12Y1MCABBKAFpy4KIae7IjAQAIJQAAoQSgH3dtarIz2xEAgFAC0IxDFpXZn70IAEAoAQAIJQCduF9Tn13aiAAAhBKANhys6MJe7UIAAEIJAEAoAejBnZpe7NgWBAAglAA04DBFR/ZtfQIAEEoAAEIJQHXu0fRl9xYnAAChBKA0Byi6s4crEwCAUAIAEEoA6nJ3ZgY7uSwBAAglAEU5NDGJ/VyTAACEEgCAUAJQkfsy89jVBQkAQCgBKMdBians7WoEACCUAACEEoBa3JGZzQ4vRQAAQglAIQ5HJLDP6xAAgFACABBKAKpwLyaH3V6EAACEEoASHIhIY89XIAAAoQQAIJQArOcuTCY7fzkBAAglAIs5BJHM/l9LAABCCQBAKAFYyf0X/ClYSAAAQgnAMg4+cOHPwirvVj9AbzYuPMUjf5Q+fPz0xCeJ4gYAEEoAAEIJAEAoAQAIJQAAoQQAIJQAAIQSAIBQAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAqGUB+OnPX1/5X3//7tvTngTgaK/PtNfn4XHcAABCCQBAKAEACCUAAKHqBsD3wMAMZafZygCs+uIboI6Fk7DuDQCAQ5UOQNl7E8BOledY6QAAcJzFAfA1AJBs7QysfgOofHsCeF3xCVY9AAAcZH0A3rwBFU8owFe9ObuWvwNfHwAAligRgOUZBDhZhblXIgBv8hYI6KXF1OoRgK3JagJsfeZVlQBUuA0BnKPIxKsSgD26RBVI1mhSFQpAkSQCHKrOrHu3+gFu8/t33/7w19+rn+L/Pnz8tPoRgEIaHf+3UjeAbV8Ye60vkGPPdKpz/N+qBWDTAKCndtN/KxgAAM5RMQAuAUAvHY//W80AbBoA9NF0+m9lA7CTBgBrtZ5CdQOwM5itVx9obef8qXn83yoHYNMAoLDu038rHoBNA4CSBkz/rX4A9tMA4Bxjps0379//uPoZ3vbb9z/v/4dL/X9FAJPcNPqLH/+3LjeAm9ZxTJyBUoZN/61LADYNAJaaN/23Lq+Arm56F7R5HQQ87NYDZZfpv7ULwHZ7AzYZAO5yx7uERtN/a/QK6OqO9fVGCLjV+Om/dbwBXNxxD7hwGwBecfd5sd303/oG4EIGgGeJGv0XvQOwPdCACyWAcA++Iu47/bcBAdgebsCFEkCUp3w12Hr6bzMCcPGUDFzpAQzz3L8M0n30X8wJwPbsBgB81Yzpvw0LwIUMAAcZM/ov+v0cwJuG/Q4BRcybLQNvAFeuAsBTzBv9F5MDcCEDwN2mjv6L+QG4UgJgp9lz/yooABcyALwiZPRfxAXgSgmAq6i5f5UbgJfEAAJlDv2XBODrJAGGMe7/TQAAQg38QTAA9hAAgFACABBKAABCCQBAKAEACCUAAKEEACCUAACEEgCAUAIAEEoAAEIJAEAoAQAIJQAAoQQAIJQAAIQSAIBQAgAQSgAAQgkAQCgBAAglAAChBAAglAAAhBIAgFACABBKAABCCQBAKAEACCUAAKEEACCUAACEEgCAUAIAEEoAAEIJAEAoAQAI9Q+WBzt0DmBKLwAAAABJRU5ErkJggg=="

MANIFEST = json.dumps({
    "name": "Ajedrez vs Stockfish",
    "short_name": "Ajedrez SF19",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#1a1a2e",
    "theme_color": "#1a1a2e",
    "icons": [
        {"src": "/icon.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/icon.png", "sizes": "192x192", "type": "image/png"}
    ]
}, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ajedrez · Stockfish</title>
<link rel="manifest" href="/manifest.json">
<link rel="icon" href="/icon.png">
<link rel="apple-touch-icon" href="/icon.png">
<style>
  :root {
    --claro:#F0D9B5;--oscuro:#B58863;--borde:#8B6248;
    --fondo:#1a1a2e;--panel:#16213e;--acento:#e94560;
    --texto:#eaeaea;--muted:#888;--verde:#4caf50;
    --amarillo:#ffb300;--radio:8px;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--fondo);color:var(--texto);min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:24px 16px;}
  h1{font-size:22px;font-weight:500;margin-bottom:4px;}
  .subtitle{font-size:13px;color:var(--muted);margin-bottom:20px;}

  /* ── UPLOAD SCREEN ── */
  #uploadScreen{display:flex;flex-direction:column;align-items:center;gap:20px;width:100%;max-width:440px;}
  .upload-card{background:var(--panel);border-radius:12px;padding:28px 24px;width:100%;display:flex;flex-direction:column;gap:16px;border:0.5px solid #2a2a3e;}
  .upload-card p{font-size:13px;color:var(--muted);line-height:1.6;}
  .upload-card code{background:#0f0f1a;border-radius:4px;padding:2px 6px;font-size:12px;color:#7ec8e3;}
  .upload-zone{border:1.5px dashed #333;border-radius:var(--radio);padding:28px;text-align:center;cursor:pointer;transition:border-color .2s;}
  .upload-zone:hover,.upload-zone.drag{border-color:var(--acento);}
  .upload-zone .icon{font-size:32px;margin-bottom:8px;}
  .upload-zone p{font-size:13px;color:var(--muted);}
  .upload-zone input{display:none;}
  .link-small{font-size:12px;color:var(--acento);text-decoration:none;}
  .link-small:hover{text-decoration:underline;}

  /* ── GAME SCREEN ── */
  #gameScreen{display:none;flex-direction:column;align-items:center;width:100%;}
  .layout{display:grid;gap:24px;align-items:start;justify-content:center;width:100%;max-width:820px;margin:0 auto;grid-template-columns:1fr 300px;grid-template-areas:"board side" "anbajo anbajo";}
  .board-wrap{position:relative;grid-area:board;display:flex;justify-content:center;}
  #tablero{display:grid;grid-template-columns:repeat(8,1fr);width:440px;height:440px;border:3px solid var(--borde);border-radius:4px;overflow:hidden;cursor:pointer;user-select:none;}
  .casilla{width:55px;height:55px;display:flex;align-items:center;justify-content:center;font-size:36px;position:relative;}
  .casilla.claro{background:var(--claro);}
  .casilla.oscuro{background:var(--oscuro);}
  .casilla.sel{background:#f6f669aa!important;}
  .casilla.posible::after{content:'';width:28%;height:28%;border-radius:50%;background:rgba(0,0,0,.25);position:absolute;}
  .casilla.posible.ocupada::after{width:90%;height:90%;border-radius:50%;background:transparent;border:4px solid rgba(0,0,0,.25);}
  .coord-col{position:absolute;bottom:-18px;left:28px;width:440px;display:flex;}
  .coord-col span{width:55px;text-align:center;font-size:11px;color:var(--muted);}
  .coord-row{position:absolute;top:0;left:6px;height:440px;display:flex;flex-direction:column;pointer-events:none;}
  .coord-row span{height:55px;line-height:55px;font-size:11px;color:var(--muted);opacity:.75;}
  .panel{background:var(--panel);border-radius:12px;padding:20px;width:280px;min-width:0;display:flex;flex-direction:column;gap:18px;}
  .field label{display:block;font-size:12px;color:var(--muted);margin-bottom:6px;}
  .field label strong{color:var(--texto);font-weight:500;}
  .field input[type=number]{width:100%;background:#0f0f1a;border:0.5px solid #333;border-radius:var(--radio);color:var(--texto);font-size:18px;font-weight:500;padding:10px 14px;outline:none;transition:border-color .2s;}
  .field input[type=number]:focus{border-color:var(--acento);}
  .field input::-webkit-inner-spin-button{opacity:.4;}
  .btn{width:100%;padding:12px;border-radius:var(--radio);border:none;font-size:14px;font-weight:500;cursor:pointer;transition:opacity .15s,transform .1s;}
  .btn:active{transform:scale(.98);}
  .btn-primary{background:var(--acento);color:#fff;}
  .btn-secondary{background:#2a2a3e;color:var(--texto);}
  .btn:disabled{opacity:.4;cursor:not-allowed;}
  .divider{border:none;border-top:0.5px solid #2a2a3e;}
  .status-box{background:#0f0f1a;border-radius:var(--radio);padding:12px 14px;font-size:13px;min-height:48px;display:flex;align-items:center;gap:8px;}
  .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
  .dot.idle{background:var(--muted);}
  .dot.think{background:var(--amarillo);animation:pulse .8s infinite;}
  .dot.ok{background:var(--verde);}
  .dot.error{background:var(--acento);}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
  .timer-bar-wrap{height:4px;background:#2a2a3e;border-radius:2px;overflow:hidden;}
  #timerBar{height:100%;width:0%;background:var(--acento);transition:width .1s linear;border-radius:2px;}
  .move-info{font-size:12px;color:var(--muted);display:flex;justify-content:space-between;}
  .score-badge{background:#1e3a1e;color:var(--verde);border-radius:4px;padding:2px 8px;font-size:12px;font-weight:500;}
  .score-badge.neg{background:#3a1e1e;color:#ef9a9a;}
  #historial{font-size:12px;color:var(--muted);line-height:1.8;max-height:80px;overflow-y:auto;word-break:break-all;}
  .turno-wrap{display:flex;align-items:center;gap:8px;font-size:13px;}
  .turno-ficha{width:20px;height:20px;border-radius:50%;border:2px solid #555;}
  .turno-ficha.blancas{background:#fff;}
  .turno-ficha.negras{background:#222;}
  .sf-tag{font-size:11px;color:var(--muted);text-align:center;}
  @media(max-width:600px){
    #tablero{width:320px;height:320px;}
    .casilla{width:40px;height:40px;font-size:26px;}
    .coord-col{width:320px;}
    .coord-col span{width:40px;}
    .coord-row span{height:40px;line-height:40px;}
    .layout{grid-template-columns:1fr;grid-template-areas:"board" "anbajo" "side";}
  }
  .upload-zone.ok{border-color:var(--verde);border-style:solid;}
  .aviso{background:#3a1420;border:0.5px solid var(--acento);border-radius:var(--radio);padding:12px 14px;font-size:13px;line-height:1.5;color:#f3c1ca;}
  /* ── PESTAÑAS + ANÁLISIS ── */
  .side{width:300px;display:flex;flex-direction:column;gap:12px;grid-area:side;}
  .side .panel{width:100%;}
  .tabs{display:flex;background:var(--panel);border-radius:12px;padding:4px;gap:4px;}
  .tab{flex:1;padding:10px;border:none;border-radius:8px;background:transparent;color:var(--muted);font-size:14px;font-weight:500;cursor:pointer;}
  .tab.act{background:#2a2a3e;color:var(--texto);}
  .tab:focus-visible,.btn:focus-visible,.an-mov:focus-visible{outline:2px solid var(--acento);outline-offset:2px;}
  .an-sec{font-size:13px;font-weight:500;color:var(--texto);}
  .an-nota{font-size:12px;color:var(--muted);line-height:1.5;white-space:pre-line;}
  .an-msg{font-size:12px;line-height:1.5;padding:8px 10px;border-radius:var(--radio);background:#0f0f1a;color:var(--muted);display:none;}
  .an-msg.ok{display:block;color:#a5d6a7;}
  .an-msg.error{display:block;color:#f3c1ca;background:#3a1420;}
  .an-msg.info{display:block;}
  .fila{display:flex;gap:8px;flex-wrap:wrap;}
  .fila .btn{width:auto;flex:1;padding:10px 6px;font-size:13px;}
  label.btn{display:block;text-align:center;}
  label.btn input{display:none;}
  .btn-suave{background:transparent;color:var(--muted);border:0.5px solid #333;}
  textarea.an-txt,input.an-txt{width:100%;background:#0f0f1a;border:0.5px solid #333;border-radius:var(--radio);color:var(--texto);font-size:12px;padding:10px 12px;outline:none;font-family:inherit;}
  textarea.an-txt{resize:vertical;min-height:70px;}
  textarea.an-txt:focus,input.an-txt:focus{border-color:var(--acento);}
  .an-nav{display:flex;gap:8px;}
  .an-nav .btn{padding:10px 0;font-size:18px;line-height:1;}
  .an-lista{position:relative;background:#0f0f1a;border-radius:var(--radio);padding:10px;max-height:190px;overflow-y:auto;font-size:13px;line-height:2;color:var(--muted);}
  .an-num{color:#666;margin:0 4px 0 8px;font-size:12px;}
  .an-num:first-child{margin-left:0;}
  .an-mov{background:transparent;border:none;color:var(--texto);font-size:13px;padding:2px 6px;border-radius:4px;cursor:pointer;}
  .an-mov:hover{background:#2a2a3e;}
  .an-mov.act{background:var(--acento);color:#fff;}
  .an-mov.rango{background:#1e3a1e;}
  .an-mov.rango.act{background:var(--acento);}
  .an-mov.m-ini{box-shadow:inset 3px 0 0 var(--verde);}
  .an-mov.m-fin{box-shadow:inset -3px 0 0 var(--amarillo);}
  .an-mov.m-ini.m-fin{box-shadow:inset 3px 0 0 var(--verde),inset -3px 0 0 var(--amarillo);}
  .casilla.ult{background-image:linear-gradient(rgba(246,246,105,.45),rgba(246,246,105,.45));}
  .pz{background:#0f0f1a;border-radius:var(--radio);padding:10px 12px;display:flex;flex-direction:column;gap:8px;}
  .pz-nombre{font-size:13px;font-weight:500;}
  .pz .fila .btn{padding:7px 4px;font-size:12px;}
  #anPuzzles{display:flex;flex-direction:column;gap:8px;}
  @media(max-width:600px){ .side{width:100%;max-width:340px;} }
  /* ── ANÁLISIS: edición en tablero ── */
  .casilla.an-sel{background:#f6f669aa!important;}
  .casilla.an-posible::after{content:'';width:28%;height:28%;border-radius:50%;background:rgba(0,0,0,.25);position:absolute;}
  .casilla.an-posible.ocupada::after{width:90%;height:90%;border-radius:50%;background:transparent;border:4px solid rgba(0,0,0,.25);}
  /* ── ANÁLISIS: líneas SF ── */
  .sf-lines{background:#0f0f1a;border-radius:var(--radio);padding:10px;display:flex;flex-direction:column;gap:4px;font-size:12px;overflow-x:auto;min-width:0;}
  .sf-line{display:flex;gap:6px;align-items:baseline;padding:3px 4px;border-radius:4px;white-space:nowrap;width:max-content;min-width:100%;}
  .sf-line:hover{background:#1a1a2e;}
  .sf-line-score{min-width:44px;font-weight:600;color:var(--verde);flex-shrink:0;}
  .sf-line-score.neg{color:#ef9a9a;}
  .sf-line-score.mate{color:var(--amarillo);}
  .sf-line-movs{color:var(--texto);line-height:1.5;white-space:nowrap;flex-shrink:0;}
  .sf-line-vacia{color:var(--muted);font-style:italic;}
  .sf-anal-hdr{display:flex;justify-content:space-between;align-items:center;}
  .sf-anal-btn{background:var(--acento);color:#fff;border:none;border-radius:5px;padding:4px 10px;font-size:12px;cursor:pointer;font-weight:500;}
  .sf-anal-btn.stop{background:#555;}
  .sf-anal-btn:disabled{opacity:.4;cursor:not-allowed;}
  .an-turno{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:6px;}
  .an-turno-ficha{width:14px;height:14px;border-radius:50%;border:2px solid #555;display:inline-block;vertical-align:middle;}
  .an-turno-ficha.blancas{background:#fff;}
  .an-turno-ficha.negras{background:#222;}
  .sf-line-num{color:#666;font-size:11px;margin-right:1px;}
  .sf-line-san{color:var(--texto);}
  .sf-auto-label{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);cursor:pointer;user-select:none;padding:2px 0;}
  .toast{position:fixed;left:50%;top:18px;transform:translate(-50%,-140%);opacity:0;z-index:9999;pointer-events:none;
    background:#1b5e20;color:#e8f5e9;border:1px solid #66bb6a;border-radius:12px;padding:12px 22px;font-size:15px;font-weight:600;
    box-shadow:0 8px 24px rgba(0,0,0,.5);max-width:90vw;text-align:center;}
  .toast.info{background:#1a237e;border-color:#7986cb;color:#e8eaf6;}
  .toast.entra{animation:toastEntra .45s cubic-bezier(.2,.9,.3,1.2) forwards;}
  .toast.sale{animation:toastSale .4s ease-in forwards;}
  @keyframes toastEntra{from{transform:translate(-50%,-140%);opacity:0}to{transform:translate(-50%,0);opacity:1}}
  @keyframes toastSale{from{transform:translate(-50%,0);opacity:1}to{transform:translate(-50%,-140%);opacity:0}}
  .pz-orden{display:flex;gap:8px;align-items:center;font-size:12px;color:var(--muted);flex-wrap:wrap;}
  .pz-activa{align-items:center;justify-content:space-between;background:#1a1a2a;border-radius:8px;padding:6px 10px;margin:4px 0;}
  .pz-activa .an-nota{margin:0;flex:1;}
  .pz-cron{font-variant-numeric:tabular-nums;font-weight:700;color:#ffb74d;}
  .pz-stats{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);padding:2px 0;}
  .pz-stats b{color:#e0e0e0;}
  .pz-tiempo{font-size:11px;color:var(--muted);}
  .pz-orden select{background:#0f0f1a;color:inherit;border:1px solid #333;border-radius:6px;padding:4px 6px;}
  #anEditor:empty:before{content:attr(data-placeholder);color:#666;}
  #anEditor .an-jugada-act{background:var(--acento);color:#fff;border-radius:3px;padding:1px 2px;}
  .pieza-btn{width:38px;height:38px;padding:0;font-size:22px;line-height:1;display:flex;align-items:center;justify-content:center;flex:none;}
  .pieza-btn.activa{outline:2px solid var(--acento);background:#2a2a3e;}
</style>
</head>
<body>

<!-- ── PANTALLA DE CARGA ── -->
<div id="uploadScreen">
  <div class="upload-card" id="uploadCard">
    <div class="aviso" id="avisoIso" style="display:none;"></div>
    <p>Sube los <strong>dos archivos</strong> de Stockfish 19 (los dos son necesarios).<br>
    Puedes elegirlos uno por uno o soltar ambos a la vez.</p>
    <div class="upload-zone" id="zonaJs">
      <div class="icon">①</div>
      <p id="lblJs">Toca aquí para seleccionar <strong>stockfish.js</strong> (cualquier versión)</p>
      <input type="file" id="fileJs">
    </div>
    <div class="upload-zone" id="zonaWasm">
      <div class="icon">②</div>
      <p id="lblWasm">Toca aquí para seleccionar <strong>stockfish.wasm</strong> (cualquier versión ~90MB)</p>
      <input type="file" id="fileWasm">
    </div>
    <div class="status-box" id="uploadStatus" style="display:none;">
      <div class="dot think" id="uploadDot"></div>
      <span id="uploadMsg">Cargando…</span>
    </div>
  </div>
  <div class="upload-card" id="termuxCheatsheet" style="margin-top:16px;">
    <p style="margin-bottom:10px;"><strong>Comandos de Termux</strong> (para volver a abrir el servidor):</p>
    <p style="font-size:13px;line-height:2.1;color:var(--muted);">
      <code>cd ~/storage/downloads</code><br>
      <code>ps aux | grep ajedrez_servidor</code><br>
      <code>pkill -f ajedrez_servidor.py</code> <span style="opacity:.7;">(solo si hay uno viejo)</span><br>
      <code>python ajedrez_servidor.py</code>
    </p>
    <p style="font-size:12px;color:var(--muted);margin-top:8px;">Deja esa ventana abierta y entra a <code>http://localhost:8000</code>.</p>
  </div>
</div>

<!-- ── PANTALLA DE JUEGO ── -->
<div id="gameScreen">
  <div class="tabs" role="tablist" style="margin-bottom:12px;max-width:260px;">
    <button class="tab act" id="tabJugar" role="tab" type="button">Jugar</button>
    <button class="tab" id="tabAnalisis" role="tab" type="button">Análisis</button>
  </div>
  <div class="layout">
    <div class="board-wrap">
      <div class="coord-row" id="coordRow"></div>
      <div id="tablero"></div>
      <div class="coord-col" id="coordCol"></div>
    </div>
    <div class="side">
    <div class="panel" id="panelAnalisis" style="display:none">
      <hr class="divider" style="margin-top:0">
      <div class="an-sec">Crear un puzzle</div>
      <p class="an-nota">Ponte en la posición inicial y márcala, luego en la final y márcala. El puzzle será la posición inicial y las jugadas hasta la final.</p>
      <div class="fila">
        <button class="btn btn-secondary" id="anMarcaIni" type="button">Inicio aquí</button>
        <button class="btn btn-secondary" id="anMarcaFin" type="button">Fin aquí</button>
      </div>
      <div class="an-nota" id="anMarcaTxt"></div>
      <input class="an-txt" id="anPuzNombre" type="text" placeholder="Nombre del puzzle (opcional)" autocomplete="off" maxlength="60">
      <div class="fila">
        <button class="btn btn-primary" id="anCrearPuzzle" type="button">Crear puzzle</button>
        <button class="btn btn-suave" id="anQuitarMarcas" type="button">Quitar marcas</button>
      </div>
      <div class="pz-stats" id="anPzStats"></div>
      <button class="btn btn-suave" id="anResetElo" type="button" style="margin-top:6px;font-size:0.85em">Restablecer Elo</button>
      <div class="pz-orden" id="anOrdenBox">
        <label for="anOrden">Orden de los puzzles:</label>
        <select id="anOrden" autocomplete="off"><option value="normal">Normal</option><option value="aleatorio">Aleatorio</option></select>
        <button class="btn btn-secondary" id="anResolverTodos" type="button">Resolver todos</button>
      </div>
      <div id="anPuzzles"></div>
      <button class="btn btn-suave" id="anDescargarPuzzles" type="button">Descargar todos los puzzles (.json)</button>
    </div>
    <div class="panel" id="panelJugar">
      <div class="timer-bar-wrap"><div id="timerBar"></div></div>
      <div class="status-box">
        <div class="dot idle" id="dot"></div>
        <span id="statusMsg">Iniciando motor…</span>
      </div>
      <div class="move-info">
        <span id="lastMove">—</span>
        <span id="scoreBadge"></span>
      </div>
      <hr class="divider">
      <div class="turno-wrap">
        <div class="turno-ficha blancas" id="fichaActual"></div>
        <span id="turnoLabel">Turno: Blancas (tú)</span>
      </div>
      <div class="field" id="bandoField">
        <label><strong>Jugar con</strong></label>
        <div style="display:flex;gap:8px;margin-top:4px;">
          <button class="btn btn-secondary" id="btnBandoBlancas" style="flex:1;padding:9px 4px;font-size:13px;" type="button">♙ Blancas</button>
          <button class="btn btn-primary" id="btnBandoNegras" style="flex:1;padding:9px 4px;font-size:13px;background:#2a2a3e;color:var(--texto);" type="button">♟ Negras</button>
        </div>
      </div>
      <button class="btn btn-primary" id="btnNueva">Nueva partida</button>
      <button class="btn btn-secondary" id="btnUndo">Deshacer jugada</button>
      <div class="field">
        <label><strong>Jugar desde posición de partida</strong> (.pgn)</label>
        <input type="file" id="filePgn" accept=".pgn,.txt">
      </div>
      <div id="historial">Sin jugadas aún</div>
      <div class="field">
        <label><strong>Tiempo de análisis</strong> (segundos)<br>Se corta la búsqueda a los N segundos exactos</label>
        <input type="number" id="tiempo" value="5" min="1" max="30" step="1">
      </div>
      <div class="field">
        <label><strong>Número de jugadas</strong><br>Cuántas jugadas analiza Stockfish para escoger entre ellas</label>
        <input type="number" id="numJugadas" value="5" min="1" max="30" step="1">
      </div>
      <div class="field">
        <label id="lblUmbral"><strong>Ventaja de las blancas</strong><br>Peones (+ = ventaja blanca). Se juega la jugada que deje esa ventaja o la más cercana.</label>
        <input type="number" id="umbral" value="2.00" min="-20" max="20" step="0.25">
      </div>
      <p class="sf-tag" id="sfTag"></p>
    </div>
    </div>

  <!-- ── ZONA DEBAJO DEL TABLERO: solo visible en modo análisis ── -->
  <div id="anBajo" style="display:none;grid-area:anbajo;width:100%;min-width:0;margin-top:0;flex-direction:column;gap:12px;">
    <!-- Análisis de Stockfish -->
    <div class="panel" id="anPanelSF" style="width:100%;box-sizing:border-box;">
      <div class="an-sec sf-anal-hdr">
        <span>Análisis de Stockfish</span>
        <button class="sf-anal-btn" id="anAnalBtn" type="button" disabled>Analizar</button>
      </div>
      <div class="an-nav">
        <button class="btn btn-secondary" id="anInicio" type="button" title="Ir al inicio" aria-label="Ir al inicio">«</button>
        <button class="btn btn-secondary" id="anAnt" type="button" title="Jugada anterior" aria-label="Jugada anterior">‹</button>
        <button class="btn btn-secondary" id="anSig" type="button" title="Jugada siguiente" aria-label="Jugada siguiente">›</button>
        <button class="btn btn-secondary" id="anFinal" type="button" title="Ir al final" aria-label="Ir al final">»</button>
        <button class="btn btn-suave" id="anGirar" type="button" title="Girar tablero" aria-label="Girar tablero" style="font-size:18px;padding:10px 14px;">⇅</button>
      </div>
      <label class="sf-auto-label">
        <input type="checkbox" id="anAutoAnalizar" style="accent-color:var(--acento);width:14px;height:14px;">
        Analizar automáticamente al navegar / jugar
      </label>
      <div class="sf-lines" id="anSfLines">
        <div class="sf-line-vacia">El motor no ha analizado esta posición.</div>
      </div>
    </div>
    <!-- Editor manual de posición: agregar/quitar piezas, vaciar, posición inicial -->
    <div class="panel" style="width:100%;box-sizing:border-box;">
      <div class="an-sec sf-anal-hdr">
        <span>Configurar posición</span>
        <button class="sf-anal-btn" id="anEditarPosBtn" type="button">Editar posición</button>
      </div>
      <div id="anEditPosPanel" style="display:none;">
        <p class="an-nota">Toca una pieza de la paleta y luego una casilla del tablero para colocarla. Elige 🗑 para quitar piezas tocando el tablero.</p>
        <div class="fila" style="flex-wrap:wrap;gap:4px;margin-top:8px;" id="anPaletaBlancas"></div>
        <div class="fila" style="flex-wrap:wrap;gap:4px;margin-top:4px;" id="anPaletaNegras"></div>
        <div class="fila" style="margin-top:10px;gap:6px;">
          <button class="btn btn-secondary" id="anEditTurnoBlancas" type="button" style="font-size:12px;flex:1;">Turno: Blancas</button>
          <button class="btn btn-secondary" id="anEditTurnoNegras" type="button" style="font-size:12px;flex:1;">Turno: Negras</button>
        </div>
        <div class="fila" style="margin-top:8px;gap:6px;">
          <button class="btn btn-suave" id="anEditInicial" type="button" style="font-size:12px;flex:1;">Posición inicial</button>
          <button class="btn btn-suave" id="anEditVaciar" type="button" style="font-size:12px;flex:1;">Vaciar tablero</button>
        </div>
        <div class="fila" style="margin-top:8px;gap:6px;">
          <button class="btn btn-primary" id="anEditAplicar" type="button" style="font-size:12px;flex:1;">Aplicar</button>
          <button class="btn btn-suave" id="anEditCancelar" type="button" style="font-size:12px;flex:1;">Cancelar</button>
        </div>
      </div>
    </div>
    <!-- Partida unificada: textarea PGN editable + nav + lista -->
    <div class="panel" id="anPanelPartida" style="width:100%;box-sizing:border-box;">
      <div style="display:flex;gap:8px;align-items:flex-start;">
        <div id="anEditor" contenteditable="true" spellcheck="false" translate="no" autocapitalize="off" autocorrect="off" data-placeholder="Escribe o pega jugadas aquí (ej: 1. e4 e5 2. Nf3 …)" style="flex:1;min-height:100px;max-height:200px;overflow:auto;border:0.5px solid #333;border-radius:var(--radio);font-size:12px;font-family:inherit;line-height:1.7;padding:10px 12px;background:#0f0f1a;color:var(--texto);box-sizing:border-box;white-space:pre-wrap;word-break:break-word;outline:none;"></div>
        <div style="display:flex;flex-direction:column;gap:6px;min-width:120px;">
          <button class="btn btn-secondary" id="anCargarTexto" type="button" style="font-size:12px;padding:7px 10px;">Cargar PGN</button>
          <label class="btn btn-secondary" style="font-size:12px;padding:7px 10px;text-align:center;cursor:pointer;">Abrir archivo<input type="file" id="anFilePgn" accept=".pgn,.txt" style="display:none"></label>
          <button class="btn btn-secondary" id="anUsarActual" type="button" style="font-size:12px;padding:7px 10px;">Usar partida actual</button>
          <button class="btn btn-suave" id="anDescargar" type="button" style="font-size:12px;padding:7px 10px;">Descargar PGN</button>
        </div>
      </div>
      <div class="an-msg" id="anMsg"></div>
      <div class="fila pz-activa" id="anPuzzleBarra" style="display:none">
        <span class="an-nota" id="anPuzzleActivoTxt"></span>
        <span class="pz-cron" id="anPuzzleCron">0:00</span>
        <button class="btn btn-suave" id="anDetenerPuzzle" type="button">Detener puzzle</button>
      </div>
      <div class="toast" id="anToast"></div>
      <div class="fila" style="margin-top:8px;gap:6px;">
        <button class="btn btn-suave" id="anCortar" type="button" style="font-size:12px;flex:1;">Cortar desde aquí</button>
        <button class="btn btn-suave" id="anBorrar" type="button" style="font-size:12px;flex:1;">Borrar siguientes</button>
        <button class="btn btn-suave" id="anDeshacerEd" type="button" style="font-size:12px;flex:1;">↩ Deshacer</button>
      </div>
      <div class="an-nota" id="anPos" style="margin-top:10px;">Sin partida cargada</div>
      <p class="an-nota" style="color:#7ec8e3;font-size:11px;">💡 Toca el tablero para añadir jugadas manualmente — puedes jugar tú ambos bandos.</p>
      <div class="an-turno" id="anTurnoWrap" style="display:none">
        <span class="an-turno-ficha" id="anTurnoFicha"></span>
        <span id="anTurnoLabel"></span>
        <span style="flex:1"></span>
        <button class="btn btn-suave" id="anDeshacer" type="button" style="width:auto;padding:4px 10px;font-size:12px;">↩ Deshacer</button>
      </div>
      <div class="an-lista" id="anLista" style="display:none"></div>
    </div>
  </div>
  </div>
</div>

<script>
// ── chess.js embebido ─────────────────────────────────
/*
 * Copyright (c) 2020, Jeff Hlywa (jhlywa@gmail.com)
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 *----------------------------------------------------------------------------*/

/* minified license below  */

/* @license
 * Copyright (c) 2018, Jeff Hlywa (jhlywa@gmail.com)
 * Released under the BSD license
 * https://github.com/jhlywa/chess.js/blob/master/LICENSE
 */

var Chess = function(fen) {
  var BLACK = 'b'
  var WHITE = 'w'

  var EMPTY = -1

  var PAWN = 'p'
  var KNIGHT = 'n'
  var BISHOP = 'b'
  var ROOK = 'r'
  var QUEEN = 'q'
  var KING = 'k'

  var SYMBOLS = 'pnbrqkPNBRQK'

  var DEFAULT_POSITION =
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

  var POSSIBLE_RESULTS = ['1-0', '0-1', '1/2-1/2', '*']

  var PAWN_OFFSETS = {
    b: [16, 32, 17, 15],
    w: [-16, -32, -17, -15]
  }

  var PIECE_OFFSETS = {
    n: [-18, -33, -31, -14, 18, 33, 31, 14],
    b: [-17, -15, 17, 15],
    r: [-16, 1, 16, -1],
    q: [-17, -16, -15, 1, 17, 16, 15, -1],
    k: [-17, -16, -15, 1, 17, 16, 15, -1]
  }

  // prettier-ignore
  var ATTACKS = [
    20, 0, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0, 0,20, 0,
     0,20, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0,20, 0, 0,
     0, 0,20, 0, 0, 0, 0, 24,  0, 0, 0, 0,20, 0, 0, 0,
     0, 0, 0,20, 0, 0, 0, 24,  0, 0, 0,20, 0, 0, 0, 0,
     0, 0, 0, 0,20, 0, 0, 24,  0, 0,20, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0,20, 2, 24,  2,20, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 2,53, 56, 53, 2, 0, 0, 0, 0, 0, 0,
    24,24,24,24,24,24,56,  0, 56,24,24,24,24,24,24, 0,
     0, 0, 0, 0, 0, 2,53, 56, 53, 2, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0,20, 2, 24,  2,20, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0,20, 0, 0, 24,  0, 0,20, 0, 0, 0, 0, 0,
     0, 0, 0,20, 0, 0, 0, 24,  0, 0, 0,20, 0, 0, 0, 0,
     0, 0,20, 0, 0, 0, 0, 24,  0, 0, 0, 0,20, 0, 0, 0,
     0,20, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0,20, 0, 0,
    20, 0, 0, 0, 0, 0, 0, 24,  0, 0, 0, 0, 0, 0,20
  ];

  // prettier-ignore
  var RAYS = [
     17,  0,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0,  0,  0, 15, 0,
      0, 17,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0,  0, 15,  0, 0,
      0,  0, 17,  0,  0,  0,  0, 16,  0,  0,  0,  0, 15,  0,  0, 0,
      0,  0,  0, 17,  0,  0,  0, 16,  0,  0,  0, 15,  0,  0,  0, 0,
      0,  0,  0,  0, 17,  0,  0, 16,  0,  0, 15,  0,  0,  0,  0, 0,
      0,  0,  0,  0,  0, 17,  0, 16,  0, 15,  0,  0,  0,  0,  0, 0,
      0,  0,  0,  0,  0,  0, 17, 16, 15,  0,  0,  0,  0,  0,  0, 0,
      1,  1,  1,  1,  1,  1,  1,  0, -1, -1,  -1,-1, -1, -1, -1, 0,
      0,  0,  0,  0,  0,  0,-15,-16,-17,  0,  0,  0,  0,  0,  0, 0,
      0,  0,  0,  0,  0,-15,  0,-16,  0,-17,  0,  0,  0,  0,  0, 0,
      0,  0,  0,  0,-15,  0,  0,-16,  0,  0,-17,  0,  0,  0,  0, 0,
      0,  0,  0,-15,  0,  0,  0,-16,  0,  0,  0,-17,  0,  0,  0, 0,
      0,  0,-15,  0,  0,  0,  0,-16,  0,  0,  0,  0,-17,  0,  0, 0,
      0,-15,  0,  0,  0,  0,  0,-16,  0,  0,  0,  0,  0,-17,  0, 0,
    -15,  0,  0,  0,  0,  0,  0,-16,  0,  0,  0,  0,  0,  0,-17
  ];

  var SHIFTS = { p: 0, n: 1, b: 2, r: 3, q: 4, k: 5 }

  var FLAGS = {
    NORMAL: 'n',
    CAPTURE: 'c',
    BIG_PAWN: 'b',
    EP_CAPTURE: 'e',
    PROMOTION: 'p',
    KSIDE_CASTLE: 'k',
    QSIDE_CASTLE: 'q'
  }

  var BITS = {
    NORMAL: 1,
    CAPTURE: 2,
    BIG_PAWN: 4,
    EP_CAPTURE: 8,
    PROMOTION: 16,
    KSIDE_CASTLE: 32,
    QSIDE_CASTLE: 64
  }

  var RANK_1 = 7
  var RANK_2 = 6
  var RANK_3 = 5
  var RANK_4 = 4
  var RANK_5 = 3
  var RANK_6 = 2
  var RANK_7 = 1
  var RANK_8 = 0

  // prettier-ignore
  var SQUARES = {
    a8:   0, b8:   1, c8:   2, d8:   3, e8:   4, f8:   5, g8:   6, h8:   7,
    a7:  16, b7:  17, c7:  18, d7:  19, e7:  20, f7:  21, g7:  22, h7:  23,
    a6:  32, b6:  33, c6:  34, d6:  35, e6:  36, f6:  37, g6:  38, h6:  39,
    a5:  48, b5:  49, c5:  50, d5:  51, e5:  52, f5:  53, g5:  54, h5:  55,
    a4:  64, b4:  65, c4:  66, d4:  67, e4:  68, f4:  69, g4:  70, h4:  71,
    a3:  80, b3:  81, c3:  82, d3:  83, e3:  84, f3:  85, g3:  86, h3:  87,
    a2:  96, b2:  97, c2:  98, d2:  99, e2: 100, f2: 101, g2: 102, h2: 103,
    a1: 112, b1: 113, c1: 114, d1: 115, e1: 116, f1: 117, g1: 118, h1: 119
  };

  var ROOKS = {
    w: [
      { square: SQUARES.a1, flag: BITS.QSIDE_CASTLE },
      { square: SQUARES.h1, flag: BITS.KSIDE_CASTLE }
    ],
    b: [
      { square: SQUARES.a8, flag: BITS.QSIDE_CASTLE },
      { square: SQUARES.h8, flag: BITS.KSIDE_CASTLE }
    ]
  }

  var board = new Array(128)
  var kings = { w: EMPTY, b: EMPTY }
  var turn = WHITE
  var castling = { w: 0, b: 0 }
  var ep_square = EMPTY
  var half_moves = 0
  var move_number = 1
  var history = []
  var header = {}

  /* if the user passes in a fen string, load it, else default to
   * starting position
   */
  if (typeof fen === 'undefined') {
    load(DEFAULT_POSITION)
  } else {
    load(fen)
  }

  function clear(keep_headers) {
    if (typeof keep_headers === 'undefined') {
      keep_headers = false
    }

    board = new Array(128)
    kings = { w: EMPTY, b: EMPTY }
    turn = WHITE
    castling = { w: 0, b: 0 }
    ep_square = EMPTY
    half_moves = 0
    move_number = 1
    history = []
    if (!keep_headers) header = {}
    update_setup(generate_fen())
  }

  function reset() {
    load(DEFAULT_POSITION)
  }

  function load(fen, keep_headers) {
    if (typeof keep_headers === 'undefined') {
      keep_headers = false
    }

    var tokens = fen.split(/\s+/)
    var position = tokens[0]
    var square = 0

    if (!validate_fen(fen).valid) {
      return false
    }

    clear(keep_headers)

    for (var i = 0; i < position.length; i++) {
      var piece = position.charAt(i)

      if (piece === '/') {
        square += 8
      } else if (is_digit(piece)) {
        square += parseInt(piece, 10)
      } else {
        var color = piece < 'a' ? WHITE : BLACK
        put({ type: piece.toLowerCase(), color: color }, algebraic(square))
        square++
      }
    }

    turn = tokens[1]

    if (tokens[2].indexOf('K') > -1) {
      castling.w |= BITS.KSIDE_CASTLE
    }
    if (tokens[2].indexOf('Q') > -1) {
      castling.w |= BITS.QSIDE_CASTLE
    }
    if (tokens[2].indexOf('k') > -1) {
      castling.b |= BITS.KSIDE_CASTLE
    }
    if (tokens[2].indexOf('q') > -1) {
      castling.b |= BITS.QSIDE_CASTLE
    }

    ep_square = tokens[3] === '-' ? EMPTY : SQUARES[tokens[3]]
    half_moves = parseInt(tokens[4], 10)
    move_number = parseInt(tokens[5], 10)

    update_setup(generate_fen())

    return true
  }

  /* TODO: this function is pretty much crap - it validates structure but
   * completely ignores content (e.g. doesn't verify that each side has a king)
   * ... we should rewrite this, and ditch the silly error_number field while
   * we're at it
   */
  function validate_fen(fen) {
    var errors = {
      0: 'No errors.',
      1: 'FEN string must contain six space-delimited fields.',
      2: '6th field (move number) must be a positive integer.',
      3: '5th field (half move counter) must be a non-negative integer.',
      4: '4th field (en-passant square) is invalid.',
      5: '3rd field (castling availability) is invalid.',
      6: '2nd field (side to move) is invalid.',
      7: "1st field (piece positions) does not contain 8 '/'-delimited rows.",
      8: '1st field (piece positions) is invalid [consecutive numbers].',
      9: '1st field (piece positions) is invalid [invalid piece].',
      10: '1st field (piece positions) is invalid [row too large].',
      11: 'Illegal en-passant square'
    }

    /* 1st criterion: 6 space-seperated fields? */
    var tokens = fen.split(/\s+/)
    if (tokens.length !== 6) {
      return { valid: false, error_number: 1, error: errors[1] }
    }

    /* 2nd criterion: move number field is a integer value > 0? */
    if (isNaN(tokens[5]) || parseInt(tokens[5], 10) <= 0) {
      return { valid: false, error_number: 2, error: errors[2] }
    }

    /* 3rd criterion: half move counter is an integer >= 0? */
    if (isNaN(tokens[4]) || parseInt(tokens[4], 10) < 0) {
      return { valid: false, error_number: 3, error: errors[3] }
    }

    /* 4th criterion: 4th field is a valid e.p.-string? */
    if (!/^(-|[abcdefgh][36])$/.test(tokens[3])) {
      return { valid: false, error_number: 4, error: errors[4] }
    }

    /* 5th criterion: 3th field is a valid castle-string? */
    if (!/^(KQ?k?q?|Qk?q?|kq?|q|-)$/.test(tokens[2])) {
      return { valid: false, error_number: 5, error: errors[5] }
    }

    /* 6th criterion: 2nd field is "w" (white) or "b" (black)? */
    if (!/^(w|b)$/.test(tokens[1])) {
      return { valid: false, error_number: 6, error: errors[6] }
    }

    /* 7th criterion: 1st field contains 8 rows? */
    var rows = tokens[0].split('/')
    if (rows.length !== 8) {
      return { valid: false, error_number: 7, error: errors[7] }
    }

    /* 8th criterion: every row is valid? */
    for (var i = 0; i < rows.length; i++) {
      /* check for right sum of fields AND not two numbers in succession */
      var sum_fields = 0
      var previous_was_number = false

      for (var k = 0; k < rows[i].length; k++) {
        if (!isNaN(rows[i][k])) {
          if (previous_was_number) {
            return { valid: false, error_number: 8, error: errors[8] }
          }
          sum_fields += parseInt(rows[i][k], 10)
          previous_was_number = true
        } else {
          if (!/^[prnbqkPRNBQK]$/.test(rows[i][k])) {
            return { valid: false, error_number: 9, error: errors[9] }
          }
          sum_fields += 1
          previous_was_number = false
        }
      }
      if (sum_fields !== 8) {
        return { valid: false, error_number: 10, error: errors[10] }
      }
    }

    if (
      (tokens[3][1] == '3' && tokens[1] == 'w') ||
      (tokens[3][1] == '6' && tokens[1] == 'b')
    ) {
      return { valid: false, error_number: 11, error: errors[11] }
    }

    /* everything's okay! */
    return { valid: true, error_number: 0, error: errors[0] }
  }

  function generate_fen() {
    var empty = 0
    var fen = ''

    for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
      if (board[i] == null) {
        empty++
      } else {
        if (empty > 0) {
          fen += empty
          empty = 0
        }
        var color = board[i].color
        var piece = board[i].type

        fen += color === WHITE ? piece.toUpperCase() : piece.toLowerCase()
      }

      if ((i + 1) & 0x88) {
        if (empty > 0) {
          fen += empty
        }

        if (i !== SQUARES.h1) {
          fen += '/'
        }

        empty = 0
        i += 8
      }
    }

    var cflags = ''
    if (castling[WHITE] & BITS.KSIDE_CASTLE) {
      cflags += 'K'
    }
    if (castling[WHITE] & BITS.QSIDE_CASTLE) {
      cflags += 'Q'
    }
    if (castling[BLACK] & BITS.KSIDE_CASTLE) {
      cflags += 'k'
    }
    if (castling[BLACK] & BITS.QSIDE_CASTLE) {
      cflags += 'q'
    }

    /* do we have an empty castling flag? */
    cflags = cflags || '-'
    var epflags = ep_square === EMPTY ? '-' : algebraic(ep_square)

    return [fen, turn, cflags, epflags, half_moves, move_number].join(' ')
  }

  function set_header(args) {
    for (var i = 0; i < args.length; i += 2) {
      if (typeof args[i] === 'string' && typeof args[i + 1] === 'string') {
        header[args[i]] = args[i + 1]
      }
    }
    return header
  }

  /* called when the initial board setup is changed with put() or remove().
   * modifies the SetUp and FEN properties of the header object.  if the FEN is
   * equal to the default position, the SetUp and FEN are deleted
   * the setup is only updated if history.length is zero, ie moves haven't been
   * made.
   */
  function update_setup(fen) {
    if (history.length > 0) return

    if (fen !== DEFAULT_POSITION) {
      header['SetUp'] = '1'
      header['FEN'] = fen
    } else {
      delete header['SetUp']
      delete header['FEN']
    }
  }

  function get(square) {
    var piece = board[SQUARES[square]]
    return piece ? { type: piece.type, color: piece.color } : null
  }

  function put(piece, square) {
    /* check for valid piece object */
    if (!('type' in piece && 'color' in piece)) {
      return false
    }

    /* check for piece */
    if (SYMBOLS.indexOf(piece.type.toLowerCase()) === -1) {
      return false
    }

    /* check for valid square */
    if (!(square in SQUARES)) {
      return false
    }

    var sq = SQUARES[square]

    /* don't let the user place more than one king */
    if (
      piece.type == KING &&
      !(kings[piece.color] == EMPTY || kings[piece.color] == sq)
    ) {
      return false
    }

    board[sq] = { type: piece.type, color: piece.color }
    if (piece.type === KING) {
      kings[piece.color] = sq
    }

    update_setup(generate_fen())

    return true
  }

  function remove(square) {
    var piece = get(square)
    board[SQUARES[square]] = null
    if (piece && piece.type === KING) {
      kings[piece.color] = EMPTY
    }

    update_setup(generate_fen())

    return piece
  }

  function build_move(board, from, to, flags, promotion) {
    var move = {
      color: turn,
      from: from,
      to: to,
      flags: flags,
      piece: board[from].type
    }

    if (promotion) {
      move.flags |= BITS.PROMOTION
      move.promotion = promotion
    }

    if (board[to]) {
      move.captured = board[to].type
    } else if (flags & BITS.EP_CAPTURE) {
      move.captured = PAWN
    }
    return move
  }

  function generate_moves(options) {
    function add_move(board, moves, from, to, flags) {
      /* if pawn promotion */
      if (
        board[from].type === PAWN &&
        (rank(to) === RANK_8 || rank(to) === RANK_1)
      ) {
        var pieces = [QUEEN, ROOK, BISHOP, KNIGHT]
        for (var i = 0, len = pieces.length; i < len; i++) {
          moves.push(build_move(board, from, to, flags, pieces[i]))
        }
      } else {
        moves.push(build_move(board, from, to, flags))
      }
    }

    var moves = []
    var us = turn
    var them = swap_color(us)
    var second_rank = { b: RANK_7, w: RANK_2 }

    var first_sq = SQUARES.a8
    var last_sq = SQUARES.h1
    var single_square = false

    /* do we want legal moves? */
    var legal =
      typeof options !== 'undefined' && 'legal' in options
        ? options.legal
        : true

    /* are we generating moves for a single square? */
    if (typeof options !== 'undefined' && 'square' in options) {
      if (options.square in SQUARES) {
        first_sq = last_sq = SQUARES[options.square]
        single_square = true
      } else {
        /* invalid square */
        return []
      }
    }

    for (var i = first_sq; i <= last_sq; i++) {
      /* did we run off the end of the board */
      if (i & 0x88) {
        i += 7
        continue
      }

      var piece = board[i]
      if (piece == null || piece.color !== us) {
        continue
      }

      if (piece.type === PAWN) {
        /* single square, non-capturing */
        var square = i + PAWN_OFFSETS[us][0]
        if (board[square] == null) {
          add_move(board, moves, i, square, BITS.NORMAL)

          /* double square */
          var square = i + PAWN_OFFSETS[us][1]
          if (second_rank[us] === rank(i) && board[square] == null) {
            add_move(board, moves, i, square, BITS.BIG_PAWN)
          }
        }

        /* pawn captures */
        for (j = 2; j < 4; j++) {
          var square = i + PAWN_OFFSETS[us][j]
          if (square & 0x88) continue

          if (board[square] != null && board[square].color === them) {
            add_move(board, moves, i, square, BITS.CAPTURE)
          } else if (square === ep_square) {
            add_move(board, moves, i, ep_square, BITS.EP_CAPTURE)
          }
        }
      } else {
        for (var j = 0, len = PIECE_OFFSETS[piece.type].length; j < len; j++) {
          var offset = PIECE_OFFSETS[piece.type][j]
          var square = i

          while (true) {
            square += offset
            if (square & 0x88) break

            if (board[square] == null) {
              add_move(board, moves, i, square, BITS.NORMAL)
            } else {
              if (board[square].color === us) break
              add_move(board, moves, i, square, BITS.CAPTURE)
              break
            }

            /* break, if knight or king */
            if (piece.type === 'n' || piece.type === 'k') break
          }
        }
      }
    }

    /* check for castling if: a) we're generating all moves, or b) we're doing
     * single square move generation on the king's square
     */
    if (!single_square || last_sq === kings[us]) {
      /* king-side castling */
      if (castling[us] & BITS.KSIDE_CASTLE) {
        var castling_from = kings[us]
        var castling_to = castling_from + 2

        if (
          board[castling_from + 1] == null &&
          board[castling_to] == null &&
          !attacked(them, kings[us]) &&
          !attacked(them, castling_from + 1) &&
          !attacked(them, castling_to)
        ) {
          add_move(board, moves, kings[us], castling_to, BITS.KSIDE_CASTLE)
        }
      }

      /* queen-side castling */
      if (castling[us] & BITS.QSIDE_CASTLE) {
        var castling_from = kings[us]
        var castling_to = castling_from - 2

        if (
          board[castling_from - 1] == null &&
          board[castling_from - 2] == null &&
          board[castling_from - 3] == null &&
          !attacked(them, kings[us]) &&
          !attacked(them, castling_from - 1) &&
          !attacked(them, castling_to)
        ) {
          add_move(board, moves, kings[us], castling_to, BITS.QSIDE_CASTLE)
        }
      }
    }

    /* return all pseudo-legal moves (this includes moves that allow the king
     * to be captured)
     */
    if (!legal) {
      return moves
    }

    /* filter out illegal moves */
    var legal_moves = []
    for (var i = 0, len = moves.length; i < len; i++) {
      make_move(moves[i])
      if (!king_attacked(us)) {
        legal_moves.push(moves[i])
      }
      undo_move()
    }

    return legal_moves
  }

  /* convert a move from 0x88 coordinates to Standard Algebraic Notation
   * (SAN)
   *
   * @param {boolean} sloppy Use the sloppy SAN generator to work around over
   * disambiguation bugs in Fritz and Chessbase.  See below:
   *
   * r1bqkbnr/ppp2ppp/2n5/1B1pP3/4P3/8/PPPP2PP/RNBQK1NR b KQkq - 2 4
   * 4. ... Nge7 is overly disambiguated because the knight on c6 is pinned
   * 4. ... Ne7 is technically the valid SAN
   */
  function move_to_san(move, sloppy) {
    var output = ''

    if (move.flags & BITS.KSIDE_CASTLE) {
      output = 'O-O'
    } else if (move.flags & BITS.QSIDE_CASTLE) {
      output = 'O-O-O'
    } else {
      var disambiguator = get_disambiguator(move, sloppy)

      if (move.piece !== PAWN) {
        output += move.piece.toUpperCase() + disambiguator
      }

      if (move.flags & (BITS.CAPTURE | BITS.EP_CAPTURE)) {
        if (move.piece === PAWN) {
          output += algebraic(move.from)[0]
        }
        output += 'x'
      }

      output += algebraic(move.to)

      if (move.flags & BITS.PROMOTION) {
        output += '=' + move.promotion.toUpperCase()
      }
    }

    make_move(move)
    if (in_check()) {
      if (in_checkmate()) {
        output += '#'
      } else {
        output += '+'
      }
    }
    undo_move()

    return output
  }

  // parses all of the decorators out of a SAN string
  function stripped_san(move) {
    return move.replace(/=/, '').replace(/[+#]?[?!]*$/, '')
  }

  function attacked(color, square) {
    for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
      /* did we run off the end of the board */
      if (i & 0x88) {
        i += 7
        continue
      }

      /* if empty square or wrong color */
      if (board[i] == null || board[i].color !== color) continue

      var piece = board[i]
      var difference = i - square
      var index = difference + 119

      if (ATTACKS[index] & (1 << SHIFTS[piece.type])) {
        if (piece.type === PAWN) {
          if (difference > 0) {
            if (piece.color === WHITE) return true
          } else {
            if (piece.color === BLACK) return true
          }
          continue
        }

        /* if the piece is a knight or a king */
        if (piece.type === 'n' || piece.type === 'k') return true

        var offset = RAYS[index]
        var j = i + offset

        var blocked = false
        while (j !== square) {
          if (board[j] != null) {
            blocked = true
            break
          }
          j += offset
        }

        if (!blocked) return true
      }
    }

    return false
  }

  function king_attacked(color) {
    return attacked(swap_color(color), kings[color])
  }

  function in_check() {
    return king_attacked(turn)
  }

  function in_checkmate() {
    return in_check() && generate_moves().length === 0
  }

  function in_stalemate() {
    return !in_check() && generate_moves().length === 0
  }

  function insufficient_material() {
    var pieces = {}
    var bishops = []
    var num_pieces = 0
    var sq_color = 0

    for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
      sq_color = (sq_color + 1) % 2
      if (i & 0x88) {
        i += 7
        continue
      }

      var piece = board[i]
      if (piece) {
        pieces[piece.type] = piece.type in pieces ? pieces[piece.type] + 1 : 1
        if (piece.type === BISHOP) {
          bishops.push(sq_color)
        }
        num_pieces++
      }
    }

    /* k vs. k */
    if (num_pieces === 2) {
      return true
    } else if (
      /* k vs. kn .... or .... k vs. kb */
      num_pieces === 3 &&
      (pieces[BISHOP] === 1 || pieces[KNIGHT] === 1)
    ) {
      return true
    } else if (num_pieces === pieces[BISHOP] + 2) {
      /* kb vs. kb where any number of bishops are all on the same color */
      var sum = 0
      var len = bishops.length
      for (var i = 0; i < len; i++) {
        sum += bishops[i]
      }
      if (sum === 0 || sum === len) {
        return true
      }
    }

    return false
  }

  function in_threefold_repetition() {
    /* TODO: while this function is fine for casual use, a better
     * implementation would use a Zobrist key (instead of FEN). the
     * Zobrist key would be maintained in the make_move/undo_move functions,
     * avoiding the costly that we do below.
     */
    var moves = []
    var positions = {}
    var repetition = false

    while (true) {
      var move = undo_move()
      if (!move) break
      moves.push(move)
    }

    while (true) {
      /* remove the last two fields in the FEN string, they're not needed
       * when checking for draw by rep */
      var fen = generate_fen()
        .split(' ')
        .slice(0, 4)
        .join(' ')

      /* has the position occurred three or move times */
      positions[fen] = fen in positions ? positions[fen] + 1 : 1
      if (positions[fen] >= 3) {
        repetition = true
      }

      if (!moves.length) {
        break
      }
      make_move(moves.pop())
    }

    return repetition
  }

  function push(move) {
    history.push({
      move: move,
      kings: { b: kings.b, w: kings.w },
      turn: turn,
      castling: { b: castling.b, w: castling.w },
      ep_square: ep_square,
      half_moves: half_moves,
      move_number: move_number
    })
  }

  function make_move(move) {
    var us = turn
    var them = swap_color(us)
    push(move)

    board[move.to] = board[move.from]
    board[move.from] = null

    /* if ep capture, remove the captured pawn */
    if (move.flags & BITS.EP_CAPTURE) {
      if (turn === BLACK) {
        board[move.to - 16] = null
      } else {
        board[move.to + 16] = null
      }
    }

    /* if pawn promotion, replace with new piece */
    if (move.flags & BITS.PROMOTION) {
      board[move.to] = { type: move.promotion, color: us }
    }

    /* if we moved the king */
    if (board[move.to].type === KING) {
      kings[board[move.to].color] = move.to

      /* if we castled, move the rook next to the king */
      if (move.flags & BITS.KSIDE_CASTLE) {
        var castling_to = move.to - 1
        var castling_from = move.to + 1
        board[castling_to] = board[castling_from]
        board[castling_from] = null
      } else if (move.flags & BITS.QSIDE_CASTLE) {
        var castling_to = move.to + 1
        var castling_from = move.to - 2
        board[castling_to] = board[castling_from]
        board[castling_from] = null
      }

      /* turn off castling */
      castling[us] = ''
    }

    /* turn off castling if we move a rook */
    if (castling[us]) {
      for (var i = 0, len = ROOKS[us].length; i < len; i++) {
        if (
          move.from === ROOKS[us][i].square &&
          castling[us] & ROOKS[us][i].flag
        ) {
          castling[us] ^= ROOKS[us][i].flag
          break
        }
      }
    }

    /* turn off castling if we capture a rook */
    if (castling[them]) {
      for (var i = 0, len = ROOKS[them].length; i < len; i++) {
        if (
          move.to === ROOKS[them][i].square &&
          castling[them] & ROOKS[them][i].flag
        ) {
          castling[them] ^= ROOKS[them][i].flag
          break
        }
      }
    }

    /* if big pawn move, update the en passant square */
    if (move.flags & BITS.BIG_PAWN) {
      if (turn === 'b') {
        ep_square = move.to - 16
      } else {
        ep_square = move.to + 16
      }
    } else {
      ep_square = EMPTY
    }

    /* reset the 50 move counter if a pawn is moved or a piece is captured */
    if (move.piece === PAWN) {
      half_moves = 0
    } else if (move.flags & (BITS.CAPTURE | BITS.EP_CAPTURE)) {
      half_moves = 0
    } else {
      half_moves++
    }

    if (turn === BLACK) {
      move_number++
    }
    turn = swap_color(turn)
  }

  function undo_move() {
    var old = history.pop()
    if (old == null) {
      return null
    }

    var move = old.move
    kings = old.kings
    turn = old.turn
    castling = old.castling
    ep_square = old.ep_square
    half_moves = old.half_moves
    move_number = old.move_number

    var us = turn
    var them = swap_color(turn)

    board[move.from] = board[move.to]
    board[move.from].type = move.piece // to undo any promotions
    board[move.to] = null

    if (move.flags & BITS.CAPTURE) {
      board[move.to] = { type: move.captured, color: them }
    } else if (move.flags & BITS.EP_CAPTURE) {
      var index
      if (us === BLACK) {
        index = move.to - 16
      } else {
        index = move.to + 16
      }
      board[index] = { type: PAWN, color: them }
    }

    if (move.flags & (BITS.KSIDE_CASTLE | BITS.QSIDE_CASTLE)) {
      var castling_to, castling_from
      if (move.flags & BITS.KSIDE_CASTLE) {
        castling_to = move.to + 1
        castling_from = move.to - 1
      } else if (move.flags & BITS.QSIDE_CASTLE) {
        castling_to = move.to - 2
        castling_from = move.to + 1
      }

      board[castling_to] = board[castling_from]
      board[castling_from] = null
    }

    return move
  }

  /* this function is used to uniquely identify ambiguous moves */
  function get_disambiguator(move, sloppy) {
    var moves = generate_moves({ legal: !sloppy })

    var from = move.from
    var to = move.to
    var piece = move.piece

    var ambiguities = 0
    var same_rank = 0
    var same_file = 0

    for (var i = 0, len = moves.length; i < len; i++) {
      var ambig_from = moves[i].from
      var ambig_to = moves[i].to
      var ambig_piece = moves[i].piece

      /* if a move of the same piece type ends on the same to square, we'll
       * need to add a disambiguator to the algebraic notation
       */
      if (piece === ambig_piece && from !== ambig_from && to === ambig_to) {
        ambiguities++

        if (rank(from) === rank(ambig_from)) {
          same_rank++
        }

        if (file(from) === file(ambig_from)) {
          same_file++
        }
      }
    }

    if (ambiguities > 0) {
      /* if there exists a similar moving piece on the same rank and file as
       * the move in question, use the square as the disambiguator
       */
      if (same_rank > 0 && same_file > 0) {
        return algebraic(from)
      } else if (same_file > 0) {
        /* if the moving piece rests on the same file, use the rank symbol as the
         * disambiguator
         */
        return algebraic(from).charAt(1)
      } else {
        /* else use the file symbol */
        return algebraic(from).charAt(0)
      }
    }

    return ''
  }

  function ascii() {
    var s = '   +------------------------+\n'
    for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
      /* display the rank */
      if (file(i) === 0) {
        s += ' ' + '87654321'[rank(i)] + ' |'
      }

      /* empty piece */
      if (board[i] == null) {
        s += ' . '
      } else {
        var piece = board[i].type
        var color = board[i].color
        var symbol = color === WHITE ? piece.toUpperCase() : piece.toLowerCase()
        s += ' ' + symbol + ' '
      }

      if ((i + 1) & 0x88) {
        s += '|\n'
        i += 8
      }
    }
    s += '   +------------------------+\n'
    s += '     a  b  c  d  e  f  g  h\n'

    return s
  }

  // convert a move from Standard Algebraic Notation (SAN) to 0x88 coordinates
  function move_from_san(move, sloppy) {
    // strip off any move decorations: e.g Nf3+?!
    var clean_move = stripped_san(move)

    // if we're using the sloppy parser run a regex to grab piece, to, and from
    // this should parse invalid SAN like: Pe2-e4, Rc1c4, Qf3xf7
    if (sloppy) {
      var matches = clean_move.match(
        /([pnbrqkPNBRQK])?([a-h][1-8])x?-?([a-h][1-8])([qrbnQRBN])?/
      )
      if (matches) {
        var piece = matches[1]
        var from = matches[2]
        var to = matches[3]
        var promotion = matches[4]
      }
    }

    var moves = generate_moves()
    for (var i = 0, len = moves.length; i < len; i++) {
      // try the strict parser first, then the sloppy parser if requested
      // by the user
      if (
        clean_move === stripped_san(move_to_san(moves[i])) ||
        (sloppy && clean_move === stripped_san(move_to_san(moves[i], true)))
      ) {
        return moves[i]
      } else {
        if (
          matches &&
          (!piece || piece.toLowerCase() == moves[i].piece) &&
          SQUARES[from] == moves[i].from &&
          SQUARES[to] == moves[i].to &&
          (!promotion || promotion.toLowerCase() == moves[i].promotion)
        ) {
          return moves[i]
        }
      }
    }

    return null
  }

  /*****************************************************************************
   * UTILITY FUNCTIONS
   ****************************************************************************/
  function rank(i) {
    return i >> 4
  }

  function file(i) {
    return i & 15
  }

  function algebraic(i) {
    var f = file(i),
      r = rank(i)
    return 'abcdefgh'.substring(f, f + 1) + '87654321'.substring(r, r + 1)
  }

  function swap_color(c) {
    return c === WHITE ? BLACK : WHITE
  }

  function is_digit(c) {
    return '0123456789'.indexOf(c) !== -1
  }

  /* pretty = external move object */
  function make_pretty(ugly_move) {
    var move = clone(ugly_move)
    move.san = move_to_san(move, false)
    move.to = algebraic(move.to)
    move.from = algebraic(move.from)

    var flags = ''

    for (var flag in BITS) {
      if (BITS[flag] & move.flags) {
        flags += FLAGS[flag]
      }
    }
    move.flags = flags

    return move
  }

  function clone(obj) {
    var dupe = obj instanceof Array ? [] : {}

    for (var property in obj) {
      if (typeof property === 'object') {
        dupe[property] = clone(obj[property])
      } else {
        dupe[property] = obj[property]
      }
    }

    return dupe
  }

  function trim(str) {
    return str.replace(/^\s+|\s+$/g, '')
  }

  /*****************************************************************************
   * DEBUGGING UTILITIES
   ****************************************************************************/
  function perft(depth) {
    var moves = generate_moves({ legal: false })
    var nodes = 0
    var color = turn

    for (var i = 0, len = moves.length; i < len; i++) {
      make_move(moves[i])
      if (!king_attacked(color)) {
        if (depth - 1 > 0) {
          var child_nodes = perft(depth - 1)
          nodes += child_nodes
        } else {
          nodes++
        }
      }
      undo_move()
    }

    return nodes
  }

  return {
    /***************************************************************************
     * PUBLIC CONSTANTS (is there a better way to do this?)
     **************************************************************************/
    WHITE: WHITE,
    BLACK: BLACK,
    PAWN: PAWN,
    KNIGHT: KNIGHT,
    BISHOP: BISHOP,
    ROOK: ROOK,
    QUEEN: QUEEN,
    KING: KING,
    SQUARES: (function() {
      /* from the ECMA-262 spec (section 12.6.4):
       * "The mechanics of enumerating the properties ... is
       * implementation dependent"
       * so: for (var sq in SQUARES) { keys.push(sq); } might not be
       * ordered correctly
       */
      var keys = []
      for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
        if (i & 0x88) {
          i += 7
          continue
        }
        keys.push(algebraic(i))
      }
      return keys
    })(),
    FLAGS: FLAGS,

    /***************************************************************************
     * PUBLIC API
     **************************************************************************/
    load: function(fen) {
      return load(fen)
    },

    reset: function() {
      return reset()
    },

    moves: function(options) {
      /* The internal representation of a chess move is in 0x88 format, and
       * not meant to be human-readable.  The code below converts the 0x88
       * square coordinates to algebraic coordinates.  It also prunes an
       * unnecessary move keys resulting from a verbose call.
       */

      var ugly_moves = generate_moves(options)
      var moves = []

      for (var i = 0, len = ugly_moves.length; i < len; i++) {
        /* does the user want a full move object (most likely not), or just
         * SAN
         */
        if (
          typeof options !== 'undefined' &&
          'verbose' in options &&
          options.verbose
        ) {
          moves.push(make_pretty(ugly_moves[i]))
        } else {
          moves.push(move_to_san(ugly_moves[i], false))
        }
      }

      return moves
    },

    in_check: function() {
      return in_check()
    },

    in_checkmate: function() {
      return in_checkmate()
    },

    in_stalemate: function() {
      return in_stalemate()
    },

    in_draw: function() {
      return (
        half_moves >= 100 ||
        in_stalemate() ||
        insufficient_material() ||
        in_threefold_repetition()
      )
    },

    insufficient_material: function() {
      return insufficient_material()
    },

    in_threefold_repetition: function() {
      return in_threefold_repetition()
    },

    game_over: function() {
      return (
        half_moves >= 100 ||
        in_checkmate() ||
        in_stalemate() ||
        insufficient_material() ||
        in_threefold_repetition()
      )
    },

    validate_fen: function(fen) {
      return validate_fen(fen)
    },

    fen: function() {
      return generate_fen()
    },

    board: function() {
      var output = [],
        row = []

      for (var i = SQUARES.a8; i <= SQUARES.h1; i++) {
        if (board[i] == null) {
          row.push(null)
        } else {
          row.push({ type: board[i].type, color: board[i].color })
        }
        if ((i + 1) & 0x88) {
          output.push(row)
          row = []
          i += 8
        }
      }

      return output
    },

    pgn: function(options) {
      /* using the specification from http://www.chessclub.com/help/PGN-spec
       * example for html usage: .pgn({ max_width: 72, newline_char: "<br />" })
       */
      var newline =
        typeof options === 'object' && typeof options.newline_char === 'string'
          ? options.newline_char
          : '\n'
      var max_width =
        typeof options === 'object' && typeof options.max_width === 'number'
          ? options.max_width
          : 0
      var result = []
      var header_exists = false

      /* add the PGN header headerrmation */
      for (var i in header) {
        /* TODO: order of enumerated properties in header object is not
         * guaranteed, see ECMA-262 spec (section 12.6.4)
         */
        result.push('[' + i + ' "' + header[i] + '"]' + newline)
        header_exists = true
      }

      if (header_exists && history.length) {
        result.push(newline)
      }

      /* pop all of history onto reversed_history */
      var reversed_history = []
      while (history.length > 0) {
        reversed_history.push(undo_move())
      }

      var moves = []
      var move_string = ''

      /* build the list of moves.  a move_string looks like: "3. e3 e6" */
      while (reversed_history.length > 0) {
        var move = reversed_history.pop()

        /* if the position started with black to move, start PGN with 1. ... */
        if (!history.length && move.color === 'b') {
          move_string = move_number + '. ...'
        } else if (move.color === 'w') {
          /* store the previous generated move_string if we have one */
          if (move_string.length) {
            moves.push(move_string)
          }
          move_string = move_number + '.'
        }

        move_string = move_string + ' ' + move_to_san(move, false)
        make_move(move)
      }

      /* are there any other leftover moves? */
      if (move_string.length) {
        moves.push(move_string)
      }

      /* is there a result? */
      if (typeof header.Result !== 'undefined') {
        moves.push(header.Result)
      }

      /* history should be back to what is was before we started generating PGN,
       * so join together moves
       */
      if (max_width === 0) {
        return result.join('') + moves.join(' ')
      }

      /* wrap the PGN output at max_width */
      var current_width = 0
      for (var i = 0; i < moves.length; i++) {
        /* if the current move will push past max_width */
        if (current_width + moves[i].length > max_width && i !== 0) {
          /* don't end the line with whitespace */
          if (result[result.length - 1] === ' ') {
            result.pop()
          }

          result.push(newline)
          current_width = 0
        } else if (i !== 0) {
          result.push(' ')
          current_width++
        }
        result.push(moves[i])
        current_width += moves[i].length
      }

      return result.join('')
    },

    load_pgn: function(pgn, options) {
      // allow the user to specify the sloppy move parser to work around over
      // disambiguation bugs in Fritz and Chessbase
      var sloppy =
        typeof options !== 'undefined' && 'sloppy' in options
          ? options.sloppy
          : false

      function mask(str) {
        return str.replace(/\\/g, '\\')
      }

      function has_keys(object) {
        for (var key in object) {
          return true
        }
        return false
      }

      function parse_pgn_header(header, options) {
        var newline_char =
          typeof options === 'object' &&
          typeof options.newline_char === 'string'
            ? options.newline_char
            : '\r?\n'
        var header_obj = {}
        var headers = header.split(new RegExp(mask(newline_char)))
        var key = ''
        var value = ''

        for (var i = 0; i < headers.length; i++) {
          key = headers[i].replace(/^\[([A-Z][A-Za-z]*)\s.*\]$/, '$1')
          value = headers[i].replace(/^\[[A-Za-z]+\s"(.*)"\]$/, '$1')
          if (trim(key).length > 0) {
            header_obj[key] = value
          }
        }

        return header_obj
      }

      var newline_char =
        typeof options === 'object' && typeof options.newline_char === 'string'
          ? options.newline_char
          : '\r?\n'

      // RegExp to split header. Takes advantage of the fact that header and movetext
      // will always have a blank line between them (ie, two newline_char's).
      // With default newline_char, will equal: /^(\[((?:\r?\n)|.)*\])(?:\r?\n){2}/
      var header_regex = new RegExp(
        '^(\[((?:' +
          mask(newline_char) +
          ')|.)*\])' +
          '(?:' +
          mask(newline_char) +
          '){2}'
      )

      // If no header given, begin with moves.
      var header_string = header_regex.test(pgn)
        ? header_regex.exec(pgn)[1]
        : ''

      // Put the board in the starting position
      reset()

      /* parse PGN header */
      var headers = parse_pgn_header(header_string, options)
      for (var key in headers) {
        set_header([key, headers[key]])
      }

      /* load the starting position indicated by [Setup '1'] and
       * [FEN position] */
      if (headers['SetUp'] === '1') {
        if (!('FEN' in headers && load(headers['FEN'], true))) {
          // second argument to load: don't clear the headers
          return false
        }
      }

      /* delete header to get the moves */
      var ms = pgn
        .replace(header_string, '')
        .replace(new RegExp(mask(newline_char), 'g'), ' ')

      /* delete comments */
      ms = ms.replace(/(\{[^}]+\})+?/g, '')

      /* delete recursive annotation variations */
      var rav_regex = /(\([^\(\)]+\))+?/g
      while (rav_regex.test(ms)) {
        ms = ms.replace(rav_regex, '')
      }

      /* delete move numbers */
      ms = ms.replace(/\d+\.(\.\.)?/g, '')

      /* delete ... indicating black to move */
      ms = ms.replace(/\.\.\./g, '')

      /* delete numeric annotation glyphs */
      ms = ms.replace(/\$\d+/g, '')

      /* trim and get array of moves */
      var moves = trim(ms).split(new RegExp(/\s+/))

      /* delete empty entries */
      moves = moves
        .join(',')
        .replace(/,,+/g, ',')
        .split(',')
      var move = ''

      for (var half_move = 0; half_move < moves.length - 1; half_move++) {
        move = move_from_san(moves[half_move], sloppy)

        /* move not possible! (don't clear the board to examine to show the
         * latest valid position)
         */
        if (move == null) {
          return false
        } else {
          make_move(move)
        }
      }

      /* examine last move */
      move = moves[moves.length - 1]
      if (POSSIBLE_RESULTS.indexOf(move) > -1) {
        if (has_keys(header) && typeof header.Result === 'undefined') {
          set_header(['Result', move])
        }
      } else {
        move = move_from_san(move, sloppy)
        if (move == null) {
          return false
        } else {
          make_move(move)
        }
      }
      return true
    },

    header: function() {
      return set_header(arguments)
    },

    ascii: function() {
      return ascii()
    },

    turn: function() {
      return turn
    },

    move: function(move, options) {
      /* The move function can be called with in the following parameters:
       *
       * .move('Nxb7')      <- where 'move' is a case-sensitive SAN string
       *
       * .move({ from: 'h7', <- where the 'move' is a move object (additional
       *         to :'h8',      fields are ignored)
       *         promotion: 'q',
       *      })
       */

      // allow the user to specify the sloppy move parser to work around over
      // disambiguation bugs in Fritz and Chessbase
      var sloppy =
        typeof options !== 'undefined' && 'sloppy' in options
          ? options.sloppy
          : false

      var move_obj = null

      if (typeof move === 'string') {
        move_obj = move_from_san(move, sloppy)
      } else if (typeof move === 'object') {
        var moves = generate_moves()

        /* convert the pretty move object to an ugly move object */
        for (var i = 0, len = moves.length; i < len; i++) {
          if (
            move.from === algebraic(moves[i].from) &&
            move.to === algebraic(moves[i].to) &&
            (!('promotion' in moves[i]) ||
              move.promotion === moves[i].promotion)
          ) {
            move_obj = moves[i]
            break
          }
        }
      }

      /* failed to find move */
      if (!move_obj) {
        return null
      }

      /* need to make a copy of move because we can't generate SAN after the
       * move is made
       */
      var pretty_move = make_pretty(move_obj)

      make_move(move_obj)

      return pretty_move
    },

    undo: function() {
      var move = undo_move()
      return move ? make_pretty(move) : null
    },

    clear: function() {
      return clear()
    },

    put: function(piece, square) {
      return put(piece, square)
    },

    get: function(square) {
      return get(square)
    },

    remove: function(square) {
      return remove(square)
    },

    perft: function(depth) {
      return perft(depth)
    },

    square_color: function(square) {
      if (square in SQUARES) {
        var sq_0x88 = SQUARES[square]
        return (rank(sq_0x88) + file(sq_0x88)) % 2 === 0 ? 'light' : 'dark'
      }

      return null
    },

    history: function(options) {
      var reversed_history = []
      var move_history = []
      var verbose =
        typeof options !== 'undefined' &&
        'verbose' in options &&
        options.verbose

      while (history.length > 0) {
        reversed_history.push(undo_move())
      }

      while (reversed_history.length > 0) {
        var move = reversed_history.pop()
        if (verbose) {
          move_history.push(make_pretty(move))
        } else {
          move_history.push(move_to_san(move))
        }
        make_move(move)
      }

      return move_history
    }
  }
}

/* export Chess object if using node or any other CommonJS compatible
 * environment */
if (typeof exports !== 'undefined') exports.Chess = Chess
/* export Chess object for any RequireJS compatible environment */
if (typeof define !== 'undefined')
  define(function() {
    return Chess
  })

// ── CARGA DEL MOTOR: stockfish-19.js + stockfish-19.wasm ─────────────
const archivos = { js: null, wasm: null };
const uploadStatus = document.getElementById('uploadStatus');
const uploadDot = document.getElementById('uploadDot');
const uploadMsg = document.getElementById('uploadMsg');
const avisoIso = document.getElementById('avisoIso');
let motorArrancando = false;

function mostrarEstado(tipo, msg) {
  uploadStatus.style.display = 'flex';
  uploadDot.className = 'dot ' + tipo;
  uploadMsg.textContent = msg;
}
function mostrarUploadError(msg) { mostrarEstado('error', msg); motorArrancando = false; }

// El motor usa hilos (SharedArrayBuffer): solo funciona si la página está "aislada".
const aislada = window.crossOriginIsolated === true && typeof SharedArrayBuffer !== 'undefined';
if (!aislada) {
  avisoIso.style.display = 'block';
  avisoIso.innerHTML = '<strong>Página no aislada.</strong> Este motor necesita que abras el juego con el servidor Python ' +
    '(<code>ajedrez_servidor.py</code>) en <code>http://localhost:8000</code>. Si abriste el HTML como archivo o desde otra IP, el motor no arrancará.';
}

function conectarZona(idZona, idInput) {
  const zona = document.getElementById(idZona), input = document.getElementById(idInput);
  zona.addEventListener('click', () => input.click());
  input.addEventListener('change', () => { if (input.files[0]) archivoElegido(input.files[0]); input.value = ''; });
}
conectarZona('zonaJs', 'fileJs');
conectarZona('zonaWasm', 'fileWasm');

const tarjeta = document.getElementById('uploadCard');
tarjeta.addEventListener('dragover', e => { e.preventDefault(); });
tarjeta.addEventListener('drop', e => {
  e.preventDefault();
  for (const f of e.dataTransfer.files) archivoElegido(f);
});

async function archivoElegido(file) {
  const nombre = file.name.toLowerCase();
  if (nombre.endsWith('.js')) {
    archivos.js = file;
    document.getElementById('zonaJs').classList.add('ok');
    document.getElementById('lblJs').innerHTML = '✔ <strong>' + file.name + '</strong> (' + (file.size/1024).toFixed(0) + ' KB)';
  } else if (nombre.endsWith('.wasm')) {
    const cab = new Uint8Array(await file.slice(0, 4).arrayBuffer());
    if (!(cab[0] === 0 && cab[1] === 0x61 && cab[2] === 0x73 && cab[3] === 0x6d)) {
      mostrarUploadError('Ese .wasm no es un WebAssembly válido.'); return;
    }
    archivos.wasm = file;
    document.getElementById('zonaWasm').classList.add('ok');
    document.getElementById('lblWasm').innerHTML = '✔ <strong>' + file.name + '</strong> (' + (file.size/1048576).toFixed(1) + ' MB)';
  } else {
    mostrarUploadError('Archivo no reconocido: usa stockfish-19.js y stockfish-19.wasm.'); return;
  }
  if (archivos.js && archivos.wasm) arrancarMotor();
  else mostrarEstado('idle', 'Falta ' + (archivos.js ? 'el .wasm' : 'el .js') + '.');
}

let _jsUrl = null, _wasmUrl = null;  // URLs blob guardadas para crear workers adicionales
async function arrancarMotor() {
  if (motorArrancando) return;
  if (!aislada) { mostrarUploadError('Página no aislada: abre el juego con ajedrez_servidor.py (http://localhost:8000).'); return; }
  motorArrancando = true;
  try {
    mostrarEstado('think', 'Leyendo stockfish-19.js…');
    let codigo = await archivos.js.text();
    // El motor crea sus hilos a partir de su propia URL; con una URL blob:
    // hay que construirla a partir de location.href (parche mínimo).
    const original = 'self.location.origin+self.location.pathname+"#"+u+",worker"';
    if (!codigo.includes(original)) throw new Error('Este stockfish-19.js no es la versión esperada.');
    codigo = codigo.split(original).join('self.location.href.split("#")[0]+"#"+u+",worker"');

    const jsUrl   = URL.createObjectURL(new Blob([codigo], { type: 'text/javascript' }));
    const wasmUrl = URL.createObjectURL(new Blob([archivos.wasm], { type: 'application/wasm' }));
    _jsUrl = jsUrl; _wasmUrl = wasmUrl;  // guardar para crearWorkerClasificador

    mostrarEstado('think', 'Compilando el motor (99 MB), puede tardar unos segundos…');
    const w = new Worker(jsUrl + '#' + encodeURIComponent(wasmUrl));
    let listo = false;
    const limite = setTimeout(() => { if (!listo) mostrarUploadError('El motor no respondió en 90 s.'); }, 90000);

    w.onerror = (ev) => { if (!listo) { clearTimeout(limite); mostrarUploadError('Error del motor: ' + (ev.message || 'no se pudo iniciar')); } };
    w.onmessage = (ev) => {
      const msg = typeof ev.data === 'string' ? ev.data : null;
      if (!msg) return;
      if (!listo) {
        if (msg === 'uciok') {
          w.postMessage('setoption name MultiPV value 5');
          w.postMessage('setoption name Threads value ' + NUM_HILOS);
          w.postMessage('setoption name Hash value 64');
          w.postMessage('isready');
        } else if (msg === 'readyok') {
          listo = true; clearTimeout(limite);
          uploadDot.className = 'dot ok';
          uploadMsg.textContent = '¡Motor listo! Iniciando…';
          w.onmessage = onSFMessage;
          iniciarJuego(w, 'Stockfish 19 · ' + NUM_HILOS + (NUM_HILOS === 1 ? ' hilo' : ' hilos'));
        }
        return;
      }
    };
    w.postMessage('uci');
  } catch (err) {
    mostrarUploadError('Error: ' + err.message);
  }
}
const NUM_HILOS = Math.max(1, Math.min(4, (navigator.hardwareConcurrency || 2) - 1));

// Crea un worker independiente de Stockfish para clasificar puzzles sin
// interferir con sfEngine (el worker principal de juego/análisis en vivo).
function crearWorkerClasificador(onReady) {
  if (!_jsUrl || !_wasmUrl) { console.error('crearWorkerClasificador: URLs no disponibles'); return; }
  const w = new Worker(_jsUrl + '#' + encodeURIComponent(_wasmUrl));
  w.onerror = (ev) => console.error('Worker clasificador error:', ev.message);
  w.onmessage = (ev) => {
    const msg = typeof ev.data === 'string' ? ev.data : null;
    if (!msg) return;
    if (msg === 'uciok') {
      w.postMessage('setoption name MultiPV value 5');
      w.postMessage('setoption name Threads value 1');
      w.postMessage('setoption name Hash value 16');
      w.postMessage('isready');
    } else if (msg === 'readyok') {
      onReady(w);
    }
  };
  w.postMessage('uci');
}

// ── JUEGO ─────────────────────────────────────────────
let chess, sfEngine, seleccionada, moviendoSF, timerInterval, historial, bestLines;
let modoAnalisis = false, anChess = null, anFlipped = false;
let esperandoBest = false, temporizadorSeguridad = null, temporizadorStop = null, kActual = 5;
let bandoJugador = 'w';   // 'w' = usuario blancas, 'b' = usuario negras

function iniciarJuego(worker, etiqueta) {
  sfEngine = worker;
  document.getElementById('uploadScreen').style.display = 'none';
  document.getElementById('gameScreen').style.display = 'flex';
  document.getElementById('sfTag').textContent = 'Motor: ' + etiqueta;
  chess = new Chess();
  seleccionada = null; moviendoSF = false; historial = []; bestLines = [];
  actualizarBandoUI();
  renderCoords(); renderBoard();
  actualizarTurno();
  anEl('anAnalBtn').disabled = false;
  if (bandoJugador === 'b') {
    setStatus('think', 'Motor listo. Stockfish empieza…');
    setTimeout(pedirJugadaSF, 400);
  } else {
    setStatus('ok', 'Motor listo. Tu turno.');
  }
}

function actualizarBandoUI() {
  const esNegras = bandoJugador === 'b';
  document.getElementById('btnBandoBlancas').className = 'btn ' + (esNegras ? 'btn-secondary' : 'btn-primary');
  document.getElementById('btnBandoBlancas').style.background = esNegras ? '#2a2a3e' : '';
  document.getElementById('btnBandoBlancas').style.color = esNegras ? 'var(--texto)' : '';
  document.getElementById('btnBandoNegras').className = 'btn ' + (esNegras ? 'btn-primary' : 'btn-secondary');
  document.getElementById('btnBandoNegras').style.background = esNegras ? '' : '#2a2a3e';
  document.getElementById('btnBandoNegras').style.color = esNegras ? '' : 'var(--texto)';
  const sub = document.getElementById('subtitulo');
  if (sub) sub.textContent = esNegras ? 'Tú juegas con negras · Stockfish con blancas' : 'Tú juegas con blancas · Stockfish con negras';
  // Actualizar label del umbral según bando
  const lblUmbral = document.getElementById('lblUmbral');
  if (lblUmbral) {
    if (esNegras) {
      lblUmbral.innerHTML = '<strong>Ventaja de las blancas</strong><br>Peones (+ blancas, − negras). Como juegas con negras, busca valores negativos (ej. −2) para que SF te deje en desventaja controlada.';
    } else {
      lblUmbral.innerHTML = '<strong>Ventaja de las blancas</strong><br>Peones (+ = ventaja blanca). Se juega la jugada que deje esa ventaja o la más cercana.';
    }
  }
}

function leerNumero(id, porDefecto, min, max, entero) {
  const crudo = document.getElementById(id).value;
  let v = entero ? parseInt(crudo) : parseFloat(crudo);
  if (!isFinite(v)) v = porDefecto;
  return Math.min(max, Math.max(min, v));
}

function onSFMessage(ev) {
  // Delegar al manejador de análisis mientras su motor tenga una búsqueda en
  // curso, en cola o pendiente de confirmar su parada — incluso si ya se
  // cambió de pestaña o se pulsó "Detener" justo antes de que llegara el
  // bestmove. Si no, ese bestmove "huérfano" se confundiría con el de una
  // jugada de la partida.
  if ((anAnalAndo || anBusquedaEnCurso || anEsperandoParada) && onSFMessageAn(ev)) return;
  const msg = typeof ev === 'string' ? ev : ev.data;
  if (typeof msg !== 'string') return;
  if (msg.startsWith('info') && msg.includes(' pv ') && !msg.includes('bound')) {
    const cpM   = msg.match(/score cp (-?\d+)/);
    const mateM = msg.match(/score mate (-?\d+)/);
    const pvM   = msg.match(/ pv (\S+)/);
    const pvNM  = msg.match(/multipv (\d+)/);
    if (pvM && (cpM || mateM)) {
      let score;   // evaluación de Stockfish desde las NEGRAS (quien mueve)
      if (cpM) score = parseInt(cpM[1]) / 100;
      else { const n = parseInt(mateM[1]); score = (n >= 0 ? 1 : -1) * (100 - Math.min(Math.abs(n), 99)); }
      const pvNum = pvNM ? parseInt(pvNM[1]) - 1 : 0;
      bestLines[pvNum] = { score, move: pvM[1] };
    }
  } else if (msg.startsWith('bestmove')) {
    if (!esperandoBest) return;
    esperandoBest = false;
    clearTimeout(temporizadorStop); clearTimeout(temporizadorSeguridad);
    if (!bestLines.some(l => l)) {           // respaldo: solo llegó bestmove
      const m = msg.match(/^bestmove (\S+)/);
      if (m && m[1] !== '(none)') bestLines[0] = { score: 0, move: m[1] };
    }
    elegirJugada(leerNumero('umbral', 2, -20, 20, false));
  }
}

function pedirJugadaSF() {
  if (!sfEngine || chess.game_over()) return;
  moviendoSF = true; bestLines = []; esperandoBest = true;
  const segundos = leerNumero('tiempo', 5, 1, 30, true);
  kActual = leerNumero('numJugadas', 5, 1, 30, true);
  setStatus('think', 'Stockfish analizando (' + segundos + 's, ' + kActual + ' jugadas)…');
  animarBarra(segundos);
  sfEngine.postMessage('setoption name MultiPV value ' + kActual);
  sfEngine.postMessage('position fen ' + chess.fen());
  sfEngine.postMessage('go infinite');
  // Corte literal: a los N segundos se detiene el análisis; el motor responde con bestmove.
  temporizadorStop = setTimeout(() => { if (esperandoBest) sfEngine.postMessage('stop'); }, segundos * 1000);
  // Seguridad: si no llega bestmove, se decide con lo analizado hasta el momento.
  temporizadorSeguridad = setTimeout(() => {
    if (!esperandoBest) return;
    esperandoBest = false;
    sfEngine.postMessage('stop');
    elegirJugada(leerNumero('umbral', 2, -20, 20, false));
  }, segundos * 1000 + 5000);
}

// Regla del umbral (T = ventaja de las BLANCAS en peones).
// SF evalúa siempre desde quien mueve. signoVB convierte el score crudo a
// ventaja blancas: si SF mueve negras -> vb = -score; si mueve blancas -> vb = score.
//  1) Entre las líneas con vb >= T se elige la de MENOR vb (la más cercana por arriba).
//  2) Si ninguna llega a T, se elige la de MAYOR vb (la más cercana por debajo).
function elegirLinea(lineas, T, signoVB) {
  const cand = lineas.filter(l => l && l.move && isFinite(l.score))
                     .map(l => ({ score: l.score, move: l.move, vb: signoVB * l.score }));
  if (!cand.length) return null;
  const alcanzan = cand.filter(c => c.vb >= T);
  if (alcanzan.length) return alcanzan.reduce((a, b) => (b.vb < a.vb ? b : a));
  return cand.reduce((a, b) => (b.vb > a.vb ? b : a));
}

function elegirJugada(umbral) {
  clearInterval(timerInterval);
  document.getElementById('timerBar').style.width = '0%';
  moviendoSF = false;
  // SF juega el bando contrario al usuario. Si el usuario es negras, SF juega blancas.
  const sfJuegaBlancas = bandoJugador === 'b';
  const signoVB = sfJuegaBlancas ? 1 : -1;
  const elegida = elegirLinea(bestLines.slice(0, kActual), umbral, signoVB);
  if (!elegida) { setStatus('error', 'Sin respuesta del motor.'); return; }
  const mov = chess.move({ from: elegida.move.slice(0,2), to: elegida.move.slice(2,4), promotion: 'q' });
  if (mov) {
    historial.push(mov.san);
    actualizarHistorial(); renderBoard(); mostrarMoveInfo(mov.san, elegida.vb);   // indicador: + ventaja blancas, - ventaja negras
    if (chess.game_over()) return finJuego();
    setStatus('ok', 'Tu turno (' + (bandoJugador==='w'?'blancas':'negras') + ').'); actualizarTurno();
  } else {
    setStatus('error', 'Jugada SF inválida: ' + elegida.move);
  }
}

// ── TABLERO ───────────────────────────────────────────
const PIEZAS = {
  wP:'♙',wN:'♘',wB:'♗',wR:'♖',wQ:'♕',wK:'♔',
  bP:'♟',bN:'♞',bB:'♝',bR:'♜',bQ:'♛',bK:'♚'
};

function renderBoard() {
  const board = document.getElementById('tablero');
  board.innerHTML = '';
  const pos = (modoAnalisis ? anChess : chess).board();
  // Rotar: en juego normal si el usuario juega con negras; en análisis si el usuario giró
  const rotar = modoAnalisis ? anFlipped : bandoJugador === 'b';
  for (let r=0;r<8;r++) for (let c=0;c<8;c++) {
    const rr = rotar ? 7-r : r;
    const cc = rotar ? 7-c : c;
    const div = document.createElement('div');
    div.className = 'casilla ' + ((rr+cc)%2===0 ? 'claro' : 'oscuro');
    const pieza = pos[rr][cc];
    if (pieza) {
      div.textContent = PIEZAS[pieza.color + pieza.type.toUpperCase()];
      div.style.color = pieza.color==='w' ? '#fff' : '#111';
      div.style.textShadow = pieza.color==='w' ? '0 1px 3px rgba(0,0,0,.7)' : '0 1px 2px rgba(255,255,255,.3)';
      div.classList.add('ocupada');
    }
    const sq = String.fromCharCode(97+cc) + (8-rr);
    div.dataset.sq = sq;
    if (modoAnalisis && anUlt && (sq === anUlt.from || sq === anUlt.to)) div.classList.add('ult');
    div.addEventListener('click', () => onClic(sq));
    board.appendChild(div);
  }
  if (!modoAnalisis && seleccionada) {
    const moves = chess.moves({ square: seleccionada, verbose: true });
    document.querySelectorAll('.casilla').forEach(d => {
      if (d.dataset.sq === seleccionada) d.classList.add('sel');
      if (moves.find(m => m.to === d.dataset.sq)) d.classList.add('posible');
    });
  }
  if (modoAnalisis && anSeleccionada) {
    const moves = anChess.moves({ square: anSeleccionada, verbose: true });
    document.querySelectorAll('.casilla').forEach(d => {
      if (d.dataset.sq === anSeleccionada) d.classList.add('an-sel');
      if (moves.find(m => m.to === d.dataset.sq)) d.classList.add('an-posible');
    });
  }
}

function onClic(sq) {
  if (modoAnalisis) {
    if (anEditandoPos) { anEditClicTablero(sq); return; }
    anClicTablero(sq);
    return;
  }
  if (moviendoSF || chess.turn() !== bandoJugador || chess.game_over()) return;
  const pieza = chess.get(sq);
  if (!seleccionada) {
    if (pieza && pieza.color === bandoJugador) { seleccionada=sq; renderBoard(); }
    return;
  }
  const mov = chess.move({ from: seleccionada, to: sq, promotion: 'q' });
  seleccionada = null;
  if (mov) {
    historial.push(mov.san); actualizarHistorial(); renderBoard();
    mostrarMoveInfo(mov.san, null);
    if (chess.game_over()) return finJuego();
    actualizarTurno(); setTimeout(pedirJugadaSF, 300);
  } else {
    if (pieza && pieza.color === bandoJugador) seleccionada = sq;
    renderBoard();
  }
}

function renderCoords() {
  const col = document.getElementById('coordCol');
  const row = document.getElementById('coordRow');
  col.innerHTML = ''; row.innerHTML = '';
  const rotar = modoAnalisis ? anFlipped : bandoJugador === 'b';
  const letras = rotar ? 'hgfedcba'.split('') : 'abcdefgh'.split('');
  letras.forEach(l => { const s=document.createElement('span'); s.textContent=l; col.appendChild(s); });
  const nums = rotar ? [1,2,3,4,5,6,7,8] : [8,7,6,5,4,3,2,1];
  nums.forEach(i => { const s=document.createElement('span'); s.textContent=i; row.appendChild(s); });
}

function setStatus(type, msg) {
  document.getElementById('dot').className = 'dot ' + type;
  document.getElementById('statusMsg').textContent = msg;
}

function animarBarra(s) {
  const bar = document.getElementById('timerBar');
  bar.style.width = '0%';
  const start = Date.now();
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const pct = Math.min((Date.now()-start)/(s*1000)*100,100);
    bar.style.width = pct + '%';
    if (pct>=100) clearInterval(timerInterval);
  }, 50);
}

function mostrarMoveInfo(san, score) {
  document.getElementById('lastMove').textContent = 'Última: ' + san;
  const badge = document.getElementById('scoreBadge');
  if (score !== null && score !== undefined) {
    badge.textContent = Math.abs(score)>=90 ? (score>0?'+M':'-M')+(100-Math.abs(score)) : (score>=0?'+':'') + score.toFixed(2);
    badge.className = 'score-badge' + (score<0?' neg':'');
  } else { badge.textContent=''; badge.className='score-badge'; }
}

function actualizarHistorial() {
  const h = document.getElementById('historial');
  if (!historial.length) { h.textContent='Sin jugadas aún'; return; }
  let txt='';
  for (let i=0;i<historial.length;i+=2)
    txt += (Math.floor(i/2)+1)+'. '+historial[i]+(historial[i+1]?' '+historial[i+1]:'')+' ';
  h.textContent=txt; h.scrollTop=h.scrollHeight;
}

function actualizarTurno() {
  const ficha = document.getElementById('fichaActual');
  const label = document.getElementById('turnoLabel');
  const turno = chess.turn();
  const esTuTurno = turno === bandoJugador;
  const nombreTurno = turno === 'w' ? 'Blancas' : 'Negras';
  label.textContent = 'Turno: ' + nombreTurno + ' (' + (esTuTurno ? 'tú' : 'Stockfish') + ')';
  ficha.className = 'turno-ficha ' + (turno === 'w' ? 'blancas' : 'negras');
}

function finJuego() {
  clearInterval(timerInterval);
  document.getElementById('timerBar').style.width='0%';
  let msg;
  if (chess.in_checkmate()) {
    // chess.turn() es quien recibe el mate (el que pierde)
    const perdedor = chess.turn();
    if (perdedor === bandoJugador) msg = '¡Jaque mate! Ganó Stockfish.';
    else msg = '¡Jaque mate! ¡Ganaste!';
  } else if (chess.in_stalemate()) msg = 'Tablas por ahogado.';
  else if (chess.in_threefold_repetition()) msg = 'Tablas por repetición.';
  else if (chess.insufficient_material()) msg = 'Tablas por material insuficiente.';
  else msg = 'Partida terminada.';
  setStatus('ok', msg);
}

document.getElementById('btnNueva').addEventListener('click', () => {
  chess=new Chess(); seleccionada=null; moviendoSF=false; historial=[]; bestLines=[];
  clearInterval(timerInterval);
  document.getElementById('timerBar').style.width='0%';
  actualizarHistorial(); renderCoords(); renderBoard(); actualizarTurno();
  document.getElementById('lastMove').textContent='—';
  document.getElementById('scoreBadge').textContent='';
  if (sfEngine) { esperandoBest=false; clearTimeout(temporizadorSeguridad); clearTimeout(temporizadorStop); sfEngine.postMessage('stop'); sfEngine.postMessage('ucinewgame'); sfEngine.postMessage('isready'); }
  if (bandoJugador === 'b') {
    setStatus('think', 'Nueva partida. Stockfish empieza…');
    setTimeout(pedirJugadaSF, 400);
  } else {
    setStatus('idle', 'Nueva partida. Tu turno.');
  }
});

document.getElementById('btnUndo').addEventListener('click', () => {
  if (moviendoSF) return;
  chess.undo(); chess.undo();
  historial=historial.slice(0,-2);
  seleccionada=null; actualizarHistorial(); renderBoard(); actualizarTurno();
  setStatus('idle', 'Jugada deshecha. Tu turno (' + (bandoJugador==='w'?'blancas':'negras') + ').');
  document.getElementById('lastMove').textContent='—';
  document.getElementById('scoreBadge').textContent='';
});

// ── CARGAR PGN ────────────────────────────────────────
// No se usa chess.load_pgn (bug conocido: con partidas terminadas en '*'
// devuelve la posición inicial). En su lugar se extraen las jugadas SAN
// a mano y se reproducen una por una con chess.move(), que sí es fiable.
function parsePGNJugadas(texto) {
  let t = texto.replace(/\[[^\]]*\]/g, ' ');      // quita encabezados [Tag "valor"]
  t = t.replace(/\{[^}]*\}/g, ' ');               // quita comentarios {..}
  t = t.replace(/\([^)]*\)/g, ' ');               // quita variantes (..)
  t = t.replace(/\$\d+/g, ' ');                   // quita anotaciones NAG ($1, $2..)
  t = t.replace(/\d+\.(\.\.)?/g, ' ');             // quita números de jugada "12." / "12..."
  t = t.replace(/1-0|0-1|1\/2-1\/2|\*/g, ' ');     // quita el resultado final
  return t.split(/\s+/).filter(Boolean);
}

function cargarPGN(texto) {
  const jugadas = parsePGNJugadas(texto);
  if (!jugadas.length) { setStatus('error', 'El archivo PGN no tiene jugadas.'); return; }
  const nuevo = new Chess();
  const nuevoHist = [];
  for (const tok of jugadas) {
    const mov = nuevo.move(tok, { sloppy: true });
    if (!mov) { setStatus('error', 'Jugada inválida en el PGN: "' + tok + '"'); return; }
    nuevoHist.push(mov.san);
  }
  if (sfEngine) { esperandoBest = false; clearTimeout(temporizadorSeguridad); clearTimeout(temporizadorStop); sfEngine.postMessage('stop'); }
  chess = nuevo; historial = nuevoHist; seleccionada = null; moviendoSF = false; bestLines = [];
  clearInterval(timerInterval); document.getElementById('timerBar').style.width = '0%';
  actualizarHistorial(); renderBoard(); actualizarTurno();
  document.getElementById('lastMove').textContent = historial.length ? 'Última: ' + historial[historial.length - 1] : '—';
  document.getElementById('scoreBadge').textContent = '';
  if (chess.game_over()) { finJuego(); return; }
  if (chess.turn() !== bandoJugador) {
    setStatus('think', 'Partida cargada (' + jugadas.length + ' jugadas). Turno de Stockfish…');
    setTimeout(pedirJugadaSF, 300);
  } else {
    setStatus('ok', 'Partida cargada (' + jugadas.length + ' jugadas). Tu turno.');
  }
}

document.getElementById('filePgn').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => cargarPGN(reader.result);
  reader.onerror = () => setStatus('error', 'No se pudo leer el archivo PGN.');
  reader.readAsText(file);
  e.target.value = '';
});

// ── ANÁLISIS ──────────────────────────────────────────
// Estado: una partida = FEN inicial + lista de jugadas SAN. `idx` = posición
// mostrada (0 = antes de la 1ª jugada). Cortar/borrar solo tocan esta lista;
// la partida de la pestaña Jugar no se modifica.
const FEN_INICIAL = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
let an = { inicio: FEN_INICIAL, movs: [], idx: 0, ini: null, fin: null };
let anUlt = null, anPila = [], puzzles = [];
let puzzleActivo = null;   // puzzle que se está resolviendo (null = ninguno)
anChess = new Chess();
function anEl(id) { return document.getElementById(id); }

function anMsg(tipo, texto) {
  const m = anEl('anMsg');
  m.className = 'an-msg' + (tipo ? ' ' + tipo : '');
  m.textContent = texto || '';
}

function anGuardar() { anPila.push(JSON.stringify(an)); if (anPila.length > 30) anPila.shift(); }

function anInfoInicio() {
  const p = an.inicio.split(' ');
  return { turno: p[1] === 'b' ? 'b' : 'w', num: parseInt(p[5]) || 1 };
}
function anNumero(p) {                       // p = índice de jugada (0-based)
  const s = anInfoInicio(), off = s.turno === 'b' ? 1 : 0;
  return { num: s.num + Math.floor((p + off) / 2), blanca: ((p + off) % 2) === 0 };
}
function anEtiqueta(i) {                     // posición tras i jugadas
  if (i === 0) return 'posición inicial';
  const n = anNumero(i - 1);
  return n.num + (n.blanca ? '.' : '…') + ' ' + an.movs[i - 1];
}

function anIr(i) {
  an.idx = Math.max(0, Math.min(an.movs.length, i));
  anChess = new Chess(an.inicio);
  anUlt = null; anSeleccionada = null;
  for (let k = 0; k < an.idx; k++) {
    const m = anChess.move(an.movs[k], { sloppy: true });
    if (!m) break;
    if (k === an.idx - 1) anUlt = { from: m.from, to: m.to };
  }
  // Detener análisis SF si estaba corriendo; relanzar si auto-análisis activo.
  // anDetenerSF/anArrancarSF gestionan la cola con el motor sin razas de signo.
  if (anAnalAndo) anDetenerSF();
  anActualizarTurno();
  anActualizar();
  if (anAutoAnalizar()) anArrancarSF();
}

function anRenderLista() {
  const cont = anEl('anLista');
  cont.innerHTML = '';
  if (!an.movs.length) { cont.textContent = 'Sin jugadas. Carga un PGN o usa la partida actual.'; return; }
  let act = null;
  an.movs.forEach((san, p) => {
    const n = anNumero(p);
    if (n.blanca || p === 0) {
      const num = document.createElement('span');
      num.className = 'an-num';
      num.textContent = n.num + (n.blanca ? '.' : '…');
      cont.appendChild(num);
    }
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'an-mov'; b.textContent = san;
    if (p + 1 === an.idx) { b.classList.add('act'); act = b; }
    if (an.ini !== null && an.fin !== null && p >= an.ini && p < an.fin) b.classList.add('rango');
    if (an.ini !== null && p === an.ini) b.classList.add('m-ini');
    if (an.fin !== null && p === an.fin - 1) b.classList.add('m-fin');
    b.addEventListener('click', () => anIr(p + 1));
    cont.appendChild(b);
  });
  if (act) cont.scrollTop = Math.max(0, act.offsetTop - cont.clientHeight / 2);
}

function anActualizarBarraPuzzle() {
  const barra = anEl('anPuzzleBarra');
  if (puzzleActivo) {
    barra.style.display = 'flex';
    anEl('anPuzzleActivoTxt').textContent = 'Resolviendo: ' + puzzleActivo.nombre;
  } else {
    barra.style.display = 'none';
  }
}

// Corta el puzzle en curso (y la cadena, si la había) sin deshacer jugadas ya hechas.
function anDetenerPuzzle() {
  if (!puzzleActivo) return;
  anCronDetener();
  puzzleActivo = null;
  colaPuzzles = [];
  anMsg('info', 'Puzzle detenido.');
  anActualizarBarraPuzzle();
}

function anActualizar() {
  anActualizarBarraPuzzle();
  renderBoard();
  anRenderLista();
  // Sincronizar la caja de texto con la partida y resaltar la jugada activa —
  // solo si el usuario no está escribiendo ahí mismo (si no, le pisaríamos
  // lo que está tecleando; en ese caso se resincroniza al salir del foco).
  if (document.activeElement !== anEl('anEditor')) anRenderEditor();
  const n = an.movs.length;
  anEl('anPos').textContent = 'Posición: ' + anEtiqueta(an.idx) + '  (' + an.idx + ' de ' + n + ')';
  const resto = n - an.idx;
  anEl('anBorrar').textContent = resto === 0 ? 'Borrar jugadas siguientes'
    : resto === 1 ? 'Borrar la jugada siguiente' : 'Borrar las ' + resto + ' jugadas siguientes';
  anEl('anInicio').disabled = anEl('anAnt').disabled = an.idx === 0;
  anEl('anSig').disabled = anEl('anFinal').disabled = an.idx === n;
  anEl('anCortar').disabled = an.idx === 0;
  anEl('anBorrar').disabled = resto === 0;
  anEl('anDeshacerEd').disabled = anPila.length === 0;
  anEl('anDescargar').disabled = n === 0;
  const listo = an.ini !== null && an.fin !== null && an.fin > an.ini;
  anEl('anCrearPuzzle').disabled = !listo;
  anEl('anQuitarMarcas').disabled = an.ini === null && an.fin === null;
  anEl('anMarcaTxt').textContent =
    'Inicio: ' + (an.ini === null ? 'sin marcar' : anEtiqueta(an.ini)) + '\n' +
    'Fin: ' + (an.fin === null ? 'sin marcar' : anEtiqueta(an.fin)) +
    (listo ? '\nJugadas del puzzle: ' + (an.fin - an.ini) : '');
}

// ── Editor de PGN (caja editable, sin dependencias externas) ──────────
function anEsc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Repinta la caja con la partida actual, resaltando la jugada activa.
// Solo se llama cuando el usuario NO tiene el foco ahí (ver anActualizar).
function anRenderEditor() {
  const el = anEl('anEditor');
  if (!el) return;
  const pgn = an.movs.length > 0 ? pgnDe(an.inicio, an.movs, {}) : '';
  if (!pgn) { el.innerHTML = ''; return; }
  const partes = pgn.split(/(\s+)/); // conserva los separadores
  let sanCount = 0, html = '';
  for (const p of partes) {
    if (p === '' || /^\s+$/.test(p)) { html += anEsc(p); continue; }
    const esSAN = p !== '*' && !/\.$/.test(p) && p[0] !== '[';
    if (esSAN) {
      const activo = sanCount === an.idx - 1;
      html += activo ? '<span class="an-jugada-act">' + anEsc(p) + '</span>' : anEsc(p);
      sanCount++;
    } else {
      html += anEsc(p);
    }
  }
  el.innerHTML = html;
}

// Núcleo: interpreta texto tipo PGN y lo aplica como la partida en análisis.
// verboso=true muestra mensajes de éxito/error (botón "Cargar PGN" o archivo);
// verboso=false es para la edición en vivo, más silenciosa (mientras se
// escribe, el texto casi siempre está "a medio terminar" y no es un error).
function anAplicarPGN(texto, verboso) {
  const t = texto.split(/\n\s*(?=\[Event )/)[0];      // solo la 1ª partida si hay varias
  let inicio = FEN_INICIAL;
  const mf = t.match(/\[FEN\s+"([^"]+)"\]/);
  if (mf) {
    const test = new Chess();
    if (!test.load(mf[1].trim())) { if (verboso) anMsg('error', 'El FEN del PGN no es válido.'); return; }
    inicio = test.fen();
  }
  const toks = parsePGNJugadas(t);
  if (!toks.length && !mf) { if (verboso) anMsg('error', 'No encontré jugadas en ese PGN.'); return; }
  const c = new Chess(inicio), sans = [];
  let malo = null;
  for (const tok of toks) {
    const m = c.move(tok, { sloppy: true });
    if (!m) { malo = tok; break; }
    sans.push(m.san);
  }
  puzzleActivo = null; colaPuzzles = [];
  an = { inicio: inicio, movs: sans, idx: sans.length, ini: null, fin: null };
  anIr(sans.length);   // posicionar en la última jugada al cargar
  if (verboso) {
    if (malo) anMsg('error', 'Cargué ' + sans.length + ' jugadas y me detuve en "' + malo + '" porque no es legal en esa posición.');
    else anMsg('ok', 'Partida cargada: ' + sans.length + ' jugadas.');
  }
}

// Botón "Cargar PGN" / abrir archivo: guarda un punto de deshacer y aplica
// mostrando mensajes.
function anCargarTexto(texto) {
  anGuardar();
  anAplicarPGN(texto, true);
}

// Edición en vivo dentro de la caja: NO guarda un punto de deshacer en cada
// tecla (eso saturaría "Deshacer" con un estado por letra); el punto de
// deshacer se guarda una sola vez, al entrar a editar (ver anEl('anEditor')
// listener 'focus' más abajo).
function anAplicarEdicionViva() {
  const el = anEl('anEditor');
  if (!el) return;
  anAplicarPGN(el.textContent, false);
}

function anUsarActual() {
  const h = chess.history();
  if (!h.length) { anMsg('info', 'La partida actual todavía no tiene jugadas.'); return; }
  anGuardar();
  puzzleActivo = null; colaPuzzles = [];
  an = { inicio: FEN_INICIAL, movs: h, idx: h.length, ini: null, fin: null };
  anIr(h.length);
  anMsg('ok', 'Partida actual copiada: ' + h.length + ' jugadas.');
}

// ── Editar ────────────────────────────────────────────
function anCortar() {
  if (an.idx === 0) return;
  anGuardar();
  const quitadas = an.idx;
  an = { inicio: anChess.fen(), movs: an.movs.slice(an.idx), idx: 0, ini: null, fin: null };
  anIr(0);
  anMsg('ok', 'Corte hecho: quité las ' + quitadas + ' jugadas anteriores. La partida empieza en esta posición.');
}

function anBorrar() {
  if (an.idx >= an.movs.length) return;
  anGuardar();
  const q = an.movs.length - an.idx;
  an.movs = an.movs.slice(0, an.idx);
  if (an.ini !== null && an.ini > an.idx) an.ini = null;
  if (an.fin !== null && an.fin > an.idx) an.fin = null;
  anIr(an.idx);
  anMsg('ok', 'Borré ' + q + (q === 1 ? ' jugada' : ' jugadas') + ' desde esta posición hasta el final.');
}

function anDeshacerEd() {
  if (!anPila.length) return;
  an = JSON.parse(anPila.pop());
  anIr(an.idx);
  anMsg('info', 'Cambio deshecho.');
}

// ── PGN y descargas ───────────────────────────────────
function pgnDe(fen, sans, cabeceras) {
  const p = fen.split(' '), off = p[1] === 'b' ? 1 : 0, num = parseInt(p[5]) || 1;
  let txt = '';
  for (const k in cabeceras) txt += '[' + k + ' "' + cabeceras[k] + '"]\n';
  if (fen !== FEN_INICIAL) txt += '[SetUp "1"]\n[FEN "' + fen + '"]\n';
  txt += '\n';
  const partes = sans.map((s, i) => {
    const blanca = ((i + off) % 2) === 0, n = num + Math.floor((i + off) / 2);
    return blanca ? n + '. ' + s : (i === 0 ? n + '... ' + s : s);
  });
  return txt + partes.join(' ') + (partes.length ? ' ' : '') + '*\n';
}

function descargar(nombre, texto, tipo) {
  const url = URL.createObjectURL(new Blob([texto], { type: tipo }));
  const a = document.createElement('a');
  a.href = url; a.download = nombre;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function nombreArchivo(s) { return (s || 'partida').replace(/[^\w\-]+/g, '_').slice(0, 40) || 'partida'; }

// ── Puzzles ───────────────────────────────────────────
function guardarPuzzles() { try { localStorage.setItem('ajedrez_puzzles', JSON.stringify(puzzles)); } catch (e) {} }

// Elo real (fórmula Elo con la dificultad estimada de cada puzzle): sube una
// vez al completar el puzzle y baja con cada jugada errada. Se guarda en
// localStorage junto con resueltos/fallos de toda la vida.
let eloJugador = 1200;
let pzAciertos = 0;
let pzFallos   = 0;

function cargarElo() {
  try {
    const r = JSON.parse(localStorage.getItem('ajedrez_elo') || 'null');
    if (r && typeof r.elo === 'number') eloJugador = r.elo;
  } catch(e) {}
}
function guardarElo() {
  try { localStorage.setItem('ajedrez_elo', JSON.stringify({ elo: eloJugador })); } catch(e) {}
}
function cargarEloHistorial() {
  try {
    const r = JSON.parse(localStorage.getItem('ajedrez_elo_historial') || '[]');
    return Array.isArray(r) ? r : [];
  } catch(e) { return []; }
}
function guardarEloHistorial(h) {
  try { localStorage.setItem('ajedrez_elo_historial', JSON.stringify(h)); } catch(e) {}
}
function eloK() { return 40; }
function aplicarElo(ratingEst, resultado) {
  const esperado = 1 / (1 + Math.pow(10, (ratingEst - eloJugador) / 400));
  eloJugador = Math.max(100, Math.round(eloJugador + eloK() * (resultado - esperado)));
  guardarElo();
}
function estimarDificultad(lineas) {
  if (!lineas || lineas.length < 2) return 1000;
  function cp(l) {
    if (l.mate != null) return l.mate > 0 ? 3000 : -3000;
    return l.score != null ? Math.round(l.score * 100) : 0;
  }
  const brecha = Math.abs(cp(lineas[0]) - cp(lineas[1]));
  if (brecha >= 300) return 800;
  if (brecha >= 150) return 1200;
  if (brecha >= 75)  return 1500;
  if (brecha >= 30)  return 1800;
  return 2200;
}
function anRenderPzStats() {
  const hist = cargarEloHistorial();
  let html = 'Elo: <b>' + eloJugador + '</b> &nbsp;|&nbsp; ✔ ' + pzAciertos
           + ' &nbsp;|&nbsp; ✘ ' + pzFallos;
  if (hist.length >= 2) {
    const W=300, H=56, P=4;
    const elos = hist.map(p => p.elo);
    const mn = Math.min(...elos), mx = Math.max(...elos), rng = mx-mn || 1;
    const pts = elos.map((e,i) =>
      (P + i/(elos.length-1)*(W-P*2)).toFixed(1)+','+(P+(1-(e-mn)/rng)*(H-P*2)).toFixed(1)
    ).join(' ');
    html += '<br><svg viewBox="0 0 '+W+' '+H+'" style="width:100%;max-width:320px;height:56px;display:block;margin-top:4px">'
          + '<polyline points="'+pts+'" fill="none" stroke="var(--acento,#4a9eff)" stroke-width="2" stroke-linejoin="round"/></svg>';
  }
  anEl('anPzStats').innerHTML = html;
}
function anClasificarElo(pz, btn, barraEl) {
  // Usa un worker independiente (sfEngineClasificador) para no interferir
  // con sfEngine ni con el análisis en vivo. sfEngine.onmessage NO se toca.
  const msAnalisis = leerNumero('tiempo', 3, 1, 30) * 1000;

  function ejecutarConWorker(w) {
    if (!pz.jugadas) pz.jugadas = [];
    const pendientes = Array.from({length: Math.ceil(pz.solucion.length/2)}, (_,i) => i*2)
      .filter(i => !pz.jugadas[i] || !pz.jugadas[i].analizado);
    if (pendientes.length === 0) {
      w.terminate();
      btn.textContent = '✓ Clasificado';
      btn.disabled = true;
      barraEl.style.display = 'none';
      guardarPuzzles();
      return;
    }
    let paso = 0;
    let lineasCapturadas = [];
    let timerStop = null;
    function analizarSiguiente() {
      if (!document.body.contains(btn)) {
        w.terminate();
        return;
      }
      if (paso >= pendientes.length) {
        guardarPuzzles();
        w.terminate();
        btn.textContent = '✓ Clasificado';
        btn.disabled = true;
        barraEl.style.display = 'none';
        return;
      }
      const ch = new Chess(pz.fen);
      for (let k = 0; k < pendientes[paso]; k++) {
        const u = pz.uci[k];
        ch.move({ from: u.slice(0,2), to: u.slice(2,4), promotion: u[4] || 'q' });
      }
      const fen = ch.fen();
      barraEl.style.display = '';
      barraEl.textContent = 'Analizando jugada ' + (paso+1) + '/' + pendientes.length + '…';
      lineasCapturadas = [];
      w.onmessage = function(ev) {
        const d = typeof ev.data === 'string' ? ev.data : '';
        if (d.startsWith('info') && d.includes(' multipv ')) {
          const mPv = d.match(/multipv (\d+)/); if (!mPv) return;
          const pvN = parseInt(mPv[1]) - 1;
          const mCp   = d.match(/score cp (-?\d+)/);
          const mMate = d.match(/score mate (-?\d+)/);
          if (!lineasCapturadas[pvN]) lineasCapturadas[pvN] = {};
          if (mCp)   lineasCapturadas[pvN].score = parseInt(mCp[1]) / 100;
          if (mMate) lineasCapturadas[pvN].mate  = parseInt(mMate[1]);
        }
        if (d.startsWith('bestmove')) {
          clearTimeout(timerStop); timerStop = null;
          pz.jugadas[pendientes[paso]] = {
            ratingEstimado: estimarDificultad(lineasCapturadas),
            analizado: true
          };
          paso++;
          analizarSiguiente();
        }
      };
      w.postMessage('position fen ' + fen);
      w.postMessage('go infinite');
      timerStop = setTimeout(() => w.postMessage('stop'), msAnalisis);
    }
    analizarSiguiente();
  }

  // Lanzar el worker clasificador independiente
  crearWorkerClasificador(ejecutarConWorker);
}

// Cronómetro del intento en curso (arranca en anResolverPuzzle, se detiene
// al resolver o al pulsar "Detener puzzle").
let pzInicioMs = null, pzCronInterval = null, pzErroresIntento = 0;
function formatoMmSs(seg) { const m = Math.floor(seg / 60), s2 = Math.floor(seg % 60); return m + ':' + String(s2).padStart(2, '0'); }
function anCronArrancar() {
  pzInicioMs = Date.now();
  pzErroresIntento = 0;
  anCronDetener();
  anEl('anPuzzleCron').textContent = '0:00';
  pzCronInterval = setInterval(() => {
    anEl('anPuzzleCron').textContent = formatoMmSs((Date.now() - pzInicioMs) / 1000);
  }, 500);
}
function anCronDetener() { if (pzCronInterval) { clearInterval(pzCronInterval); pzCronInterval = null; } }
function anCronSegundos() { return pzInicioMs ? (Date.now() - pzInicioMs) / 1000 : 0; }

// Una jugada equivocada: baja el Elo (fórmula real, resultado 0). Cada
// jugada errada cuenta, aunque se repita.
function anPuzzleFallo() {
  pzErroresIntento++;
  pzFallos++;
  const rEst = (puzzleActivo?.jugadas?.[an.movs.length]?.ratingEstimado) ?? 1500;
  aplicarElo(rEst, 0);
  anRenderPzStats();
}
function cargarPuzzles() {
  try {
    const r = JSON.parse(localStorage.getItem('ajedrez_puzzles') || '[]');
    puzzles = Array.isArray(r) ? r : [];
  } catch (e) { puzzles = []; }
}

function anMarcar(cual) {
  if (cual === 'ini') { an.ini = an.idx; if (an.fin !== null && an.fin <= an.ini) an.fin = null; }
  else { an.fin = an.idx; if (an.ini !== null && an.ini >= an.fin) an.ini = null; }
  anActualizar();
}

function anCrearPuzzle() {
  if (an.ini === null || an.fin === null || an.fin <= an.ini) return;
  const c = new Chess(an.inicio);
  for (let k = 0; k < an.ini; k++) c.move(an.movs[k], { sloppy: true });
  const fen = c.fen(), turno = c.turn(), sol = [], uci = [];
  for (let k = an.ini; k < an.fin; k++) {
    const m = c.move(an.movs[k], { sloppy: true });
    if (!m) { anMsg('error', 'No pude reproducir el tramo elegido.'); return; }
    sol.push(m.san); uci.push(m.from + m.to + (m.promotion || ''));
  }
  const nombre = anEl('anPuzNombre').value.trim() || ('Puzzle ' + (puzzles.length + 1));
  puzzles.push({ id: Date.now(), nombre: nombre, fen: fen, turno: turno, solucion: sol, uci: uci });
  guardarPuzzles(); renderPuzzles();
  anEl('anPuzNombre').value = '';
  anMsg('ok', 'Puzzle "' + nombre + '" creado con ' + sol.length + (sol.length === 1 ? ' jugada.' : ' jugadas.'));
}

let toastT1 = null, toastT2 = null;
function anToast(texto, tipo) {
  const t = anEl('anToast');
  clearTimeout(toastT1); clearTimeout(toastT2);
  t.textContent = texto;
  t.className = 'toast' + (tipo === 'info' ? ' info' : '');
  void t.offsetWidth;                       // reinicia la animación
  t.classList.add('entra');
  toastT1 = setTimeout(() => { t.classList.remove('entra'); t.classList.add('sale'); }, 2200);
  toastT2 = setTimeout(() => { t.className = 'toast'; }, 2700);
}

// Cola de puzzles de la sesión (ids). Orden normal = orden del array
// `puzzles`; aleatorio = barajado. El puzzle pulsado va siempre primero.
let colaPuzzles = [], sesionN = 0;
function anConstruirCola(primero) {
  const aleatorio = anEl('anOrden').value === 'aleatorio';
  let ids = puzzles.map(p => p.id);
  if (aleatorio) {
    for (let i = ids.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [ids[i], ids[j]] = [ids[j], ids[i]]; }
  }
  if (primero) {
    ids = ids.filter(id => id !== primero.id);
    if (!aleatorio) {   // normal: desde el pulsado hacia delante
      const pos = puzzles.findIndex(p => p.id === primero.id);
      ids = puzzles.slice(pos + 1).map(p => p.id);
    }
    ids.unshift(primero.id);
  }
  colaPuzzles = ids;
}
function anIniciarSesion(primero) {
  if (!puzzles.length) return;
  anConstruirCola(primero || null);
  sesionN = colaPuzzles.length;
  anSiguienteDeCola();
}
function anSiguienteDeCola() {
  while (colaPuzzles.length) {
    const id = colaPuzzles.shift();
    const pz = puzzles.find(p => p.id === id);
    if (pz) { anResolverPuzzle(pz); return; }
  }
  anToast('🏁 No quedan más puzzles', 'info');
}
// Puzzle resuelto: toast y paso al siguiente de la cola.
function anPuzzleResuelto(pz) {
  anCronDetener();
  const seg = anCronSegundos();
  const t = formatoMmSs(seg);
  if (pz.mejorTiempo == null || seg < pz.mejorTiempo) { pz.mejorTiempo = seg; guardarPuzzles(); renderPuzzles(); }
  const rEst = (pz.jugadas?.[an.movs.length > 0 ? an.movs.length-1 : 0]?.ratingEstimado) ?? 1500;
  pzAciertos++; aplicarElo(rEst, 1);
  const hist = cargarEloHistorial();
  hist.push({ n: hist.length+1, elo: eloJugador });
  guardarEloHistorial(hist);
  anRenderPzStats();
  puzzleActivo = null;
  anActualizarBarraPuzzle();
  anMsg('ok', '¡Puzzle resuelto! 🎉 (' + t + (pzErroresIntento ? ', ' + pzErroresIntento + ' error' + (pzErroresIntento === 1 ? '' : 'es') : '') + ') — Elo: ' + eloJugador);
  anToast('¡Puzzle resuelto! 🎉  ' + t);
  if (colaPuzzles.length) {
    setTimeout(() => { if (!puzzleActivo) anSiguienteDeCola(); }, 1800);
  } else if (sesionN > 1) {
    setTimeout(() => { if (!puzzleActivo) anToast('🏁 No quedan más puzzles', 'info'); }, 2800);
  }
}

function renderPuzzles() {
  const cont = anEl('anPuzzles');
  cont.innerHTML = '';
  anEl('anDescargarPuzzles').style.display = puzzles.length ? '' : 'none';
  anEl('anOrdenBox').style.display = puzzles.length ? '' : 'none';
  puzzles.forEach((pz) => {
    const caja = document.createElement('div'); caja.className = 'pz';
    const nom = document.createElement('div'); nom.className = 'pz-nombre'; nom.textContent = pz.nombre;
    const inf = document.createElement('div'); inf.className = 'an-nota';
    inf.textContent = 'Juegan ' + (pz.turno === 'w' ? 'blancas' : 'negras') + ', ' + pz.solucion.length +
      (pz.solucion.length === 1 ? ' jugada' : ' jugadas');
    const fila = document.createElement('div'); fila.className = 'fila';
    const mk = (txt, fn) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'btn btn-secondary'; b.textContent = txt; b.addEventListener('click', fn); fila.appendChild(b); };
    mk('Resolver', () => anIniciarSesion(pz));
    mk('PGN', () => descargar(nombreArchivo(pz.nombre) + '.pgn', pgnDe(pz.fen, pz.solucion, { Event: pz.nombre }), 'application/x-chess-pgn'));
    mk('Borrar', () => {
      if (puzzleActivo && puzzleActivo.id === pz.id) { puzzleActivo = null; colaPuzzles = []; }
      colaPuzzles = colaPuzzles.filter(id => id !== pz.id);
      puzzles = puzzles.filter(x => x.id !== pz.id); guardarPuzzles(); renderPuzzles();
    });
    // Botón Clasificar Elo
    const yaClasificado = pz.jugadas &&
      Array.from({length: Math.ceil(pz.solucion.length/2)}, (_,i) => i*2)
           .every(i => pz.jugadas[i] && pz.jugadas[i].analizado);
    const btnElo = document.createElement('button');
    btnElo.type = 'button';
    btnElo.className = 'btn btn-secondary';
    btnElo.textContent = yaClasificado ? '✓ Clasificado' : 'Clasificar Elo';
    btnElo.disabled = yaClasificado;
    fila.appendChild(btnElo);
    // Barra de progreso de clasificación
    const barraElo = document.createElement('div');
    barraElo.className = 'pz-elo-barra';
    barraElo.style.cssText = 'display:none;font-size:0.85em;color:var(--texto2,#888);margin-top:4px';
    if (!yaClasificado) {
      btnElo.addEventListener('click', () => {
        if (!sfEngine) { alert('Carga el motor primero.'); return; }
        btnElo.disabled = true;
        anClasificarElo(pz, btnElo, barraElo);
      });
    }
    caja.appendChild(nom); caja.appendChild(inf);
    if (pz.mejorTiempo != null) {
      const tie = document.createElement('div'); tie.className = 'pz-tiempo';
      tie.textContent = 'Mejor tiempo: ' + formatoMmSs(pz.mejorTiempo);
      caja.appendChild(tie);
    }
    caja.appendChild(fila);
    caja.appendChild(barraElo);
    cont.appendChild(caja);
  });
}

// Arranca el modo "resolver": el usuario juega su bando, el programa
// contesta automáticamente con las jugadas del oponente guardadas en el
// puzzle, hasta agotar toda la solución.
function anResolverPuzzle(pz) {
  anGuardar();
  an = { inicio: pz.fen, movs: [], idx: 0, ini: null, fin: null };
  puzzleActivo = pz;
  anCronArrancar();
  anIr(0);
  anMsg('info', 'Puzzle "' + pz.nombre + '": te tocan ' + (pz.turno === 'w' ? 'blancas' : 'negras') +
    '. Encuentra ' + (pz.solucion.length === 1 ? 'la jugada.' : 'las jugadas (' + pz.solucion.length + ' en total).'));
}

// Tras una jugada correcta del usuario, si quedan jugadas en la solución
// le toca al oponente: el programa la juega solo. Se repite hasta agotar
// pz.solucion, sea cual sea su longitud (varias rondas usuario/oponente).
function anPuzzleContinuar() {
  const pz = puzzleActivo;
  if (!pz) return;
  if (an.movs.length >= pz.solucion.length) { anPuzzleResuelto(pz); return; }
  setTimeout(() => {
    if (puzzleActivo !== pz) return;   // el usuario cambió de puzzle mientras tanto
    const uci = pz.uci[an.movs.length];
    const mv = anChess.move({ from: uci.slice(0, 2), to: uci.slice(2, 4), promotion: uci[4] || 'q' });
    if (!mv) {
      anMsg('error', 'No pude reproducir la jugada del oponente guardada en el puzzle.');
      anCronDetener();
      puzzleActivo = null;
      anActualizarBarraPuzzle();
      return;
    }
    an.movs.push(mv.san);
    anUlt = { from: mv.from, to: mv.to };
    an.idx = an.movs.length;
    anSfLinesLimpiar();
    anActualizarTurno();
    anActualizar();
    if (an.movs.length >= pz.solucion.length) {
      anPuzzleResuelto(pz);
    } else {
      anRenderPzStats();
      anMsg('info', 'Bien. Te toca de nuevo.');
    }
  }, 500);
}

// ── ANÁLISIS: interacción con el tablero ──────────────
let anSeleccionada = null;
let anAnalAndo = false;   // SF analizando en modo análisis
let anBestLines = [];     // líneas recibidas del motor durante el análisis
let anTurnoBusqueda = 'w';    // turno ('w'/'b') de la posición que el motor está buscando AHORA
let anBusquedaEnCurso = false; // true entre 'go infinite' y el 'bestmove' que lo cierra
let anEsperandoParada = false; // se pidió 'stop' y estamos esperando el bestmove que lo confirma
let anProximaFen = null;       // fen en cola para lanzar en cuanto se confirme la parada anterior

function anActualizarTurno() {
  const wrap = anEl('anTurnoWrap');
  if (!an.movs.length && an.idx === 0 && an.inicio === FEN_INICIAL) { wrap.style.display = 'none'; return; }
  wrap.style.display = 'flex';
  const t = anChess.turn();
  anEl('anTurnoFicha').className = 'an-turno-ficha ' + (t === 'w' ? 'blancas' : 'negras');
  anEl('anTurnoLabel').textContent = 'Turno: ' + (t === 'w' ? 'Blancas' : 'Negras');
  anEl('anDeshacer').disabled = an.idx === 0;
}

// ── Editor manual de posición: agregar/quitar piezas, vaciar, posición inicial ──
let anEditandoPos = false;
let anEditHerramienta = { tipo: 'p', color: 'w' };  // o el string 'borrar'
let anEditTurno = 'w';
let anEditFenAntes = null;

function anConstruirPaleta() {
  const tipos = [['k','Rey'],['q','Dama'],['r','Torre'],['b','Alfil'],['n','Caballo'],['p','Peón']];
  const contB = anEl('anPaletaBlancas'), contN = anEl('anPaletaNegras');
  function botonPieza(tipo, color, nombre) {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'btn btn-secondary pieza-btn';
    b.textContent = PIEZAS[color + tipo.toUpperCase()];
    b.title = nombre + ' ' + (color === 'w' ? 'blanco' : 'negro');
    b.dataset.tipo = tipo; b.dataset.color = color;
    b.addEventListener('click', () => anEditFijarHerramienta({ tipo, color }));
    return b;
  }
  tipos.forEach(([tipo, nombre]) => contB.appendChild(botonPieza(tipo, 'w', nombre)));
  tipos.forEach(([tipo, nombre]) => contN.appendChild(botonPieza(tipo, 'b', nombre)));
  const borrar = document.createElement('button');
  borrar.type = 'button'; borrar.className = 'btn btn-secondary pieza-btn';
  borrar.textContent = '🗑'; borrar.title = 'Borrar pieza';
  borrar.dataset.borrar = '1';
  borrar.addEventListener('click', () => anEditFijarHerramienta('borrar'));
  contN.appendChild(borrar);
}
anConstruirPaleta();

function anEditFijarHerramienta(h) {
  anEditHerramienta = h;
  document.querySelectorAll('.pieza-btn').forEach(b => {
    b.classList.toggle('activa', h === 'borrar' ? b.dataset.borrar === '1' : (b.dataset.tipo === h.tipo && b.dataset.color === h.color));
  });
}

function anActualizarBotonesTurnoEdicion() {
  anEl('anEditTurnoBlancas').classList.toggle('btn-primary', anEditTurno === 'w');
  anEl('anEditTurnoBlancas').classList.toggle('btn-secondary', anEditTurno !== 'w');
  anEl('anEditTurnoNegras').classList.toggle('btn-primary', anEditTurno === 'b');
  anEl('anEditTurnoNegras').classList.toggle('btn-secondary', anEditTurno !== 'b');
}
function anEditFijarTurno(t) { anEditTurno = t; anActualizarBotonesTurnoEdicion(); }

function anBloquearOtrosPaneles(bloquear) {
  ['anPanelSF', 'anPanelPartida'].forEach(id => {
    const el = anEl(id);
    el.style.opacity = bloquear ? '0.45' : '';
    el.style.pointerEvents = bloquear ? 'none' : '';
  });
}

function anEntrarEdicion() {
  if (anAnalAndo) anDetenerSF();
  if (puzzleActivo) anDetenerPuzzle();
  anEditandoPos = true;
  anEditFenAntes = anChess.fen();
  anEditTurno = anEditFenAntes.split(' ')[1] === 'b' ? 'b' : 'w';
  anSeleccionada = null;
  anEl('anEditarPosBtn').textContent = 'Editando…';
  anEl('anEditarPosBtn').disabled = true;
  anEl('anEditPosPanel').style.display = 'block';
  anBloquearOtrosPaneles(true);
  anEditFijarHerramienta({ tipo: 'p', color: 'w' });
  anActualizarBotonesTurnoEdicion();
  renderBoard();
}

function anSalirEdicion(restaurar) {
  if (restaurar && anEditFenAntes) anChess.load(anEditFenAntes);
  anEditandoPos = false;
  anEl('anEditarPosBtn').textContent = 'Editar posición';
  anEl('anEditarPosBtn').disabled = false;
  anEl('anEditPosPanel').style.display = 'none';
  anBloquearOtrosPaneles(false);
  document.querySelectorAll('.pieza-btn').forEach(b => b.classList.remove('activa'));
}

function anEditClicTablero(sq) {
  if (anEditHerramienta === 'borrar') {
    anChess.remove(sq);
  } else {
    anChess.remove(sq);   // limpiar primero, por si ya había otra pieza ahí
    const ok = anChess.put({ type: anEditHerramienta.tipo, color: anEditHerramienta.color }, sq);
    if (!ok) anMsg('error', 'Ya hay un rey ' + (anEditHerramienta.color === 'w' ? 'blanco' : 'negro') + ' en el tablero; quítalo primero.');
  }
  renderBoard();
}

function anEditPosicionInicial() {
  anChess.reset();
  anEditTurno = 'w';
  anActualizarBotonesTurnoEdicion();
  renderBoard();
}
function anEditVaciarTablero() {
  anChess.clear();
  anEditTurno = 'w';
  anActualizarBotonesTurnoEdicion();
  renderBoard();
}

function anAplicarEdicionPos() {
  const partes = anChess.fen().split(' ');
  partes[1] = anEditTurno;
  partes[2] = '-'; partes[3] = '-'; partes[4] = '0'; partes[5] = '1';
  const fenFinal = partes.join(' ');
  const prueba = new Chess();
  if (!prueba.load(fenFinal)) { anMsg('error', 'Posición inválida.'); return; }
  let reyesB = 0, reyesN = 0;
  prueba.board().forEach(fila => fila.forEach(cas => {
    if (cas && cas.type === 'k') { if (cas.color === 'w') reyesB++; else reyesN++; }
  }));
  if (reyesB !== 1 || reyesN !== 1) { anMsg('error', 'La posición debe tener exactamente un rey blanco y uno negro.'); return; }
  anSalirEdicion(false);
  anGuardar();
  puzzleActivo = null; colaPuzzles = [];
  an = { inicio: fenFinal, movs: [], idx: 0, ini: null, fin: null };
  anIr(0);
  anMsg('ok', 'Posición aplicada.');
}

function anClicTablero(sq) {
  if (anChess.game_over()) return;
  if (puzzleActivo) {
    if (an.idx !== an.movs.length) { anMsg('info', 'Vuelve a la posición actual del puzzle (») para seguir jugando.'); return; }
    if (an.movs.length % 2 !== 0) return;   // le toca al oponente: la juega el programa solo
  }
  const pieza = anChess.get(sq);
  if (!anSeleccionada) {
    if (pieza) { anSeleccionada = sq; renderBoard(); }
    return;
  }
  // Intento de promoción: siempre reina por ahora
  const mov = anChess.move({ from: anSeleccionada, to: sq, promotion: 'q' });
  anSeleccionada = null;
  if (mov) {
    if (puzzleActivo) {
      const esperada = puzzleActivo.solucion[an.movs.length];
      if (mov.san !== esperada) {
        anChess.undo();
        renderBoard();
        anPuzzleFallo();
        anMsg('error', 'Esa no es la jugada del puzzle. Intenta otra.');
        return;
      }
    }
    // Si estamos en medio de la lista, descartamos las jugadas siguientes y añadimos la nueva
    anGuardar();
    an.movs = an.movs.slice(0, an.idx);
    an.movs.push(mov.san);
    if (an.ini !== null && an.ini >= an.movs.length) an.ini = null;
    if (an.fin !== null && an.fin > an.movs.length) an.fin = null;
    anUlt = { from: mov.from, to: mov.to };
    an.idx = an.movs.length;
    anSfLinesLimpiar();
    anActualizarTurno();
    anActualizar();
    // Si SF estaba analizando o auto-análisis activo, reiniciar para la nueva posición
    if ((anAnalAndo || anAutoAnalizar()) && sfEngine) {
      anArrancarSF();
    }
    if (puzzleActivo) anPuzzleContinuar();
  } else {
    // Clic en otra pieza propia: redirigir selección
    if (pieza) { anSeleccionada = sq; }
    renderBoard();
  }
}

// ── ANÁLISIS SF: mostrar líneas en vivo ──────────────
function anSfLinesLimpiar() {
  anBestLines = [];
  anEl('anSfLines').innerHTML = '<div class="sf-line-vacia">El motor no ha analizado esta posición.</div>';
}

function anSfRenderLineas(lineas, enVivo) {
  const cont = anEl('anSfLines');
  if (!lineas.length) {
    cont.innerHTML = enVivo
      ? '<div class="sf-line-vacia">Calculando…</div>'
      : '<div class="sf-line-vacia">El motor no ha analizado esta posición.</div>';
    return;
  }
  // Ordenar por multipv
  const sorted = [...lineas].sort((a, b) => a.pv - b.pv);
  cont.innerHTML = '';
  const fenBase = anChess.fen();
  const fenParts = fenBase.split(' ');
  // Turno de la posición para la que se calcularon estas líneas: el motor las
  // etiqueta como "anTurnoBusqueda" en el momento en que se lanzó ESA búsqueda,
  // no el turno actual de anChess (que puede haber avanzado si llegan mensajes
  // tardíos de una búsqueda anterior ya detenida). Evita confundir el signo.
  const turnoBase = anTurnoBusqueda;
  const numBase   = parseInt(fenParts[5]) || 1;
  sorted.forEach(l => {
    const div = document.createElement('div'); div.className = 'sf-line';
    const sc = document.createElement('span');
    let scoreTexto, scoreClase;
    if (Math.abs(l.score) >= 90) {
      const vbMate = turnoBase === 'w' ? l.score : -l.score;
      const mn = 100 - Math.abs(vbMate);
      scoreTexto = (vbMate > 0 ? '+M' : '-M') + mn;
      scoreClase = 'sf-line-score mate';
    } else {
      // score viene desde perspectiva del que mueve; convertir a blancas
      const vb = turnoBase === 'w' ? l.score : -l.score;
      scoreTexto = (vb >= 0 ? '+' : '') + vb.toFixed(2);
      scoreClase = 'sf-line-score' + (vb < 0 ? ' neg' : '');
    }
    sc.className = scoreClase; sc.textContent = scoreTexto;
    div.appendChild(sc);
    // Convertir UCI moves a SAN con numeración de jugadas
    const ms = document.createElement('span'); ms.className = 'sf-line-movs';
    const tmpC = new Chess(fenBase);
    let turno = turnoBase, numJug = numBase, primero = true;
    (l.moves || []).slice(0, 8).forEach(uci => {
      const m = tmpC.move({ from: uci.slice(0,2), to: uci.slice(2,4), promotion: uci[4] || 'q' });
      if (!m) return;
      if (ms.childNodes.length) ms.appendChild(document.createTextNode(' '));
      if (turno === 'w') {
        const num = document.createElement('span'); num.className = 'sf-line-num'; num.textContent = numJug + '.';
        ms.appendChild(num);
        ms.appendChild(document.createTextNode(' '));
      } else if (primero) {
        const num = document.createElement('span'); num.className = 'sf-line-num'; num.textContent = numJug + '…';
        ms.appendChild(num);
        ms.appendChild(document.createTextNode(' '));
        numJug++;
      } else {
        numJug++;
      }
      const san = document.createElement('span'); san.className = 'sf-line-san'; san.textContent = m.san;
      ms.appendChild(san);
      primero = false;
      turno = turno === 'w' ? 'b' : 'w';
    });
    if (!ms.childNodes.length) ms.textContent = (l.moves && l.moves[0]) || '';
    div.appendChild(ms);
    // Hacer la línea clicable: aplica toda la variante como jugadas nuevas
    div.style.cursor = 'pointer';
    div.title = 'Clic para aplicar esta variante al tablero';
    div.addEventListener('click', () => {
      const uciMoves = l.moves || [];
      if (!uciMoves.length) return;
      const tmpApply = new Chess(anChess.fen());
      const aplicadas = [];
      for (const uci of uciMoves) {
        const mv = tmpApply.move({ from: uci.slice(0,2), to: uci.slice(2,4), promotion: uci[4] || 'q' });
        if (!mv) break;
        aplicadas.push(mv.san);
      }
      if (!aplicadas.length) return;
      anGuardar();
      const nuevosMovs = an.movs.slice(0, an.idx).concat(aplicadas);
      an.movs = nuevosMovs;
      an.ini = null; an.fin = null;
      anDetenerSF();
      anIr(an.movs.length);
      anMsg('info', 'Variante aplicada: ' + aplicadas.join(' '));
    });
    cont.appendChild(div);
  });
}

function anAutoAnalizar() {
  return anEl('anAutoAnalizar') && anEl('anAutoAnalizar').checked && !!sfEngine && !anChess.game_over();
}

// Lanza la búsqueda del motor para `fen` de verdad (solo se llama cuando no
// queda ninguna búsqueda anterior pendiente de confirmar su parada).
function anLanzarBusquedaMotor(fen) {
  anBestLines = [];
  anSfRenderLineas([], true);
  anTurnoBusqueda = fen.split(' ')[1] === 'b' ? 'b' : 'w';
  anBusquedaEnCurso = true;
  const k = Math.max(1, Math.min(leerNumero('numJugadas', 5, 1, 30, true), 10));
  sfEngine.postMessage('setoption name MultiPV value ' + k);
  sfEngine.postMessage('position fen ' + fen);
  sfEngine.postMessage('go infinite');
}

// Pide analizar la posición actual. Si el motor ya está buscando otra (p.ej.
// se navegó a otra jugada), se le pide 'stop' y la nueva búsqueda queda en
// cola: NO se lanza hasta recibir el 'bestmove' que confirma que el motor
// terminó de verdad con la anterior. Así ninguna línea "tardía" de la
// posición vieja puede mezclarse con las de la nueva (y su turno/signo).
function anArrancarSF() {
  if (!sfEngine || anChess.game_over()) return;
  const fen = anChess.fen();
  anAnalAndo = true;
  anEl('anAnalBtn').textContent = 'Detener'; anEl('anAnalBtn').classList.add('stop');
  anProximaFen = fen;
  if (anBusquedaEnCurso) {
    if (!anEsperandoParada) { sfEngine.postMessage('stop'); anEsperandoParada = true; }
    anSfRenderLineas([], true);
    return;   // anLanzarBusquedaMotor(anProximaFen) se llama al llegar el bestmove
  }
  anLanzarBusquedaMotor(fen);
}

function anDetenerSF() {
  if (!sfEngine) return;
  anAnalAndo = false;
  anProximaFen = null;
  if (anBusquedaEnCurso && !anEsperandoParada) { sfEngine.postMessage('stop'); anEsperandoParada = true; }
  anEl('anAnalBtn').textContent = 'Analizar'; anEl('anAnalBtn').classList.remove('stop');
}

function anIniciarAnalisis() {
  if (!sfEngine) { anMsg('error', 'Motor no cargado.'); return; }
  if (anAnalAndo) { anDetenerSF(); return; }
  anArrancarSF();
}

// Interceptar mensajes SF para análisis en modo análisis
const _onSFMessageOrig = typeof onSFMessage !== 'undefined' ? onSFMessage : null;
function onSFMessageAn(ev) {
  const data = ev.data;
  if (typeof data !== 'string') return false;
  // Mientras esperamos el bestmove que confirma una parada, TODO lo que llegue
  // (info o bestmove intermedios) pertenece a la búsqueda vieja: se descarta
  // sin tocar anBestLines/anTurnoBusqueda de la búsqueda nueva.
  if (data.startsWith('bestmove')) {
    anBusquedaEnCurso = false;
    if (anEsperandoParada) {
      anEsperandoParada = false;
      if (anAnalAndo && anProximaFen != null) { anLanzarBusquedaMotor(anProximaFen); }
      return true;
    }
    if (anAnalAndo) anSfRenderLineas(anBestLines, false);
    return true;
  }
  if (anEsperandoParada || !anAnalAndo) return anAnalAndo || anEsperandoParada;
  if (data.startsWith('info') && data.includes(' pv ')) {
    if (data.includes(' lowerbound') || data.includes(' upperbound')) return true;
    const pvM = data.match(/\bpv\s+(\S+(?:\s+\S+)*)/);
    const scM = data.match(/\bscore (cp|mate) (-?\d+)/);
    const pvN = data.match(/\bmultipv (\d+)/);
    if (!pvM || !scM) return true;
    const pv = pvN ? parseInt(pvN[1]) : 1;
    let score = parseInt(scM[2]);
    if (scM[1] === 'cp') score = score / 100;
    else score = score > 0 ? (100 - score) : -(100 + score);
    const moves = pvM[1].trim().split(/\s+/);
    const idx = anBestLines.findIndex(l => l.pv === pv);
    if (idx >= 0) anBestLines[idx] = { pv, score, moves };
    else anBestLines.push({ pv, score, moves });
    anSfRenderLineas(anBestLines, true);
    return true;
  }
  return false;
}

// ── Pestañas y eventos ────────────────────────────────
function mostrarPestana(cual) {
  // Detener análisis SF si se cambia de pestaña
  if (anAnalAndo && cual !== 'analisis') anDetenerSF();
  if (anEditandoPos && cual !== 'analisis') anSalirEdicion(true);
  modoAnalisis = cual === 'analisis';
  seleccionada = null; anSeleccionada = null;
  anEl('panelJugar').style.display = modoAnalisis ? 'none' : '';
  anEl('panelAnalisis').style.display = modoAnalisis ? '' : 'none';
  const anBajo = anEl('anBajo');
  anBajo.style.display = modoAnalisis ? 'flex' : 'none';
  anEl('tabJugar').classList.toggle('act', !modoAnalisis);
  anEl('tabAnalisis').classList.toggle('act', modoAnalisis);
  anEl('tabJugar').setAttribute('aria-selected', String(!modoAnalisis));
  anEl('tabAnalisis').setAttribute('aria-selected', String(modoAnalisis));
  if (modoAnalisis) {
    anEl('anAnalBtn').disabled = !sfEngine;
    anActualizar();
    anActualizarTurno();
  } else { renderBoard(); actualizarTurno(); }
}

anEl('tabJugar').addEventListener('click', () => mostrarPestana('jugar'));
anEl('tabAnalisis').addEventListener('click', () => mostrarPestana('analisis'));
anEl('anAnalBtn').addEventListener('click', anIniciarAnalisis);
anEl('anEditarPosBtn').addEventListener('click', anEntrarEdicion);
anEl('anEditAplicar').addEventListener('click', anAplicarEdicionPos);
anEl('anEditCancelar').addEventListener('click', () => { anSalirEdicion(true); anActualizarTurno(); anActualizar(); });
anEl('anEditInicial').addEventListener('click', anEditPosicionInicial);
anEl('anEditVaciar').addEventListener('click', anEditVaciarTablero);
anEl('anEditTurnoBlancas').addEventListener('click', () => anEditFijarTurno('w'));
anEl('anEditTurnoNegras').addEventListener('click', () => anEditFijarTurno('b'));
anEl('anDeshacer').addEventListener('click', () => {
  if (an.idx === 0) return;
  anGuardar();
  an.movs = an.movs.slice(0, an.idx - 1);
  anSfLinesLimpiar();
  anIr(an.movs.length);
});
anEl('anAutoAnalizar').addEventListener('change', () => {
  if (anEl('anAutoAnalizar').checked && modoAnalisis && !anAnalAndo) {
    if (sfEngine && !anChess.game_over()) anArrancarSF();
  } else if (!anEl('anAutoAnalizar').checked && anAnalAndo) {
    anDetenerSF();
  }
});
anEl('anCargarTexto').addEventListener('click', () => {
  const el = anEl('anEditor');
  const t = el ? el.textContent : '';
  if (!t.trim()) { anMsg('info', 'Escribe o pega primero el texto del PGN.'); return; }
  anCargarTexto(t);
});
anEl('anFilePgn').addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const r = new FileReader();
  r.onload = () => {
    const el = anEl('anEditor');
    if (el) el.textContent = r.result;
    anCargarTexto(r.result);
  };
  r.onerror = () => anMsg('error', 'No se pudo leer el archivo.');
  r.readAsText(f);
  e.target.value = '';
});
anEl('anUsarActual').addEventListener('click', anUsarActual);

// ── Edición en vivo dentro de la caja ──────────────────────────────────
// Es una caja "contenteditable" normal (nada de librerías externas: funciona
// sin internet igual que el resto de la app). Mientras el usuario escribe,
// se interpretan las jugadas y se mueve el tablero en cuanto deja de teclear
// un instante; al salir de la caja se repinta con el resaltado de la jugada
// activa (mientras se edita no se repinta el contenido para no pisarle el
// cursor al usuario).
(function () {
  const el = anEl('anEditor');
  if (!el) return;
  let temporizador = null;

  el.addEventListener('focus', () => { anGuardar(); }); // 1 solo punto de deshacer por sesión de edición

  el.addEventListener('input', () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(anAplicarEdicionViva, 350);
  });

  el.addEventListener('blur', () => {
    clearTimeout(temporizador);
    anAplicarEdicionViva();
    anRenderEditor(); // ya no está en foco: repinta con el resaltado
  });

  // Pegar siempre como texto plano (nada de formato/HTML pegado).
  el.addEventListener('paste', (e) => {
    e.preventDefault();
    const texto = (e.clipboardData || window.clipboardData).getData('text/plain');
    document.execCommand('insertText', false, texto);
  });

  // Enter inserta un espacio en vez de crear <div>/<br> (mantiene todo en
  // un único bloque de texto, mucho más simple de parsear e igual de legible
  // porque el CSS ya envuelve las líneas largas).
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.execCommand('insertText', false, ' ');
    }
  });
})();
anEl('anInicio').addEventListener('click', () => anIr(0));
anEl('anAnt').addEventListener('click', () => anIr(an.idx - 1));
anEl('anSig').addEventListener('click', () => anIr(an.idx + 1));
anEl('anFinal').addEventListener('click', () => anIr(an.movs.length));
anEl('anGirar').addEventListener('click', () => { anFlipped = !anFlipped; renderCoords(); renderBoard(); });
anEl('anCortar').addEventListener('click', anCortar);
anEl('anBorrar').addEventListener('click', anBorrar);
anEl('anDeshacerEd').addEventListener('click', anDeshacerEd);
anEl('anDescargar').addEventListener('click', () => descargar('analisis.pgn', pgnDe(an.inicio, an.movs, { Event: 'Analisis' }), 'application/x-chess-pgn'));
anEl('anMarcaIni').addEventListener('click', () => anMarcar('ini'));
anEl('anMarcaFin').addEventListener('click', () => anMarcar('fin'));
anEl('anQuitarMarcas').addEventListener('click', () => { an.ini = an.fin = null; anActualizar(); });
anEl('anCrearPuzzle').addEventListener('click', anCrearPuzzle);
anEl('anResolverTodos').addEventListener('click', () => anIniciarSesion(null));
anEl('anDetenerPuzzle').addEventListener('click', anDetenerPuzzle);
anEl('anDescargarPuzzles').addEventListener('click', () => descargar('puzzles.json', JSON.stringify(puzzles, null, 2), 'application/json'));
document.addEventListener('keydown', (e) => {
  if (!modoAnalisis) return;
  const tag = e.target.tagName;
  if (tag === 'TEXTAREA' || tag === 'INPUT') return;
  if (e.key === 'ArrowLeft') { anIr(an.idx - 1); e.preventDefault(); }
  else if (e.key === 'ArrowRight') { anIr(an.idx + 1); e.preventDefault(); }
  else if (e.key === 'Home') { anIr(0); e.preventDefault(); }
  else if (e.key === 'End') { anIr(an.movs.length); e.preventDefault(); }
});
cargarPuzzles(); cargarElo(); anRenderPzStats(); renderPuzzles();
anEl('anResetElo').addEventListener('click', () => {
  if (!confirm('¿Restablecer Elo a 1200 y borrar historial?')) return;
  eloJugador = 1200; pzAciertos = 0; pzFallos = 0;
  guardarElo(); guardarEloHistorial([]);
  anRenderPzStats();
});

// ── BANDO DEL JUGADOR ──────────────────────────────────
function cambiarBando(nuevo) {
  if (bandoJugador === nuevo) return;
  bandoJugador = nuevo;
  actualizarBandoUI();
  // Arrancar nueva partida con el bando elegido
  chess = new Chess(); seleccionada = null; moviendoSF = false; historial = []; bestLines = [];
  clearInterval(timerInterval);
  document.getElementById('timerBar').style.width = '0%';
  if (sfEngine) {
    esperandoBest = false;
    clearTimeout(temporizadorSeguridad); clearTimeout(temporizadorStop);
    sfEngine.postMessage('stop'); sfEngine.postMessage('ucinewgame'); sfEngine.postMessage('isready');
  }
  actualizarHistorial(); renderCoords(); renderBoard(); actualizarTurno();
  document.getElementById('lastMove').textContent = '—';
  document.getElementById('scoreBadge').textContent = '';
  if (bandoJugador === 'b') {
    setStatus('think', 'Nueva partida con negras. Stockfish empieza…');
    setTimeout(pedirJugadaSF, 400);
  } else {
    setStatus('idle', 'Nueva partida con blancas. Tu turno.');
  }
}
document.getElementById('btnBandoBlancas').addEventListener('click', () => cambiarBando('w'));
document.getElementById('btnBandoNegras').addEventListener('click', () => cambiarBando('b'));

// El editor de PGN (#anEditor) es una caja "contenteditable" normal: no
// depende de ninguna librería ni de internet. Su lógica de resaltado y
// edición en vivo está junto a las demás funciones de análisis, arriba.
</script>
</body>
</html>
"""


class Manejador(BaseHTTPRequestHandler):
    def _responder(self, codigo, tipo, cuerpo, con_cuerpo=True):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if con_cuerpo:
            self.wfile.write(cuerpo)

    def _atender(self, con_cuerpo):
        ruta = self.path.split("?")[0].split("#")[0]
        if ruta in ("/", "/index.html"):
            self._responder(200, "text/html; charset=utf-8", HTML.encode("utf-8"), con_cuerpo)
        elif ruta == "/manifest.json":
            self._responder(200, "application/manifest+json; charset=utf-8", MANIFEST.encode("utf-8"), con_cuerpo)
        elif ruta == "/icon.png":
            self._responder(200, "image/png", base64.b64decode(ICON_PNG_B64), con_cuerpo)
        elif ruta == "/favicon.ico":
            self._responder(204, "image/x-icon", b"", con_cuerpo)
        else:
            self._responder(404, "text/plain; charset=utf-8", b"No encontrado", con_cuerpo)

    def do_GET(self):
        self._atender(True)

    def do_HEAD(self):
        self._atender(False)

    def log_message(self, *args):
        pass  # sin ruido en la consola


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO_FIJO
    puerto_pedido = puerto
    servidor = None
    for p in range(puerto, puerto + 20):
        try:
            servidor = ThreadingHTTPServer(("127.0.0.1", p), Manejador)
            puerto = p
            break
        except OSError:
            continue
    if servidor is None:
        print("No se pudo abrir ningún puerto libre.")
        return
    url = "http://localhost:%d" % puerto
    print("Ajedrez · Stockfish 19")
    print("Abre en el navegador:  " + url)
    if puerto != puerto_pedido:
        print("AVISO: el puerto %d estaba ocupado, se usó %d en su lugar." % (puerto_pedido, puerto))
        print("       Si tienes un icono instalado apuntando a localhost:%d," % puerto_pedido)
        print("       cierra el otro proceso y reinicia, o reinstala el icono en :%d." % puerto)
    print("(Ctrl+C para cerrar)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")


if __name__ == "__main__":
    main()


# ── AÑADIR AL FINAL DE ajedrez_servidor.py ──

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class MiManejador(BaseHTTPRequestHandler):
    """Servidor HTTP que inyecta las cabeceras COOP/COEP para SharedArrayBuffer"""
    def do_GET(self):
        if self.path == '/icon.png':
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(base64.b64decode(ICON_PNG_B64))
        elif self.path == '/manifest.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(MANIFEST.encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            # CABECERAS REQUERIDAS POR STOCKFISH WASM
            self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
            self.send_header('Cross-Origin-Embedder-Policy', 'credentialless')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))

def iniciar_servidor_android():
    """Función llamada desde Java (Chaquopy) para arrancar el servidor"""
    servidor = ThreadingHTTPServer(('localhost', PUERTO_FIJO), MiManejador)
    print(f"Servidor corriendo en http://localhost:{PUERTO_FIJO}")
    servidor.serve_forever()
