# 🔒 IoT Device Security System (CNS Final Project)

### Secure Raspberry Pi Telemetry • Encrypted Uploads • Rate Limiting • Device Blocking • ML-Based False Data Detection

---

## 📍 Overview  
This project is built for the **Computer & Network Security (CNS)** course.  
It demonstrates how to secure an IoT device (Raspberry Pi) sending important telemetry to the cloud.

The Raspberry Pi counts **people entering and exiting** a location and uploads this data to Firebase through a **secure Cloud Function**.  
The system ensures:

- data cannot be spoofed  
- packets cannot be replayed  
- attackers cannot flood the server  
- false values cannot be injected  
- compromised devices are automatically blocked  

This is a full **IoT → Security Layer → Cloud** pipeline.

---

# 🚀 Core Security Features

## 🔐 1. Encrypted Pi → Cloud Upload  
The Raspberry Pi sends encrypted logs using:

### ✔ XOR Encryption (Lightweight)  
- Very fast  
- Suitable for IoT  
- Works well with simple strings  
- Adds obfuscation + basic confidentiality  

### ✔ HEX Encoding  
Encrypted text is encoded to HEX before transmission so HTTP cannot break the payload.

### Payload Before Encryption:
```json
{
  "deviceId": "pi001",
  "entered": 1,
  "exited": 0,
  "timestamp": 1730000000
}


2. Firebase Cloud Function (Main Security Layer)
All Pi uploads go to:
https://<region>-smartbus.cloudfunctions.net/iotUpload


The Cloud Function performs the following security checks:
✔ 1. Decryption
XOR decryption
HEX decode
JSON parse validation
Invalid payload → rejected immediately.
✔ 2. Timestamp Freshness (Anti-Replay)
Rejects any packet older than:
> 5 seconds drift


3. Rate Limiting
Each device can only send:
15 requests per minute
If exceeded → flagged → blocked on repeated violations.

4. Value Validation
Accept only logical values:
entered >= 0
exited >= 0
no huge numbers
no negative inputs
This stops attackers from injecting fake data.
✔ 5. ML-Based Anomaly Detection
A lightweight Isolation Forest model checks:
spikes
abnormal patterns
unusual values
bot-like repeating patterns
The Pi itself sends clean data, so ML helps catch attacker scripts trying to poison logs.
✔ 6. Device Blocking System
If a device:
fails validation too often
floods requests
sends suspicious ML patterns
It is automatically placed into:
/devices/{deviceId}/status = "blocked"
Blocked devices are denied until manually unblocked

3. Raspberry Pi Device Logic
The Raspberry Pi does all counting:
✔ Counts entered and exited
from your YOLO tracking logic
keeps memory of tracking IDs
calculates increments
sends only the delta values
✔ Sends data every 5 seconds
Runs a small Flask or Python script like:
payload = {
  "deviceId": DEVICE,
  "entered": entered,
  "exited": exited,
  "timestamp": int(time.time())
}
encrypted = xor_encrypt(json.dumps(payload), KEY)
Uploads via:
requests.post(CLOUD_ENDPOINT, json={"data": encrypted})
📡 Firebase Data Layout
/iot_data/{deviceId}/logs/{logId}
    entered:
    exited:
    timestamp:

/devices/{deviceId}/status
/devices/{deviceId}/lastActive
/blocked_history/{entryId}
🔧 System Architecture
[Raspberry Pi]
 - YOLO counting
 - XOR encryption
 - HEX encoding
 - POST request
       |
       v
[Cloud Function Security Layer]
 - decrypt
 - validate
 - rate limit
 - check timestamp
 - ML anomaly detection
 - block device if needed
       |
       v
[Firebase Realtime Database]
 - stores only valid logs


## 🎥 Project Demo Video

[![Watch the Demo](https://img.youtube.com/vi/8OjqJszHSk4/maxresdefault.jpg)](https://youtu.be/8OjqJszHSk4)

> Click the thumbnail to watch the full demo video on YouTube.

