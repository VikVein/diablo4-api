from flask import Flask, request, jsonify
from datetime import datetime
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

SOURCES = [
    {
        "name": "Mobalytics",
        "base": "https://mobalytics.gg/diablo-4",
        "search": "https://mobalytics.gg/diablo-4/builds"
    },
    {
        "name": "D4Builds",
        "base": "https://d4builds.gg",
        "search": "https://d4builds.gg/builds"
    }
]

def normalize(text):
    return (text or "").lower().replace("-", " ").strip()

def fetch_page(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 Diablo4BuildAssistant/1.0"
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.text
    except Exception:
        return ""
    return ""

def extract_builds_from_page(html, source_name, source_base, character_class, skill, item):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    wanted_terms = [
        normalize(character_class),
        normalize(skill),
        normalize(item)
    ]
    wanted_terms = [x for x in wanted_terms if x]

    links = soup.find_all("a", href=True)

    for link in links:
        text = normalize(link.get_text(" "))
        href = link.get("href", "")

        if not text:
            continue

        match_score = 0
        for term in wanted_terms:
            if term in text or term.replace(" ", "-") in href.lower():
                match_score += 1

        if match_score > 0:
            url = href if href.startswith("http") else source_base.rstrip("/") + "/" + href.lstrip("/")

            results.append({
                "name": link.get_text(" ", strip=True)[:120],
                "source": source_name,
                "url": url,
                "purpose": "Unknown",
                "confidence": "medium",
                "match_score": match_score
            })

    unique = []
    seen = set()

    for build in results:
        if build["url"] not in seen:
            unique.append(build)
            seen.add(build["url"])

    return unique[:10]

def score_build(build):
    source_bonus = 1 if build.get("source") in ["Mobalytics", "D4Builds"] else 0
    confidence = build.get("confidence", "low")

    base = 6.5

    if confidence == "high":
        base += 1.5
    elif confidence == "medium":
        base += 0.8

    base += source_bonus * 0.3

    final = min(round(base, 1), 10)

    return {
        "leveling": final - 0.3,
        "endgame": final,
        "survivability": final - 0.5,
        "damage": final,
        "ease": final - 0.2,
        "gear_dependency": 7.0,
        "speed": final - 0.1,
        "bossing": final - 0.4,
        "final": final
    }

def tier(score):
    if score >= 9:
        return "S"
    if score >= 8:
        return "A"
    if score >= 7:
        return "B"
    if score >= 6:
        return "C"
    return "Experimental"

def theorycraft_build(character_class, skill, item):
    name_parts = [skill, character_class, "Custom Theorycraft"]
    name = " ".join([x.title() for x in name_parts if x])

    return {
        "name": name,
        "source": "Theorycraft",
        "url": None,
        "purpose": "Custom / Experimental",
        "confidence": "low",
        "type": "Experimental Theorycraft Build",
        "concept": f"Build criada usando sinergias gerais de {character_class} com foco em {skill or item}.",
        "warning": "Não foi encontrada build confirmada nas fontes. Esta build deve ser tratada como experimental."
    }

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Diablo 4 Build API running",
        "endpoints": [
            "/search-builds",
            "/latest-meta",
            "/patch-status",
            "/coach"
        ]
    })

@app.route("/patch-status")
def patch_status():
    return jsonify({
        "game": "Diablo 4",
        "status": "live-check-needed",
        "note": "Use source freshness from Mobalytics/D4Builds before claiming current meta.",
        "checked_at": datetime.utcnow().isoformat()
    })

@app.route("/search-builds")
def search_builds():
    character_class = request.args.get("class", "")
    skill = request.args.get("skill", "")
    item = request.args.get("item", "")

    all_builds = []

    for source in SOURCES:
        html = fetch_page(source["search"])
        found = extract_builds_from_page(
            html,
            source["name"],
            source["base"],
            character_class,
            skill,
            item
        )
        all_builds.extend(found)

    if not all_builds:
        all_builds = [theorycraft_build(character_class, skill, item)]

    for build in all_builds:
        build["score"] = score_build(build)
        build["tier"] = tier(build["score"]["final"])

    return jsonify({
        "query": {
            "class": character_class,
            "skill": skill,
            "item": item
        },
        "count": len(all_builds),
        "builds": all_builds[:10],
        "checked_at": datetime.utcnow().isoformat()
    })

@app.route("/latest-meta")
def latest_meta():
    character_class = request.args.get("class", "")

    return jsonify({
        "class": character_class,
        "message": "Use /search-builds with class, skill, or item for source-based meta checks.",
        "sources": SOURCES,
        "checked_at": datetime.utcnow().isoformat()
    })

@app.route("/coach")
def coach():
    character_class = request.args.get("class", "")
    level = request.args.get("level", "")
    build = request.args.get("build", "")
    problem = request.args.get("problem", "")

    advice = []

    if "dying" in normalize(problem) or "morrendo" in normalize(problem):
        advice.append("Priorize vida, armadura, redução de dano e habilidades defensivas.")
    if "damage" in normalize(problem) or "dano" in normalize(problem):
        advice.append("Priorize arma melhor, ranks da habilidade principal, multiplicadores e aspectos ofensivos.")
    if "resource" in normalize(problem) or "mana" in normalize(problem):
        advice.append("Busque geração de recurso, redução de custo e passivas de sustain.")

    if not advice:
        advice.append("Continue seguindo a progressão da build e atualize arma/aspectos sempre que possível.")

    return jsonify({
        "class": character_class,
        "level": level,
        "build": build,
        "problem": problem,
        "advice": advice,
        "next_step": "Informe nível, build escolhida, problema atual e itens importantes para coaching mais preciso."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
