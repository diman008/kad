from fastapi import FastAPI, Query
import requests, time
app = FastAPI()

KAD = "https://kad.arbitr.ru/Kad/SearchInstances"
HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

def kad_post(payload):
    for attempt in range(3):           # до 3 попыток
        try:
            r = requests.post(KAD, json=payload, headers=HEADERS, timeout=45)
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("KAD unreachable")

@app.get("/kad/search", tags=["KAD"])
def search(q: str = Query(...), page: int = 1):
    payload = {
        "Page": page, "Count": 20,
        "Text": q, "CaseNumber": "",
        "Sides": [], "Judges": [],
        "WithVKSInstances": True, "WithoutVKSInstances": False
    }
    raw = kad_post(payload)
    items = [{
        "case": r["CaseNumber"],
        "link": f'https://kad.arbitr.ru/Card/{r["CaseId"]}',
        "court": r["CourtName"],
        "date": r["Date"]
    } for r in raw.get("Items", [])]
    return {"results": items}

@app.get("/kad/details", tags=["KAD"])
def details(caseNumber: str = Query(...)):
    payload = {"CaseNumber": caseNumber}
    return kad_post(payload)          # отдаём как есть
