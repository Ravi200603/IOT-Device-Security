from flask import Flask, request, jsonify
import requests
import time
import threading
import json

# =============================
# CONFIG
# =============================
DEVICE_ID = "bus001"
CLOUD_FN = "https://iotupload-n47mkff2za-uc.a.run.app"

# CURRENT VALUES (NOT CUMULATIVE, NOT DELTA)
people_entered = 0
people_exited = 0
current_on_bus = 0

UPLOAD_INTERVAL = 1

app = Flask(__name__)

# =============================
# XOR ENCRYPTION
# =============================
def xor_encrypt(text, key):
    return bytes([ord(c) ^ key for c in text])

def hex_encode(b):
    return b.hex().upper()

# =============================
# BUILD ENCRYPTED PAYLOAD
# =============================
def build_encrypted_payload():
    ts = int(time.time())
    key_id = ts // 600
    enc_key = (key_id % 200) + 20

    data = {
        "deviceId": DEVICE_ID,
        "timestamp": ts,
        "keyId": key_id,
        "payload": {
            "peopleEntered": int(people_entered),   # SNAPSHOT
            "peopleExited": int(people_exited),     # SNAPSHOT
        }
    }

    print("\n========== PLAINTEXT PAYLOAD ==========")
    print(data)

    plain_json = json.dumps(data, separators=(",", ":"))
    encrypted_bytes = xor_encrypt(plain_json, enc_key)
    encrypted_hex = hex_encode(encrypted_bytes)

    return {
        "deviceId": DEVICE_ID,
        "keyId": key_id,
        "encrypted": encrypted_hex
    }

# =============================
# MAC → PI UPDATE API
# =============================
@app.route("/update", methods=["POST"])
def update_counts():
    global people_entered, people_exited, current_on_bus

    body = request.json
    if not body:
        return jsonify({"error": "No JSON data"}), 400

    # REPLACE values → not cumulative, not delta
    people_entered = int(body.get("peopleEntered", people_entered))
    people_exited = int(body.get("peopleExited", people_exited))

    

    print(f"[PI] STATE UPDATED → Entered={people_entered}, Exited={people_exited}")

    return jsonify({"status": "ok"}), 200

# =============================
# PERIODIC UPLOAD LOOP
# =============================
def upload_loop():
    while True:
        try:
            payload = build_encrypted_payload()
            r = requests.post(CLOUD_FN, json=payload, timeout=5)
            print(f"[UPLOAD] Status={r.status_code} | Response={r.text}")

        except Exception as e:
            print("[UPLOAD ERROR]", e)

        time.sleep(UPLOAD_INTERVAL)

# =============================
# MAIN LAUNCH
# =============================
if __name__ == "__main__":
    print("[PI] SmartBus Device Running…")
    threading.Thread(target=upload_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
