import time
import json
import requests

DEVICE_ID = "bus001"
CLOUD_FN = "https://iotupload-n47mkff2za-uc.a.run.app"

# =============================
# XOR ENCRYPTION (same as your PI)
# =============================
def xor_encrypt(text, key):
    return bytes([ord(c) ^ key for c in text])

def hex_encode(b):
    return b.hex().upper()

# =============================
# SEND ONE ABNORMAL PAYLOAD
# =============================
def send_abnormal(entered, exited):
    ts = int(time.time())
    key_id = ts // 600
    enc_key = (key_id % 200) + 20

    # Build abnormal payload
    payload_plain = {
        "deviceId": DEVICE_ID,
        "timestamp": ts,
        "keyId": key_id,
        "payload": {
            "peopleEntered": entered,
            "peopleExited": exited
        }
    }

    print("\n🔥 SENDING ABNORMAL PAYLOAD (PLAINTEXT)")
    print(payload_plain)

    plain_json = json.dumps(payload_plain, separators=(",", ":"))
    encrypted_bytes = xor_encrypt(plain_json, enc_key)
    encrypted_hex = hex_encode(encrypted_bytes)

    payload_encrypted = {
        "deviceId": DEVICE_ID,
        "keyId": key_id,
        "encrypted": encrypted_hex
    }

    # Upload to cloud
    r = requests.post(CLOUD_FN, json=payload_encrypted)
    print(f"➡ Uploaded | status={r.status_code} | response={r.text}")


# =============================
# MAIN — SEND DIFFERENT ATTACKS
# =============================
if __name__ == "__main__":
    print("🚨 ABNORMAL LOG SENDER (TEST MODE)")
    print("Sending 5 abnormal logs for ML testing...\n")

    abnormal_tests = [
        (200, 0),   # unrealistic high → suspicious-unrealistic
        (-5,  2),   # negative → suspicious-invalid-negative
        (50,  0),   # ML will detect → unusual-ml
        (1,  99),   # exit > enter → unusual-ml
        (300, 200)  # extreme values → suspicious-unrealistic
    ]

    for (ent, ext) in abnormal_tests:
        send_abnormal(ent, ext)
        time.sleep(3)  # wait before next attack

    print("\n✅ DONE — Check Firebase logs & ML flags.")
