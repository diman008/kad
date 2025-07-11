import os, json
from flask import Flask, request, jsonify
import requests as rq

app = Flask(__name__)

KAD_API = "https://kad.arbitr.ru/Kad/SearchInstances"
UA       = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36")

def query_kad(text: str, page: int = 1, count: int = 20):
    payload = {
        "Page": page,
        "Count": count,
        "CaseNumber": "",          # если нужен поиск по номеру — заполнится ниже
        "Sides": [], "Judges": [],
        "CaseCategory": None,
        "CaseDateFrom": None,
        "CaseDateTo":   None,
        "Instance": None,
        "Text": text              # свободный текст (документы / предмет спора)
    }

    # если пользователь ввёл номер дела — кладём в CaseNumber
    if any(c.isdigit() for c in text) and " " not in text:
        payload["CaseNumber"] = text
        payload["Text"] = ""

    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json;charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://kad.arbitr.ru",
        "Referer": "https://kad.arbitr.ru/"
    }

    r = rq.post(KAD_API, headers=headers, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

@app.route("/kad/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(error="Missing q"), 400

    try:
        data = query_kad(q)
    except Exception as e:
        return jsonify(error=str(e)), 502

    results = []
    for row in data.get("Items", [])[:10]:
        results.append({
            "case":  row.get("CaseNumber"),
            "link":  f'https://kad.arbitr.ru/Card/{row.get("CaseId")}',
            "court": row.get("CourtName"),
            "date":  row.get("Date"),
            "category": row.get("CaseCategory")
        })
    return jsonify(results=results)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
