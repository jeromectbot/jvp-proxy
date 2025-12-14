from flask import Flask, request, jsonify
import os
from openai import OpenAI

app = Flask(__name__)

# OpenAI client (clé dans Render > Environment)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "ok": True,
        "service": "jardin-vision-proxy",
        "endpoints": {
            "health": "/health (GET)",
            "analyze": "/analyze (POST)"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/analyze", methods=["GET"])
def analyze_help():
    # Pour éviter "Method Not Allowed" quand tu testes dans le navigateur
    return jsonify({
        "ok": True,
        "hint": "Utilise POST sur /analyze avec un JSON {\"prompt\":\"...\"}",
        "example_body": {"prompt": "Ma plante a des feuilles jaunes, que faire ?"}
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    if not os.getenv("OPENAI_API_KEY"):
        return jsonify({"error": "OPENAI_API_KEY is missing in Render Environment"}), 500

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Tu es un assistant jardinage. Réponds de façon pratique, courte, en étapes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    return jsonify({"result": resp.choices[0].message.content})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
