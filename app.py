from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
import requests
import csv
import os

app = Flask(__name__)

# --- CONFIGURACIÓN (Rellena tus datos) ---
EMPRESA = "Nombre de tu Empresa"
TELEGRAM_TOKEN = "TU_TOKEN_AQUI"
TELEGRAM_CHAT_ID = "TU_CHAT_ID_AQUI"

# Sincronizado exactamente con generar_qrs.py ("Admin" y "Recepcion")
MATRIZ_ACCESOS = {
    "Recepcion": ["Admin", "Recepcion"],
    "Sala de Datos": ["Admin"]
}

ARCHIVO_BITACORA = "bitacora_accesos.csv"

if not os.path.exists(ARCHIVO_BITACORA):
    with open(ARCHIVO_BITACORA, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Fecha y Hora", "ID", "Persona", "Rol", "Zona", "Resultado"])

def enviar_alerta_telegram(persona, rol, zona, fecha):
    mensaje = (
        f"🚨 *ALERTA DE SEGURIDAD - {EMPRESA}* 🚨\n\n"
        f"⛔ *Intento de acceso denegado*\n"
        f"👤 *Persona:* {persona}\n"
        f"🏷️ *Rol:* {rol}\n"
        f"📍 *Zona:* {zona}\n"
        f"🕒 *Hora:* {fecha}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }, timeout=5)
    except Exception as e:
        print(f"Error enviando alerta a Telegram: {e}")

HTML_ESCANER = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso QR - {{ empresa }}</title>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0E1117; color: #FAFAFA; text-align: center; padding: 20px; margin: 0; }
        h2 { margin-bottom: 5px; }
        .sub { color: #9CA3AF; font-size: 14px; margin-bottom: 20px; }
        select { padding: 12px; font-size: 16px; border-radius: 8px; background: #1E232F; color: white; border: 1px solid #374151; margin-bottom: 15px; width: 100%; max-width: 400px; }
        #reader { width: 100%; max-width: 400px; margin: 0 auto; border-radius: 12px; overflow: hidden; }
        #resultado { margin-top: 20px; padding: 20px; border-radius: 12px; font-size: 18px; font-weight: bold; display: none; max-width: 400px; margin-left: auto; margin-right: auto; }
        .permitido { background: #14532D; border: 2px solid #22C55E; color: #DCFCE7; }
        .denegado { background: #7F1D1D; border: 2px solid #EF4444; color: #FEE2E2; }
        a { color: #60A5FA; text-decoration: none; font-size: 14px; display: inline-block; margin-top: 20px; }
    </style>
</head>
<body>
    <h2>{{ empresa }}</h2>
    <div class="sub">Control de Acceso QR</div>
    <select id="zona">
        <option value="Recepcion">Zona 1: Recepción</option>
        <option value="Sala de Datos">Zona 2: Sala de Datos (Crítica)</option>
    </select>
    <div id="reader"></div>
    <div id="resultado"></div>
    <a href="/bitacora" target="_blank">Ver Bitácora en vivo →</a>

    <script>
        let bloqueado = false;

        function onScanSuccess(decodedText) {
            if (bloqueado) return;
            bloqueado = true;

            const zona = document.getElementById("zona").value;
            fetch("/validar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ qr: decodedText, zona: zona })
            })
            .then(res => res.json())
            .then(data => {
                const div = document.getElementById("resultado");
                div.style.display = "block";
                div.className = data.acceso ? "permitido" : "denegado";
                div.innerHTML = `${data.acceso ? "✅ ACCESO PERMITIDO" : "⛔ ACCESO DENEGADO"}<br>
                                 <span style="font-size:14px; font-weight:normal;">${data.persona} (${data.rol})</span>`;
                setTimeout(() => { bloqueado = false; }, 3000);
            });
        }

        const scanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        scanner.render(onScanSuccess);
    </script>
</body>
</html>
"""

HTML_BITACORA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3">
    <title>Bitácora - {{ empresa }}</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0E1117; color: #FAFAFA; padding: 30px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #161B22; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #30363D; }
        th { background: #1F2937; color: #9CA3AF; font-size: 13px; text-transform: uppercase; }
        .PERMITIDO { color: #22C55E; font-weight: bold; }
        .DENEGADO { color: #EF4444; font-weight: bold; }
    </style>
</head>
<body>
    <h2>Bitácora de Accesos — {{ empresa }}</h2>
    <table>
        <thead>
            <tr><th>Fecha y Hora</th><th>ID</th><th>Persona</th><th>Rol</th><th>Zona</th><th>Resultado</th></tr>
        </thead>
        <tbody>
            {% for fila in registros %}
            <tr>
                <td>{{ fila[0] }}</td><td>{{ fila[1] }}</td><td>{{ fila[2] }}</td>
                <td>{{ fila[3] }}</td><td>{{ fila[4] }}</td><td class="{{ fila[5] }}">{{ fila[5] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_ESCANER, empresa=EMPRESA)

@app.route("/bitacora")
def bitacora():
    registros = []
    if os.path.exists(ARCHIVO_BITACORA):
        with open(ARCHIVO_BITACORA, "r", encoding="utf-8") as f:
            registros = list(csv.reader(f))[1:]
    registros.reverse()
    return render_template_string(HTML_BITACORA, empresa=EMPRESA, registros=registros)

@app.route("/validar", methods=["POST"])
def validar():
    data = request.json
    qr_texto = data.get("qr", "")
    zona = data.get("zona", "")
    
    partes = qr_texto.split("|")
    if len(partes) == 3:
        uid, persona, rol = [p.strip() for p in partes]
    else:
        uid, persona, rol = "N/A", "QR Inválido", "Desconocido"

    acceso = rol in MATRIZ_ACCESOS.get(zona, [])
    resultado = "PERMITIDO" if acceso else "DENEGADO"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ARCHIVO_BITACORA, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([fecha, uid, persona, rol, zona, resultado])

    if not acceso:
        enviar_alerta_telegram(persona, rol, zona, fecha)

    return jsonify({"acceso": acceso, "persona": persona, "rol": rol, "resultado": resultado})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)