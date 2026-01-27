import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "BURAYA_KENDI_KEYIN"

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        search_query = data.get("title", "")

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr",
            "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])

        output = []

        for item in results[:10]:
            raw_link = item.get("link", "")
            product_id = ""

            id_match = re.search(r'p-(\d+)|/(\d{7,})', raw_link)
            if id_match:
                product_id = id_match.group(1) or id_match.group(2)

            output.append({
                "site": item.get("source", ""),
                "price": item.get("price", ""),
                "image": item.get("thumbnail", ""),
                "p_id": product_id,
                "title": item.get("title", ""),
                "url": raw_link   # 🔥 İŞTE OLAYI ÇÖZEN SATIR
            })

        return jsonify({"results": output})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
