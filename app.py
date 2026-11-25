from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)

# Matriz de accesos: define qué roles pueden entrar a cada zona
MATRIZ_ACCESOS = {
    "Recepcion": ["Admin TI", "Recepcion", "Visitante"],
    "Sala de Datos": ["Admin TI"]
}

ARCHIVO_BITACORA = "bitacora_accesos.csv"

# Inicializar bitácora si no existe
if not os.path.exists(ARCHIVO_BITACORA):
    with open(ARCHIVO_BITACORA, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Fecha y Hora", "ID", "Persona", "Rol", "Zona", "Resultado"])

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control de Acceso QR</title>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0E1117; color: #FAFAFA; text-align: center; padding: 20px; margin: 0; }
        select { padding: 12px; font-size: 16px; border-radius: 8px; background: #1E232F; color: white; border: 1px solid #333; margin-bottom: 15px; width: 100%; max-width: 400px; }
        #reader { width: 100%; max-width: 400px; margin: 0 auto; border-radius: 12px; overflow: hidden; }
        #resultado { margin-top: 20px; padding: 20px; border-radius: 12px; font-size: 18px; font-weight: bold; display: none; max-width: 400px; margin-left: auto; margin-right: auto; }
        .permitido { background: #14532D; border: 2px solid #22C55E; color: #DCFCE7; }
        .denegado { background: #7F1D1D; border: 2px solid #EF4444; color: #FEE2E2; }
    </style>
</head>
<body>
    <h2>Control de Acceso - Centro de Datos</h2>
    <select id="zona">
        <option value="Recepcion">Zona 1: Recepción</option>
        <option value="Sala de Datos">Zona 2: Sala de Datos (Crítica)</option>
    </select>
    <div id="reader"></div>
    <div id="resultado"></div>

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

        const html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

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

    return jsonify({"acceso": acceso, "persona": persona, "rol": rol, "resultado": resultado})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)