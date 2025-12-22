from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# 🔥 CORS tamamen açık (MVP için ideal)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS":
        # Preflight request (Chrome için gerekli)
        return "", 200

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").lower()
    price = data.get("price", "")
    url = data.get("url", "")

    # 🔧 Şimdilik mock data (ileride API / scraping bağlanacak)
    results = [
        {
            "site": "Trendyol",
            "price": "₺24.999",
            "link": "https://www.trendyol.com/"
        },
        {
            "site": "Hepsiburada",
            "price": "₺25.499",
            "link": "https://www.hepsiburada.com/"
        },
        {
            "site": "Amazon",
            "price": "₺25.199",
            "link": "https://www.amazon.com.tr/"
        }
    ]

    return jsonify({
        "query": title,
        "current_price": price,
        "source_url": url,
        "results": results
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
