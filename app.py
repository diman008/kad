# ---------- app.py ----------
# Простой прокси к КАД Арбитр

import time, requests, os
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="KAD proxy")

KAD_ENDPOINT = "https://kad.arbitr.ru/Kad/SearchInstances"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

# ------------------ вспомогательная функция ------------------
def kad_request(payload: dict) -> dict:
    """POST в КАД с 3 попытками и таймаутом 45 с."""
    for attempt in range(3):
        try:
            r = requests.post(KAD_ENDPOINT, json=payload,
                              headers=HEADERS, timeout=45)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == 2:
                raise RuntimeError(f"KAD error: {e}") from e
            time.sleep(2 * (attempt + 1))

# ------------------------- /kad/search -----------------------
@app.get("/kad/search", tags=["KAD"])
def search_kad_cases(
    q: str = Query(..., description="Ключевые слова"),
    page: int = Query(1, ge=1, description="Номер страницы")
):
    payload = {
        "Page": page,
        "Count": 20,
        "Text": q,
        "CaseNumber": "",
        "Sides": [], "Judges": [],
        "WithVKSInstances": True,
        "WithoutVKSInstances": False
    }
    raw = kad_request(payload)
    rows = raw.get("Instances", [])          # актуальный ключ
    results = [{
        "case":  row.get("CaseNumber"),
        "link":  f'https://kad.arbitr.ru/Card/{row.get("CaseId")}',
        "court": row.get("CourtName"),
        "date":  row.get("Date")
    } for row in rows]
    return JSONResponse({"results": results})

# ------------------------ /kad/details -----------------------
@app.get("/kad/details", tags=["KAD"])
def get_kad_case_details(
    caseNumber: str = Query(..., description="Номер дела А40-…/2024")
):
    return kad_request({"CaseNumber": caseNumber})

# ------------------- локальный запуск -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app",
                host="0.0.0.0",
                port=int(os.getenv("PORT", 8000)),
                reload=True)
