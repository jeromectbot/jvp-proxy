from flask import Flask, request, jsonify
import os
from openai import OpenAI

app = Flask(__name__)

# Client OpenAI (clé dans Render : OPENAI_API_KEY)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/")
def home():
    return jsonify({
        "ok": True,
        "service": "jardin-vision-proxy",
        "endpoints": ["/health", "/analyze"]
    })


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Protection: si la clé n'est pas définie côté Render
    if not os.getenv("OPENAI_API_KEY"):
        return jsonify({"error": "OPENAI_API_KEY missing on server"}), 500

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant jardinage. Réponds court, concret, et prudent."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        text = resp.choices[0].message.content or ""
        return jsonify({"result": text})

    except Exception as e:
        return jsonify({"error": "OpenAI request failed", "details": str(e)}), 500


if __name__ == "__main__":
    # En local seulement. Sur Render, gunicorn démarre l'app.
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
