from flask import Flask, request, jsonify
app = Flask(__name__)

# NOTE: This is a placeholder backend.
# Replace with real integrations:
# - Affiliate APIs (Trendyol, Hepsiburada, Amazon) to fetch product, price and affiliate links
# - Or legal scraping with careful respect to robots.txt and site terms
# - Use caching and rate limits

@app.route('/compare', methods=['POST'])
def compare():
    data = request.get_json() or {}
    title = data.get('title','').lower()
    # Mock matching logic — in real app you'd query APIs or search product catalogues
    # Return sample results
    results = [
        {"site":"Trendyol","price":"₺1.299","link":"https://www.trendyol.com/"},
        {"site":"Hepsiburada","price":"₺1.259","link":"https://www.hepsiburada.com/"},
        {"site":"Amazon","price":"₺1.319","link":"https://www.amazon.com.tr/"}
    ]
    return jsonify({"query_title": title, "results": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
