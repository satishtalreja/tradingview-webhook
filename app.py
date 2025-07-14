from datetime import datetime
from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
import pytz

app = Flask(__name__)

# Use persistent Railway volume path
excel_filename = "/mnt/signals.xlsx"  # Make sure to add a volume in Railway

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
        utc_time_str = data.get('time')

        # Convert to IST
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        utc_time = pytz.utc.localize(utc_time)
        ist_time = utc_time.astimezone(pytz.timezone("Asia/Kolkata"))
        time = ist_time.strftime("%d-%m-%Y %H:%M:%S")

        # Prepare data row
        new_entry = pd.DataFrame([{
            "symbol": symbol,
            "event": event,
            "price": price,
            "time": time
        }])

        # Load existing or start new Excel
        if os.path.exists(excel_filename):
            existing_df = pd.read_excel(excel_filename)
            updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        else:
            updated_df = new_entry

        # Save updated Excel
        updated_df.to_excel(excel_filename, index=False)

        return jsonify({"status": "success", "message": "Signal saved to Railway volume"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_excel():
    if os.path.exists(excel_filename):
        return send_file(excel_filename, as_attachment=True)
    else:
        return "📂 No signals recorded yet.", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
