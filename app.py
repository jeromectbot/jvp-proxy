from flask import Flask, request, jsonify, Response
import os
import base64
from openai import OpenAI

app = Flask(__name__)

# OpenAI key doit être dans les variables d'environnement Render
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Page d'accueil "jolie" sur /
@app.get("/")
def home():
    html = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Jardin Vision Proxy</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;background:#0b0f14;color:#e8eef7;margin:0}
    .wrap{max-width:820px;margin:0 auto;padding:28px}
    .card{background:#111826;border:1px solid #1f2a3a;border-radius:16px;padding:18px;margin-top:14px}
    h1{margin:0 0 6px 0;font-size:26px}
    .muted{opacity:.8}
    code,pre{background:#0b1220;border:1px solid #1f2a3a;border-radius:12px;padding:10px;display:block;overflow:auto}
    a{color:#86b7ff}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>🌿 Jardin Vision Proxy</h1>
    <div class="muted">Service OK. Endpoints disponibles :</div>

    <div class="card">
      <b>GET /health</b>
      <pre>{"ok": true}</pre>
    </div>

    <div class="card">
      <b>POST /analyze</b> (texte)
      <pre>{
  "prompt": "Ma plante a des feuilles jaunes, que faire ?"
}</pre>
    </div>

    <div class="card">
      <b>POST /analyze-image</b> (image base64 + prompt)
      <pre>{
  "image_base64": "(base64 jpeg sans prefix)",
  "prompt": "Analyse cette plante…"
}</pre>
    </div>

    <div class="card">
      <div class="muted">Astuce : ouvre <a href="/health">/health</a> pour vérifier rapidement.</div>
    </div>
  </div>
</body>
</html>
"""
    return Response(html, mimetype="text/html")


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "jardin-vision-proxy"})


# ✅ Analyse texte (ton endpoint actuel)
@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    r = client.responses.create(
        model="gpt-4o-mini",
        input=[{
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}]
        }]
    )
    return jsonify({"result": (r.output_text or "").strip()})


# ✅ Analyse image (CELUI QUI MANQUE → corrige ton 404 Android)
@app.post("/analyze-image")
def analyze_image():
    data = request.get_json(silent=True) or {}
    img_b64 = (data.get("image_base64") or "").strip()
    prompt = (data.get("prompt") or "").strip()

    if not img_b64 or not prompt:
        return jsonify({"error": "Missing image_base64 or prompt"}), 400

    # On accepte base64 nu, ou data URL si jamais
    if img_b64.startswith("data:image"):
        data_url = img_b64
    else:
        # mini validation base64
        try:
            base64.b64decode(img_b64, validate=True)
        except Exception:
            return jsonify({"error": "image_base64 is not valid base64"}), 400
        data_url = f"data:image/jpeg;base64,{img_b64}"

    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": data_url, "detail": "low"}
            ]
        }]
    )

    return jsonify({"result": (r.output_text or "").strip()})
