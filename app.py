from datetime import date, datetime, timezone
from flask import Flask, request, jsonify, Response
import os
import base64
import json
import re
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

def _extract_json_object(text: str) -> dict:
    """Récupère le 1er objet JSON trouvé dans un texte (si l'IA ajoute du texte autour)."""
    if not text:
        raise ValueError("empty")
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("no_json")
    return json.loads(m.group(0))
    
def _phase_lune_auto_utc() -> str:
    """
    Retourne 'croissante' ou 'décroissante' (approximation fiable pour usage jardin).
    Basé sur un cycle synodique moyen, sans dépendance externe.
    """
    synodic_month = 29.53058867  # jours
    # Référence nouvelle lune (UTC) : 2000-01-06 18:14
    ref = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    days = (now - ref).total_seconds() / 86400.0
    age = days % synodic_month  # âge de la lune en jours

    # Croissante : de nouvelle lune à pleine lune (~14.765j), décroissante après
    return "croissante" if age < (synodic_month / 2.0) else "décroissante"
    
@app.post("/potager")
def potager():
    data = request.get_json(silent=True)

    # Fallback solide si Flask ne parse pas le JSON
    if not isinstance(data, dict) or not data:
        try:
            raw = request.data.decode("utf-8", errors="ignore").strip()
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}

    region = (data.get("region") or "France").strip()
    mois = (data.get("mois") or "Décembre").strip()

    # phase_lune robuste (accepte plusieurs clés + normalise)
    phase_lune = (
        data.get("phase_lune")
        or data.get("phaseLune")
        or data.get("lune")
        or data.get("phase")
        or ""
    )
    phase_lune = str(phase_lune).strip().lower()

    if not phase_lune:
        phase_lune = _phase_lune_auto_utc()
    if phase_lune in ["croissante", "croissant", "waxing", "waxing_moon"]:
        phase_lune = "croissante"
    elif phase_lune in ["décroissante", "decroissante", "décroissant", "waning", "waning_moon"]:
        phase_lune = "décroissante"
    else:
        phase_lune = ""

    system = (
        "Tu es un jardinier expert du potager en France. "
        "Tu réponds UNIQUEMENT en JSON strict, sans texte autour."
    )

    user = f"""
Région: {region}
Mois (à respecter à l’identique): {mois}
Phase de lune (si fournie): {phase_lune}

Génère un calendrier potager réaliste incluant :
- légumes
- fruits (ex: fraisiers, petits fruits, arbres fruitiers si pertinent)
- aromatiques

Contraintes :
- JSON strict uniquement
- 10 à 20 éléments par liste
- pas de doublons
- si un élément est sous abri / serre, précise-le entre parenthèses

RÈGLE LUNE (STRICTE) :
- Si phase_lune est vide : mets "phase_non_fournie" et NE DONNE PAS de conseils lunaires.
- Si phase_lune est fournie (croissante/décroissante) : donne un court conseil lunaire OPTIONNEL.
- Ne jamais inventer une phase.

Format EXACT:
{{
  "semer": [...],
  "planter": [...],
  "a_eviter": [...],
  "lune": {{
    "phase": "croissante" | "décroissante" | "phase_non_fournie",
    "conseil": "string (court)" | ""
  }}
}}
""".strip()

    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    txt = (r.output_text or "").strip()

    try:
        obj = _extract_json_object(txt)

        semer = (obj.get("semer") or [])[:20]
        planter = (obj.get("planter") or [])[:20]
        a_eviter = (obj.get("a_eviter") or [])[:20]

        lune = obj.get("lune") or {"phase": "phase_non_fournie", "conseil": ""}
        # Force la phase renvoyée si on en a fourni une
        if phase_lune:
            lune["phase"] = phase_lune

        return jsonify({
            "region": region,
            "mois": mois,
            "phase_lune_recue": phase_lune,
            "semer": semer,
            "planter": planter,
            "a_eviter": a_eviter,
            "lune": lune
        })

    except Exception:
        return jsonify({
            "region": region,
            "mois": mois,
            "phase_lune_recue": phase_lune,
            "semer": [],
            "planter": [],
            "a_eviter": [],
            "lune": {"phase": "erreur", "conseil": ""},
            "raw": txt[:800]
        }), 200


