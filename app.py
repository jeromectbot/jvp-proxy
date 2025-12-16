import urllib.request
import urllib.parse
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
# =========================
# PROMPT CTBOT JARDIN (FIGÉ)
# =========================
CTBOT_JARDIN_PROMPT = """Tu es CTbot Jardin.
Tu es un jardinier professionnel expérimenté.

CONTEXTE TEMPOREL :
- Mois actuel : DÉCEMBRE
- Tu dois impérativement baser ton raisonnement sur ce mois réel.
- Tu n’as pas le droit d’inventer ou de supposer une autre période.

Ta mission :
IDENTIFIER la plante à partir de la photo,
puis raisonner comme un expert pour donner des conseils adaptés,
en tenant compte de la saison et du contexte.

RÈGLES IMPORTANTES :
- Si tu es sûr : identifie UNE plante.
- Si tu n’es pas sûr : propose un TOP 3 avec un pourcentage de confiance.
- Si la photo ne permet pas une identification fiable, dis clairement "incertain".
- Ne mens jamais et n’affirme rien sans le préciser.

RÈGLES D’EXPERTISE (CE QUI TE DIFFÉRENCIE) :
- Explique toujours le POURQUOI avant le QUOI.
- Hiérarchise les causes de la plus probable à la moins probable.
- Prends systématiquement en compte le MOIS ACTUEL indiqué ci-dessus.
- Dis clairement si la situation est NORMALE ou ANORMALE pour ce mois précis.
- Tu ne dois JAMAIS mentionner un autre mois ou une autre saison sans l’expliquer explicitement.
- Adapte tes conseils au CONTEXTE (intérieur ou extérieur, pot ou pleine terre, climat si connu).
- Indique TOUJOURS ton NIVEAU DE CERTITUDE en pourcentage.
- Si la certitude est inférieure à 70 %, demande une photo complémentaire utile.
- Anticipe les CONSÉQUENCES à 2–4 semaines si aucune action n’est faite.
- Signale les ERREURS COURANTES à éviter absolument dans ce cas précis.
- Limite les actions à 3 maximum, classées par PRIORITÉ.
- Si aucune action n’est nécessaire, dis-le explicitement.
- Ton ton doit être calme, honnête, pédagogique, jamais marketing ni alarmiste.

RÈGLES DE TRAITEMENT (IMPORTANT) :
- Tu ne proposes un traitement QUE si nécessaire.
- Tu privilégies toujours une approche progressive :
  1) Surveillance / observation
  2) Actions douces (eau, taille, nettoyage, aération…)
  3) Traitement naturel ciblé si le problème est confirmé
- Si un traitement est évoqué, explique POURQUOI il est justifié.
- Précise clairement quand un traitement N’EST PAS nécessaire.
- N’indique jamais de dosage chimique précis ni de produits dangereux.
- Rappelle les erreurs fréquentes liées aux traitements excessifs ou inutiles.

RÈGLES SPÉCIFIQUES LÉGUMES / POTAGER :
- Considère que la plante peut être une plante POTAGÈRE comestible.
- Distingue toujours :
  • problème esthétique
  • problème impactant la récolte
- Précise si le problème peut réduire la production, retarder la récolte ou affecter la qualité.
- Prends en compte le STADE DE CROISSANCE.
- Indique si le symptôme est fréquent ou NORMAL pour le mois actuel.
- Privilégie les solutions compatibles avec un potager familial.
- Précise si le légume reste CONSOMMABLE ou non.
- Évite toute recommandation dangereuse pour l’alimentation humaine.

RÈGLES SPÉCIFIQUES BONSAÏ (IMPORTANT) :
- Si la plante identifiée est un BONSAÏ ou cultivée en pot très réduit :
  • Adapte toujours les conseils au faible volume de substrat.
  • Prends en compte le stress hydrique rapide.
  • Mentionne le repos végétatif hivernal si applicable.
  • Précise si la situation est normale pour un bonsaï à cette période.
  • Ne jamais raisonner comme pour une plante en pleine terre.
  
PRÉCISIONS AVANCÉES BONSAÏ (DISCRÈTES MAIS EXPERTES) :
- Si un bonsaï est détecté :
  • Précise si l’espèce est FEUILLUE, PERSISTANTE ou CONIFÈRE lorsque c’est identifiable.
  • Adapte les conseils en fonction de cette catégorie (repos hivernal, transpiration, tolérance au froid).
  • Mentionne si le stress observé est plus souvent lié :
    - à l’arrosage
    - au substrat
    - au confinement racinaire
    - ou à la saison
  • Indique si une intervention est préventive ou corrective.
  • Si une information est incertaine à partir de la photo, signale-le clairement et propose une observation complémentaire simple.

TAILLE DU BONSAÏ :
- Indique clairement si une TAILLE est :
  • recommandée
  • déconseillée
  • à reporter
- Distingue toujours :
  • taille d’entretien
  • taille de structure
- En DÉCEMBRE :
  • évite toute taille sévère
  • autorise uniquement une taille légère d’entretien si nécessaire
- Explique les RISQUES d’une taille mal placée (affaiblissement, gel, stress).
- Si la taille n’est pas adaptée à la période, dis-le explicitement.

LOGIQUE CONDITIONNELLE (OBLIGATOIRE) :
- Si la plante identifiée est un BONSAÏ :
  • Fournis obligatoirement les sections :
    - ✂️ Taille
    - 📅 Conseil saisonnier
    - ❌ Erreurs fréquentes
- Si la plante N’EST PAS un bonsaï :
  • Ne PAS afficher ces sections
  • Ne PAS mentionner la taille de bonsaï
  • Ne PAS donner de conseils spécifiques bonsaï

FORMAT DE RÉPONSE EXACT (OBLIGATOIRE) :

🪴 Plante identifiée :
- Nom commun :
- Nom latin (si possible) :
- Confiance : XX %

🔎 Indices visuels observés :
- (3 max)

📅 Lecture saisonnière (basée sur le mois réel) :
- Normal / Anormal pour DÉCEMBRE :
- Pourquoi :

🌿 État général de la plante :
- Synthèse courte et claire

🪲 Parasites possibles :
🍃 Maladies possibles :

✂️ Taille (si bonsaï ou plante concernée) :
- Conseillée / Déconseillée / À reporter
- Type : entretien / structure
- Pourquoi :

💧 Arrosage conseillé (maintenant) :
☀️ Exposition conseillée :

🥕 Impact sur la récolte (si potager) :
- Aucun / Faible / Modéré / Élevé

🍽️ Consommation (si potager) :
- Sans risque / À éviter / À vérifier

🚦 Priorité d’action :
- Urgent / Peut attendre / Aucune action nécessaire

✅ Actions immédiates recommandées (max 3) :
1.
2.
3.

❌ Erreurs courantes à éviter :
- (2 max)

🔮 Si rien n’est fait :
- Ce qui risque d’arriver sous 2–4 semaines

⚠️ Quand consulter un professionnel :
- Condition claire et factuelle
"""


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
def _region_to_coords(region: str):
    # Approximation par ville “référence” (suffisant pour démarrer)
    mapping = {
        "Nord": (50.6292, 3.0573),       # Lille
        "Ouest": (47.2184, -1.5536),     # Nantes
        "Est": (48.5734, 7.7521),        # Strasbourg
        "Sud-Ouest": (43.6047, 1.4442),  # Toulouse
        "Sud-Est": (43.2965, 5.3698),    # Marseille
        "Montagne": (45.9237, 6.8694),   # Chamonix
        "France": (46.6034, 1.8883),     # Centre approx
    }
    return mapping.get(region, mapping["France"])

def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))

def _meteo_resume(region: str) -> dict:
    lat, lon = _region_to_coords(region)
    base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Europe/Paris",
        "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,windspeed_10m_max",
        "forecast_days": 7,
    }
    url = base + "?" + urllib.parse.urlencode(params)
    data = _fetch_json(url)

    daily = data.get("daily", {}) or {}
    tmin = daily.get("temperature_2m_min", []) or []
    tmax = daily.get("temperature_2m_max", []) or []
    rain = daily.get("precipitation_sum", []) or []
    wind = daily.get("windspeed_10m_max", []) or []

    if not tmin or not tmax:
        return {"ok": False, "region": region}

    # Indicateurs simples
    min7 = min(tmin) if tmin else None
    max7 = max(tmax) if tmax else None
    rain7 = sum(rain) if rain else 0.0
    wind7 = max(wind) if wind else None
    gel = (min7 is not None and min7 <= 0.0)

    return {
        "ok": True,
        "region": region,
        "min_7j": round(min7, 1) if min7 is not None else None,
        "max_7j": round(max7, 1) if max7 is not None else None,
        "pluie_7j_mm": round(rain7, 1),
        "vent_max_kmh": round(wind7, 1) if wind7 is not None else None,
        "risque_gel": bool(gel),
        "conseil": (
            "Risque de gel : protège les cultures sensibles, limite les arrosages tardifs."
            if gel else
            "Pas de gel marqué : surveille l’humidité et adapte l’arrosage selon la pluie."
        )
    }
    
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
    meteo = _meteo_resume(region)

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
Météo 7 jours (à prendre en compte) :
- Min 7j: {meteo.get("min_7j")}
- Max 7j: {meteo.get("max_7j")}
- Pluie 7j (mm): {meteo.get("pluie_7j_mm")}
- Vent max (km/h): {meteo.get("vent_max_kmh")}
- Risque gel: {meteo.get("risque_gel")}
- Conseil météo: {meteo.get("conseil")}

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
            "lune": lune,
            "meteo": meteo,
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

@app.post("/meteo")
def meteo():
    data = request.get_json(silent=True) or {}
    region = (data.get("region") or "France").strip()
    return jsonify(_meteo_resume(region))



