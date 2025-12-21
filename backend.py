from flask import Flask, request, jsonify

app = Flask(__name__)

# Bu şifreyi birazdan Meta paneline yazacağız, unutma!
VERIFY_TOKEN = "fiyat_botu_123"

@app.route("/whatsapp", methods=['GET', 'POST'])
def webhook():
    # Meta'nın "Bu site senin mi?" doğrulama isteği
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Doğrulama başarısız', 403

    # Kullanıcıdan mesaj (link) geldiğinde burası çalışır
    data = request.get_json()
    print("Gelen Mesaj:", data)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=10000)