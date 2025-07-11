import os
import json
import requests as rq
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- настройки ----------------------------------------------------------
KAD_API      = "https://kad.arbitr.ru/Kad/SearchInstances"
SCRAPER_KEY  = os.getenv("SCRAPER_API")        # ключ ScraperAPI берём из переменной
SCRAPER_URL  = "https://api.scraperapi.com/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
# ------------------------------------------------------------------------

print("Using ScraperAPI, key starts with:",
      SCRAPER_KEY[:4] if SCRAPER_KEY else "None")

def kad_via_scraper(payload: dict):
    """Отправить POST в КАД через ScraperAPI и вернуть JSON."""
    params = {
        "api_key": SCRAPER_KEY,
        "url": KAD_API,
        "render": "false",
        "method": "POST",
        "headers": json.dumps({
            "User-Agent": UA,
            "Content-Type": "application/json;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        }),
        "body": json.dumps(payload)
    }
    r = rq.get(SCRAPER_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def build_payload(text: str, page: int = 1, count: int = 20) -> dict:
    """Сформировать JSON-payload КАД."""
    payload = {
        "Page": page,
        "Count": count,
        "CaseNumber": "",
        "Sides": [],
        "Judges": [],
        "CaseCategory": None,
        "CaseDateFrom": None,
        "CaseDateTo": None,
        "Instance": None,
        "Text": text
    }
    # если похоже на номер дела — перенесём в CaseNumber
    if any(c.isdigit() for c in text) and " " not in text:
        payload["CaseNumber"] = text
        payload["Text"] = ""
    return payload

@app.route("/kad/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(error="Missing q"), 400
    if not SCRAPER_KEY:
        return jsonify(error="SCRAPER_API key not set"), 500

    try:
        raw = kad_via_scraper(build_payload(q))
    except Exception as e:
        return jsonify(error=str(e)), 502

    items = [
        {
            "case":     row.get("CaseNumber"),
            "link":     f'https://kad.arbitr.ru/Card/{row.get("CaseId")}',
            "court":    row.get("CourtName"),
            "date":     row.get("Date"),
            "category": row.get("CaseCategory")
        }
        for row in raw.get("Items", [])[:10]
    ]
    return jsonify(results=items)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
