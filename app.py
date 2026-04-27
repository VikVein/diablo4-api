from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Diablo 4 API running"
    })

@app.route("/patch-status")
def patch_status():
    return jsonify({
        "game": "Diablo 4",
        "status": "ok",
        "checked_at": datetime.utcnow().isoformat()
    })

@app.route("/search-builds")
def search_builds():
    character_class = request.args.get("class", "")
    skill = request.args.get("skill", "")

    return jsonify({
        "query": {
            "class": character_class,
            "skill": skill
        },
        "builds": [
            {
                "name": f"{skill.title()} {character_class.title()} Build",
                "source": "Prototype",
                "purpose": "Testing",
                "confidence": "low"
            }
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
