from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

status_file = "status.json"

vehicles = {
    "M1": ["CHF", "HL", "RD 1", "RD 2"],
    "M2": ["CHF", "HL", "RD 1", "RD 2"],
    "V1": ["CHF", "BM"],
    "R1": ["CHF", "BM"],
    "S1": ["CHF", "BM"],
    "R3": ["CHF", "HL", "BM 1", "BM 2"]
}

def load_status():
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            return json.load(f)
    return {}

def save_status(status):
    with open(status_file, "w") as f:
        json.dump(status, f)

@app.route("/")
def index():
    status = load_status()
    return render_template("index.html", vehicles=vehicles, status=status)

@app.route("/toggle", methods=["POST"])
def toggle():
    data = request.get_json()
    key = f"{data['vehicle']}_{data['role']}"
    status = load_status()
    status[key] = not status.get(key, False)
    save_status(status)
    return jsonify({"active": status[key]})

@app.route("/reset", methods=["POST"])
def reset():
    save_status({})
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
