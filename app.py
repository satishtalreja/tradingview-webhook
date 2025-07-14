from datetime import datetime
from flask import Flask, request, jsonify, redirect, session
import pandas as pd
import os
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Replace this with a secure random value in production

excel_filename = "signals.xlsx"
CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']
REDIRECT_URI = 'https://web-production-8d8ce.up.railway.app/oauth2callback'

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
    <p>Authorize Google Drive: <a href="/authorize">Click here</a></p>
    </body>
    </html>
    """

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    return "✅ Google Drive Authorized. Now send signals to /webhook."

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        symbol = data.get("symbol")
        event = data.get("event")
        price = data.get("price")
        utc_time_str = data.get('time')

        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        utc = pytz.utc
        utc_time = utc.localize(utc_time)
        ist = pytz.timezone("Asia/Kolkata")
        ist_time = utc_time.astimezone(ist)
        time = ist_time.strftime("%d-%m-%Y %H:%M:%S")

        new_entry = pd.DataFrame([{
            "symbol": symbol,
            "event": event,
            "price": price,
            "time": time
        }])

        print("Received Webhook Signal:")
        print(new_entry)

        if os.path.exists(excel_filename):
            existing_df = pd.read_excel(excel_filename)
            updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        else:
            updated_df = new_entry

        updated_df.to_excel(excel_filename, index=False)

        # Upload to Google Drive if authorized
        if 'credentials' in session:
            creds = Credentials(**session['credentials'])
            service = build('drive', 'v3', credentials=creds)
            file_metadata = {
                'name': excel_filename,
                'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            media = MediaFileUpload(excel_filename, mimetype=file_metadata['mimeType'])
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        return jsonify({"status": "success", "message": "Signal received"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
