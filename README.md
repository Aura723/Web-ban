# Pairing Test Lab — Full Web Application

A Flask dashboard for importing authorized phone numbers from CSV, validating international-format phone numbers, and viewing a local activity log.

**Important:** this project is a safe local validation/demo harness. It does not connect to WhatsApp, submit pairing requests, send codes, or automate linking accounts.

## Features
- Responsive dashboard
- CSV upload and validation
- Requires an explicit `authorized` column
- Validates international phone-number format (`+` followed by 8–15 digits, first digit non-zero)
- Configurable row limit
- Local activity log and clear-log action
- `.env` configuration
- Docker deployment file

## CSV format

Create a UTF-8 CSV file such as `numbers.csv`:

```csv
phone_number,authorized
+2348012345678,yes
+2348098765432,yes
```

Only rows marked `yes`, `true`, or `1` in `authorized` are processed. Other rows are skipped. Use only numbers you own or have explicit permission to test.

## Run locally

### 1. Install Python
Use Python 3.10 or newer.

### 2. Create and activate a virtual environment

Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Copy `.env.example` to `.env` and replace `SECRET_KEY` with a long random value.

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

macOS/Linux:
```bash
cp .env.example .env
```

### 5. Start the dashboard
```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | development placeholder | Flask session security; replace before deployment |
| `HOST` | `127.0.0.1` | Bind address. Keep local for local-only use |
| `PORT` | `5000` | Web server port |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode only for local development |
| `MAX_ROWS` | `100` | Maximum authorized CSV rows; app clamps this to 1–500 |

## Docker

For a production-style container, build with the production requirements:

```bash
docker build -t pairing-test-lab .
docker run --rm -p 5000:5000 --env-file .env pairing-test-lab
```

Before deploying publicly:
- Set a strong `SECRET_KEY`.
- Use HTTPS and a production WSGI server.
- Add authentication and rate limiting.
- Do not expose this demo dashboard publicly without access controls.
- The included Dockerfile installs `requirements.txt`; for Gunicorn, change the Dockerfile install line to `COPY requirements-prod.txt requirements.txt` before `RUN pip install ...`, or install `gunicorn` in the image.

## Notes
- Activity logs are in memory and reset when the process restarts.
- The application only performs local validation and simulation; no external pairing requests are made.
