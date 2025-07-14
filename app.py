# ---------- app.py ----------
"""
Мини-прокси к КАД Арбитр
  • /kad/search   – поиск дел по ключевым словам
  • /kad/details  – карточка конкретного дела

Если КАД отвечает 451/403 (блокировка зарубежного IP),
код автоматически пробует тот же запрос через ScraperAPI
(нужен API-key и country_code=ru).
"""
import os, time, json, requests
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="KAD proxy")

KAD_URL = "https://kad.arbitr.ru/Kad/SearchInstances"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}

SCRAPER_KEY = os.getenv("SCRAPER_API")      # задайте в Render → Environment
SCRAPER_URL = "https://api.scraperapi.com/"

# ------------------------------------------------------------------
def kad_request(payload: dict) -> dict:
    """POST в КАД, fallback на ScraperAPI при 451/403."""
    def _post_direct() -> requests.Response:
        return requests.post(KAD_URL, json=payload,
                             headers=HEADERS, timeout=45)

    # 1. пытаемся напрямую
    resp = _post_direct()
    if resp.status_code in (451, 403) and SCRAPER_KEY:
        params = {
            "api_key": SCRAPER_KEY,
            "url": KAD_URL,
            "method": "POST",
            "country_code": "ru",
            "render": "false",
            "headers": json.dumps(HEADERS),
            "body": json.dumps(payload),
        }
        resp = requests.get(SCRAPER_URL, params=params, timeout=60)

    resp.raise_for_status()           # если всё ещё 4xx/5xx → исключение
    return resp.json()

# ------------------------------------------------------------------
@app.get("/kad/search", tags=["KAD"])
def search_kad_cases(
    q: str = Query(..., description="Ключевые слова, статья, ИНН, ФИО"),
    page: int = Query(1, ge=1, description="Номер страницы"),
):
    payload = {
        "Page": page,
        "Count": 20,
        "Text": q,
        "CaseNumber": "",
        "Sides": [],
        "Judges": [],
        "WithVKSInstances": True,
        "WithoutVKSInstances": False,
    }
    raw = kad_request(payload)
    rows = raw.get("Instances", [])
    results = [
        {
            "case":   row.get("CaseNumber"),
            "link":   f"https://kad.arbitr.ru/Card/{row.get('CaseId')}",
            "court":  row.get("CourtName"),
            "date":   row.get("Date"),
        }
        for row in rows
    ]
    return JSONResponse({"results": results})

# ------------------------------------------------------------------
@app.get("/kad/details", tags=["KAD"])
def get_kad_case_details(
    caseNumber: str = Query(..., description="Номер дела, напр. А40-5001/2022")
):
    return kad_request({"CaseNumber": caseNumber})

# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
