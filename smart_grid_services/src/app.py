# smart_grid_services/app.py
import os
import json
import time
import threading
import logging
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request

# Import SE logic & AAS writer
from state_estimation.se_main import load_config, load_pandapower_network, load_se_connector, run_state_estimation_pipeline
from state_estimation.se_to_aas import write_estimates_to_aas

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_services")

CONFIG_PATH = Path("/app/config_se.yaml")
AAS_JSON_PATH = Path(
    os.environ.get(
        "AAS_JSON_PATH",
        "/app/basyx_aas/cim_eq_gl_aasx_hierarchical_20151231T2300Z_YYY_EQ_.json"
    )
)

# --- Scheduler state ---
_loop_thread = None
_stop_event = threading.Event()
_loop_lock = threading.Lock()
_status = {
    "running": False,
    "interval_sec": None,
    "last_run": None,
    "last_result": None,
    "error": None,
}

# --- Core SE runner ---
def _run_once_internal(aas_json_override: Path | None = None):
    try:
        logger.info("Running State Estimation once...")
        cfg = load_config(CONFIG_PATH)
        net = load_pandapower_network(cfg)
        if net is None:
            raise RuntimeError("Pandapower network could not be created")

        connector = load_se_connector(cfg, net)
        results = run_state_estimation_pipeline(connector, net)

        if not results.get("converged", False):
            raise RuntimeError(results.get("error", "State estimation did not converge"))

        target = Path(aas_json_override) if aas_json_override else AAS_JSON_PATH
        write_estimates_to_aas(target, results, net)

        _status.update({
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_result": {
                "converged": True,
                "vm_pu_count": len(results.get("vm_pu", {})),
                "va_degree_count": len(results.get("va_degree", {})),
            },
            "error": None,
        })
        logger.info("State Estimation successful.")
        return {"ok": True, "details": _status["last_result"], "aas_file": str(target)}
    except Exception as e:
        logger.exception("State Estimation failed.")
        _status.update({"error": str(e)})
        return {"ok": False, "error": str(e)}

# --- Background loop ---
def _loop(interval_sec: int, aas_json_override: Path | None):
    while not _stop_event.is_set():
        _run_once_internal(aas_json_override)
        for _ in range(interval_sec):
            if _stop_event.is_set():
                break
            time.sleep(1)

# --- API endpoints ---
@app.route("/api/se/health", methods=["GET"])
def health():
    return jsonify({"service": "smart_grid_services", "status": "ok"})

@app.route("/api/se/status", methods=["GET"])
def status():
    return jsonify(_status)

@app.route("/api/se/run-once", methods=["POST"])
def run_once():
    data = request.get_json(silent=True) or {}
    aas_path = data.get("aas_json_path")
    return jsonify(_run_once_internal(Path(aas_path) if aas_path else None))

@app.route("/api/se/start", methods=["POST"])
def start():
    global _loop_thread
    data = request.get_json(silent=True) or {}
    interval_sec = int(data.get("interval_sec", 30))
    aas_path = data.get("aas_json_path")

    with _loop_lock:
        if _status["running"]:
            return jsonify({"ok": False, "error": "Already running", "interval_sec": _status["interval_sec"]})
        _stop_event.clear()
        _loop_thread = threading.Thread(
            target=_loop,
            args=(interval_sec, Path(aas_path) if aas_path else None),
            daemon=True
        )
        _loop_thread.start()
        _status.update({"running": True, "interval_sec": interval_sec})
        logger.info(f"Started SE scheduler every {interval_sec}s")
        return jsonify({"ok": True, "running": True, "interval_sec": interval_sec})

@app.route("/api/se/stop", methods=["POST"])
def stop():
    with _loop_lock:
        if not _status["running"]:
            return jsonify({"ok": False, "error": "Not running"})
        _stop_event.set()
        _status.update({"running": False, "interval_sec": None})
        logger.info("Stopped SE scheduler.")
        return jsonify({"ok": True, "stopped": True})

# --- Entry point ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
