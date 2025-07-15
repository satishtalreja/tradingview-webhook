from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import pytz
import os

app = Flask(__name__)

# Configure SQLite for simplicity (auto creates signals.db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///signals.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define table model
class Signal(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # serial number
    symbol = db.Column(db.String(50))
    event = db.Column(db.String(20))
    price = db.Column(db.Float)
    time = db.Column(db.String(50))

# Create table on first run
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return """
    <html>
    <head><title>Webhook Receiver</title></head>
    <body style="font-family: Arial; background-color: #f0f8ff; text-align: center; padding-top: 80px;">
    <h1>🚀 Webhook Receiver is Running</h1>
    <p>Send TradingView webhook to <strong>/webhook</strong> endpoint.</p>
    <p>View stored signals table at <a href='/signals' target='_blank'>/signals</a>.</p>
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

        # Create DataFrame for potential future processing
        new_entry = pd.DataFrame([{
            "symbol": symbol,
            "event": event,
            "price": price,
            "time": time_str
        }])

        # Print to Railway logs
        print("🔔 Webhook received:")
        print(new_entry)

        # Insert into DB
        signal = Signal(symbol=symbol, event=event, price=price, time=time_str)
        db.session.add(signal)
        db.session.commit()

        return jsonify({
            "status": "success",
            "data": new_entry.to_dict(orient="records")
        }), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/signals', methods=['GET'])
def view_signals():
    signals = Signal.query.all()

    table_html = """
    <html>
    <head>
        <title>Stored Signals</title>
        <style>
            body { font-family: Arial; background-color: #f9f9f9; padding: 20px; }
            table { border-collapse: collapse; width: 80%; margin: auto; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
            th { background-color: #f0f0f0; }
            h1 { text-align: center; }
        </style>
    </head>
    <body>
        <h1>📊 Stored TradingView Signals</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Symbol</th>
                <th>Event</th>
                <th>Price</th>
                <th>Time (IST)</th>
            </tr>
            {% for s in signals %}
            <tr>
                <td>{{ s.id }}</td>
                <td>{{ s.symbol }}</td>
                <td>{{ s.event }}</td>
                <td>{{ s.price }}</td>
                <td>{{ s.time }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    return render_template_string(table_html, signals=signals)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
