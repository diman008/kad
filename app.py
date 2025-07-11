@@
-import requests as rq
+import requests as rq, json, os

-KAD_API = "https://kad.arbitr.ru/Kad/SearchInstances"
-UA       = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
-            "AppleWebKit/537.36 (KHTML, like Gecko) "
-            "Chrome/126.0 Safari/537.36")
+KAD_API      = "https://kad.arbitr.ru/Kad/SearchInstances"
+SCRAPER_KEY  = os.getenv("SCRAPER_API")     # берём из переменной окружения
+SCRAPER_URL  = "https://api.scraperapi.com/"
+UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
+      "AppleWebKit/537.36 (KHTML, like Gecko) "
+      "Chrome/126.0 Safari/537.36")
 
 def query_kad(text: str, page: int = 1, count: int = 20):
@@
-    headers = {
-        "User-Agent": UA,
-        "Content-Type": "application/json;charset=UTF-8",
-        "X-Requested-With": "XMLHttpRequest",
-        "Origin": "https://kad.arbitr.ru",
-        "Referer": "https://kad.arbitr.ru/"
-    }
-
-    r = rq.post(KAD_API, headers=headers, json=payload, timeout=15)
+    # --- запрос через ScraperAPI ---
+    params = {
+        "api_key": SCRAPER_KEY,
+        "url": KAD_API,
+        "render": "false",       # нам не нужен HTML, только JSON
+        "method": "POST",
+        "headers": json.dumps({
+            "User-Agent": UA,
+            "Content-Type": "application/json;charset=UTF-8",
+            "X-Requested-With": "XMLHttpRequest",
+        }),
+        "body": json.dumps(payload)
+    }
+    r = rq.get(SCRAPER_URL, params=params, timeout=30)
     r.raise_for_status()
     return r.json()
