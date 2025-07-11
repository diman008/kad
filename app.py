from flask import Flask, request, jsonify
import requests as rq
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/kad/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify(error='Missing q'), 400

    url = f'https://kad.arbitr.ru/Search?q={rq.utils.quote(q)}'
    resp = rq.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if resp.status_code != 200:
        return jsonify(error='kad.arbitr.ru unavailable'), 502

    soup = BeautifulSoup(resp.text, 'html.parser')
    items = []
    for row in soup.select('.b-cases__item')[:10]:          # первые 10 дел
        link_el = row.select_one('.b-cases__link')
        if not link_el:
            continue
        items.append({
            'case':  link_el.text.strip(),
            'link':  'https://kad.arbitr.ru' + link_el['href'],
            'court': row.select_one('.b-cases__court').text.strip() if row.select_one('.b-cases__court') else '',
            'date':  row.select_one('.b-cases__date').text.strip()  if row.select_one('.b-cases__date')  else ''
        })
    return jsonify(results=items)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
