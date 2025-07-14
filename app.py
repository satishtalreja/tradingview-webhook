from datetime import datetime
from flask import Flask, request, jsonify
import pandas as pd
import os
import pytz

app = Flask(__name__)
excel_filename = "signals.xlsx"

@app.route('/')
def home():
    return """
    <html>
    <head>
    <title>Webhook Receiver</title>
    <style>
    body {
    font-family: Arial, sans-serif;
    background-color: #f0f8ff;
    color: #333;
    text-align: center;
    padding-top: 80px;
    }
    h1 { color: #2c3e50; }
    p { color: #555; font-size: 18px; }
    </style>
    </head>
    <body>
    <h1>🚀 Webhook Receiver is Running</h1>
    <p>Waiting for TradingView webhook at <strong>/webhook</strong> endpoint...</p>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        # Extract necessary fields
        symbol = data.get("symbol")
        event = data.get("event")
        price = data.get("price")
        # time = data.get("time")  # Expected as a string like "2025-07-14 15:30:45"
        utc_time_str = data.get('time')
        # Parse the time string as UTC
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        utc = pytz.utc
        utc_time = utc.localize(utc_time)
        # Convert to your local timezone (e.g., IST)
        ist = pytz.timezone("Asia/Kolkata")
        ist_time = utc_time.astimezone(ist)
        # Format the time as desired
        time = ist_time.strftime("%d-%m-%Y %H:%M:%S")

        new_entry = pd.DataFrame([{
        "symbol": symbol,
        "event": event,
        "price": price,
        "time": time
        }])
        print("Received Webhook Signal:")
        print(new_entry)
            # Check if Excel file exists, append or create accordingly
        if os.path.exists(excel_filename):
            existing_df = pd.read_excel(excel_filename)
            updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        else:
            updated_df = new_entry

        # Save the updated DataFrame to Excel
        updated_df.to_excel(excel_filename, index=False)

        return jsonify({"status": "success", "message": "Signal received"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
