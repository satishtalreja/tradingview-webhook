from datetime import datetime
from flask import Flask, request, jsonify
import pandas as pd
import os
import pytz
import io
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = Flask(__name__)
excel_filename = "signals.xlsx"

# Get credentials from environment variable
def get_drive_service():
    json_creds = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
    if not json_creds:
        raise ValueError("Missing GOOGLE_CLIENT_SECRET_JSON env variable")

    print(f"Type of json_creds: {type(json_creds)}")
    creds_dict = json.loads(json_creds)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build('drive', 'v3', credentials=creds)
    return service

def upload_to_drive(filename, mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
    service = get_drive_service()
    file_metadata = {
        'name': filename,
        'parents': []  # Optional: set folder ID inside this list if needed
    }
    media = MediaIoBaseUpload(io.FileIO(filename, 'rb'), mimetype=mime_type)
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print(f"✅ File uploaded to Google Drive with ID: {uploaded.get('id')}")

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
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        utc_time = pytz.utc.localize(utc_time)
        ist_time = utc_time.astimezone(pytz.timezone("Asia/Kolkata"))
        time = ist_time.strftime("%d-%m-%Y %H:%M:%S")

        new_entry = pd.DataFrame([{
            "symbol": symbol,
            "event": event,
            "price": price,
            "time": time
        }])

        if os.path.exists(excel_filename):
            existing_df = pd.read_excel(excel_filename)
            updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        else:
            updated_df = new_entry

        updated_df.to_excel(excel_filename, index=False)

        # Upload to Google Drive
        upload_to_drive(excel_filename)

        return jsonify({"status": "success", "message": "Signal received and uploaded"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
