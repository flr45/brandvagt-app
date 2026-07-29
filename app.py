from pathlib import Path
from threading import Lock
import json
import os
import tempfile

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

STATUS_FILE = Path(
    os.environ.get(
        "BRANDVAGT_STATUS_FILE",
        str(Path(app.root_path) / "status.json"),
    )
).resolve()
STATUS_LOCK = Lock()

vehicles = {
    "M1": ["CHF", "HL", "RD 1", "RD 2"],
    "M2": ["CHF", "HL", "RD 1", "RD 2"],
    "V1": ["CHF", "BM"],
    "R1": ["CHF", "BM"],
    "S1": ["CHF", "BM"],
    "R3": ["CHF", "HL", "BM 1", "BM 2"],
}


def load_status_unlocked():
    if not STATUS_FILE.exists():
        return {}

    try:
        with STATUS_FILE.open("r", encoding="utf-8") as file:
            value = json.load(file)
    except (OSError, json.JSONDecodeError):
        app.logger.exception("Kunne ikke læse statusfilen")
        return {}

    return value if isinstance(value, dict) else {}


def load_status():
    with STATUS_LOCK:
        return load_status_unlocked()


def save_status_unlocked(status):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_path = tempfile.mkstemp(
        dir=STATUS_FILE.parent,
        prefix=f".{STATUS_FILE.name}.",
        text=True,
    )

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(status, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, STATUS_FILE)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@app.get("/")
def index():
    return render_template("index.html", vehicles=vehicles, status=load_status())


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/toggle")
def toggle():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ugyldig JSON"}), 400

    vehicle = data.get("vehicle")
    role = data.get("role")
    if vehicle not in vehicles or role not in vehicles[vehicle]:
        return jsonify({"error": "Ukendt køretøj eller rolle"}), 400

    key = f"{vehicle}_{role}"
    with STATUS_LOCK:
        status = load_status_unlocked()
        status[key] = not bool(status.get(key, False))
        save_status_unlocked(status)
        active = status[key]

    return jsonify({"active": active})


@app.post("/reset")
def reset():
    with STATUS_LOCK:
        save_status_unlocked({})
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
