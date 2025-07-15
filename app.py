from datetime import datetime
from flask import Flask, request, jsonify
import pandas as pd
import pytz

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Webhook Receiver</title></head>
    <body style="font-family: Arial; background-color: #f0f8ff; text-align: center; padding-top: 80px;">
    <h1>🚀 Webhook Receiver is Running</h1>
    <p>Waiting for TradingView webhook at <strong>/webhook</strong> endpoint...</p>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        symbol = data.get("symbol")
        event = data.get("event")
        price = data.get("price")
        utc_time_str = data.get("time")

        # Convert to IST
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        utc_time = pytz.utc.localize(utc_time)
        ist_time = utc_time.astimezone(pytz.timezone("Asia/Kolkata"))
        time_str = ist_time.strftime("%d-%m-%Y %H:%M:%S")

        # Create DataFrame for inspection, later pipeline extension
        new_entry = pd.DataFrame([{
            "symbol": symbol,
            "event": event,
            "price": price,
            "time": time_str
        }])

        # Return DataFrame content as JSON for easy checking
        return jsonify({
            "status": "success",
            "data": new_entry.to_dict(orient="records")
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
