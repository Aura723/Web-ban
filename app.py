import csv
import io
import os
import re
import time
from datetime import datetime, timezone
from threading import Lock

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-before-deployment")
MAX_ROWS = max(1, min(int(os.getenv("MAX_ROWS", "100")), 500))
LOG_LIMIT = 100
logs = []
log_lock = Lock()
PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


def add_log(phone, status, detail):
    entry = {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "phone": phone,
        "status": status,
        "detail": detail,
    }
    with log_lock:
        logs.insert(0, entry)
        del logs[LOG_LIMIT:]


def load_rows(file_storage):
    raw = file_storage.stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or "phone_number" not in reader.fieldnames:
        raise ValueError("CSV must include a 'phone_number' header.")
    if "authorized" not in reader.fieldnames:
        raise ValueError("CSV must include an 'authorized' column. Set it to yes only for numbers you own or have explicit permission to test.")
    rows = []
    for row in reader:
        phone = (row.get("phone_number") or "").strip()
        authorized = (row.get("authorized") or "").strip().lower()
        if not phone:
            continue
        if authorized not in {"yes", "true", "1"}:
            add_log(phone, "SKIPPED", "No authorization marked in CSV.")
            continue
        if not PHONE_RE.fullmatch(phone):
            add_log(phone, "INVALID", "Use international format, e.g. +2348012345678.")
            continue
        rows.append(phone)
        if len(rows) > MAX_ROWS:
            raise ValueError(f"Upload exceeds the configured limit of {MAX_ROWS} authorized rows.")
    return rows


@app.get("/")
def index():
    with log_lock:
        current_logs = list(logs)
    return render_template(
        "index.html",
        logs=current_logs,
        max_rows=MAX_ROWS,
        total=len(current_logs),
        success_count=sum(1 for x in current_logs if x["status"] == "SIMULATED"),
        failed_count=sum(1 for x in current_logs if x["status"] in {"INVALID", "ERROR"}),
    )


@app.post("/test")
def test_numbers():
    if request.form.get("confirm_authorized") != "yes":
        flash("Confirm that every submitted number is yours or explicitly authorized.", "error")
        return redirect(url_for("index"))

    upload = request.files.get("csv_file")
    if not upload or not upload.filename:
        flash("Choose a CSV file first.", "error")
        return redirect(url_for("index"))
    if not upload.filename.lower().endswith(".csv"):
        flash("Upload a .csv file.", "error")
        return redirect(url_for("index"))

    try:
        phones = load_rows(upload)
    except (UnicodeDecodeError, ValueError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))

    if not phones:
        flash("No valid, authorized phone numbers were found.", "error")
        return redirect(url_for("index"))

    # Safe local simulation only: this deliberately does not contact WhatsApp
    # or send pairing codes/requests to any phone number.
    for phone in phones:
        add_log(phone, "SIMULATED", "Local validation passed; no message or pairing request was sent.")
    flash(f"Finished local validation for {len(phones)} authorized number(s). No WhatsApp requests were sent.", "success")
    return redirect(url_for("index"))


@app.post("/clear-logs")
def clear_logs():
    with log_lock:
        logs.clear()
    flash("Logs cleared.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
