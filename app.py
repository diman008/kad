# ---------- app.py  ----------
# Мини-прокси к КАД Арбитр: два маршрута
#   • /kad/search   – поиск дел по ключевым словам
#   • /kad/details  – карточка конкретного дела
# Работает без ключей, только requests.

import time
import requests
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="KAD proxy")

KAD_ENDPOINT = "https://kad.arbitr.ru/Kad/SearchInstances"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

# ------------------------------------------------------------
def kad_request(payload: dict) -> dict:
    """POST в КАД с 3 попытками и 45-сек таймаутом."""
    for attempt in range(3):
        try:
            r = requests.post(KAD_ENDPOINT, json=payload,
                              headers=HEADERS, timeout=45)
            r.raise_for_status()
            return r.json()        # ValueError -> except
        except Exception as e:
            if attempt == 2:
                raise RuntimeError(f"KAD error: {e}") from e
            time.sleep(2 * (attempt + 1))   # 2, 4 c задержка и повтор

# ------------------------------------------------------------
@app.get("/kad/search", tags=["KAD"], methods=["GET", "HEAD"])
def search_kad_cases(
    q: str = Query(..., description="Ключевые слова"),
    page: int = Query(1, ge=1, description="Номер страницы")
):
    """Поиск арбитражных дел по тексту (статья, ИНН, ФИО…)."""
    payload = {
        "Page": page,
        "Count": 20,
        "Text": q,
        "CaseNumber": "",
        "Sides": [],
        "Judges": [],
        "WithVKSInstances": True,
        "WithoutVKSInstances": False
    }

    raw = kad_request(payload)
    rows = raw.get("Instances", [])           # <-- актуальный ключ!

    results = [{
        "case":   row.get("CaseNumber"),
        "link":   f'https://kad.arbitr.ru/Card/{row.get("CaseId")}',
        "court":  row.get("CourtName"),
        "date":   row.get("Date")
    } for row in rows]

    return JSONResponse({"results": results})

# ------------------------------------------------------------
@app.get("/kad/details", tags=["KAD"], methods=["GET", "HEAD"])
def get_kad_case_details(
    caseNumber: str = Query(..., description="Номер дела А40-…/2024")
):
    """Возвращает «сырую» карточку дела из КАД."""
    return kad_request({"CaseNumber": caseNumber})

# ------------------------------------------------------------
# Локальный запуск: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("app:app",
                host="0.0.0.0",
                port=int(os.getenv("PORT", 8000)),
                reload=True)
