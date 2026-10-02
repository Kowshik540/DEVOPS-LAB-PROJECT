import datetime
import os
import platform
from flask import Flask, request, jsonify, render_template_string
import psutil

app = Flask(__name__)

# In-memory store with sample enterprise logs
LOG_STORE = [
    {"timestamp": "2026-10-02 10:00:12", "level": "INFO", "service": "auth-service", "message": "User admin logged in successfully"},
    {"timestamp": "2026-10-02 10:04:30", "level": "WARNING", "service": "payment-gateway", "message": "Latency threshold exceeded: 420ms"},
    {"timestamp": "2026-10-02 10:08:15", "level": "ERROR", "service": "order-processor", "message": "Connection refused to database pool"},
    {"timestamp": "2026-10-02 10:12:00", "level": "INFO", "service": "inventory-api", "message": "Stock cache refreshed"},
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevOps Microservice Telemetry Hub</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 30px; }
        .wrapper { max-width: 1100px; margin: auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }
        h1 { margin: 0; font-size: 24px; color: #38bdf8; }
        .badge { background: #059669; color: white; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px; text-align: center; }
        .card h3 { margin: 0 0 8px 0; font-size: 13px; color: #94a3b8; text-transform: uppercase; }
        .card p { margin: 0; font-size: 26px; font-weight: 700; color: #f1f5f9; }
        .form-panel { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 24px; }
        .form-row { display: flex; gap: 10px; margin-top: 10px; }
        input, select, button { padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: white; }
        input { flex: 2; }
        select { flex: 1; }
        button { background: #0284c7; border: none; font-weight: 600; cursor: pointer; padding: 10px 20px; }
        button:hover { background: #0369a1; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #334155; }
        th { background: #334155; font-size: 12px; text-transform: uppercase; color: #cbd5e1; }
        .lvl-INFO { color: #38bdf8; font-weight: bold; }
        .lvl-WARNING { color: #facc15; font-weight: bold; }
        .lvl-ERROR { color: #f87171; font-weight: bold; }
    </style>
</head>
<body>
<div class="wrapper">
    <header>
        <div>
            <h1>DevOps Telemetry & Log Monitoring Service</h1>
            <small style="color: #94a3b8;">Containerized Environment: {{ metrics.container_os }}</small>
        </div>
        <span class="badge">CONTAINER ACTIVE</span>
    </header>

    <div class="grid">
        <div class="card"><h3>Total Ingested Logs</h3><p>{{ metrics.total_logs }}</p></div>
        <div class="card"><h3>Error Count</h3><p style="color: #f87171;">{{ metrics.error_count }}</p></div>
        <div class="card"><h3>Container CPU Usage</h3><p>{{ metrics.cpu_usage }}%</p></div>
        <div class="card"><h3>Container RAM Usage</h3><p>{{ metrics.ram_usage }}%</p></div>
    </div>

    <div class="form-panel">
        <h3 style="margin: 0; color: #e2e8f0;">Ingest New Service Log Event</h3>
        <form method="POST" action="/log" class="form-row">
            <select name="level" required>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
            </select>
            <input type="text" name="service" placeholder="Service Name (e.g., auth-api)" required>
            <input type="text" name="message" placeholder="Log Message Description" required>
            <button type="submit">Ingest Log</button>
        </form>
    </div>

    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Service Name</th>
                <th>Log Message</th>
            </tr>
        </thead>
        <tbody>
            {% for item in logs[::-1] %}
            <tr>
                <td style="color: #94a3b8; font-size: 13px;">{{ item.timestamp }}</td>
                <td class="lvl-{{ item.level }}">{{ item.level }}</td>
                <td>{{ item.service }}</td>
                <td>{{ item.message }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
</body>
</html>
"""

def compute_metrics():
    mem = psutil.virtual_memory()
    error_count = sum(1 for log in LOG_STORE if log["level"] == "ERROR")
    return {
        "total_logs": len(LOG_STORE),
        "error_count": error_count,
        "cpu_usage": psutil.cpu_percent(interval=0.2),
        "ram_usage": mem.percent,
        "container_os": f"{platform.system()} {platform.release()} ({platform.machine()})"
    }

@app.route("/", methods=["GET"])
def dashboard():
    return render_template_string(HTML_TEMPLATE, logs=LOG_STORE, metrics=compute_metrics())

@app.route("/log", methods=["POST"])
def add_log_form():
    level = request.form.get("level", "INFO")
    service = request.form.get("service", "unknown-service")
    message = request.form.get("message", "")
    new_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "service": service,
        "message": message
    }
    LOG_STORE.append(new_entry)
    return dashboard()

@app.route("/api/logs", methods=["GET", "POST"])
def api_logs():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if not data.get("message"):
            return jsonify({"status": "error", "message": "Missing 'message' field"}), 400
        new_entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": data.get("level", "INFO"),
            "service": data.get("service", "external-api"),
            "message": data["message"]
        }
        LOG_STORE.append(new_entry)
        return jsonify({"status": "success", "entry": new_entry}), 201
    return jsonify({"total": len(LOG_STORE), "logs": LOG_STORE})

@app.route("/health", methods=["GET"])
def health_probe():
    return jsonify({
        "status": "UP",
        "timestamp": datetime.datetime.now().isoformat(),
        "runtime": "Docker Container",
        "system": compute_metrics()
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)