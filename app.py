from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

@app.route("/", methods=["GET", "HEAD"])
def home():
    # Route demandée par Render (évite les 404)
    return jsonify({"ok": True, "service": "jardin-vision-proxy"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/analyze", methods=["POST"])
def analyze():
    if not OPENAI_API_KEY:
        return jsonify({"error": "OPENAI_API_KEY missing on server"}), 500

    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Tu es un assistant jardinage. Réponse courte, claire, concrète."},
            {"role": "user", "content": prompt}
        ]
    )

    return jsonify({"result": response.choices[0].message["content"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
