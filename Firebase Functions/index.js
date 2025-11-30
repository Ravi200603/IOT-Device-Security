const { onRequest, onCall } = require("firebase-functions/v2/https");
const { onValueCreated } = require("firebase-functions/v2/database");
const admin = require("firebase-admin");
const cors = require("cors")({ origin: true });

admin.initializeApp();
const realtimeDB = admin.database();

/* -------------------------------------------------------------
   XOR DECRYPT
------------------------------------------------------------- */
function xorDecrypt(hexString, key) {
  const bytes = Buffer.from(hexString, "hex");
  let out = "";
  for (let i = 0; i < bytes.length; i++) {
    out += String.fromCharCode(bytes[i] ^ key);
  }
  return out;
}

/* -------------------------------------------------------------
   1) DEVICE UPLOAD
------------------------------------------------------------- */
exports.iotUpload = onRequest(async (req, res) => {
  return cors(req, res, async () => {
    try {
      if (req.method !== "POST")
        return res.status(405).send("Only POST allowed");

      const { deviceId, keyId, encrypted } = req.body || {};
      if (!deviceId || !keyId || !encrypted)
        return res.status(400).send("Missing fields");

      const ENC_KEY = (keyId % 200) + 20;
      const decrypted = xorDecrypt(encrypted, ENC_KEY);
      const data = JSON.parse(decrypted);

      const now = Math.floor(Date.now() / 1000);
      const ts = Number(data.timestamp);

      if (!ts || Math.abs(now - ts) > 120)
        return res.status(401).send("Clock drift too large");

      const statusRef = realtimeDB.ref(`IoT/status/${deviceId}`);
      const statusSnap = await statusRef.get();

      if (!statusSnap.exists()) {
        await statusRef.set({
          blocked: false,
          blockedReason: null,
          blockedAt: null,
          lastTimestamp: null,
          lastSeen: Date.now()
        });
      } else {
        await statusRef.update({ lastSeen: Date.now() });
      }

      await realtimeDB.ref(`IoT/logs/${deviceId}`).push({
        timestamp: ts,
        peopleEntered: Number(data.payload.peopleEntered),
        peopleExited: Number(data.payload.peopleExited),
        receivedAt: Date.now()
      });

      return res.status(200).send("OK");

    } catch (err) {
      console.error("UPLOAD ERROR:", err);
      return res.status(500).send("Server error");
    }
  });
});

/* -------------------------------------------------------------
   BLOCK DEVICE
------------------------------------------------------------- */
async function blockDevice(deviceId, reason) {
  await realtimeDB.ref(`IoT/status/${deviceId}`).update({
    blocked: true,
    blockedReason: reason,
    blockedAt: Date.now()
  });
}

/* -------------------------------------------------------------
   RATE LIMIT + DUPLICATE CHECK
------------------------------------------------------------- */
exports.rateLimitAndDupCheck = onValueCreated(
  "IoT/logs/{deviceId}/{logId}",
  async (event) => {
    const deviceId = event.params.deviceId;
    const log = event.data.val();
    if (!log || !log.timestamp) return;

    const ts = Number(log.timestamp);
    const statusRef = realtimeDB.ref(`IoT/status/${deviceId}`);
    const isBlocked = (await statusRef.child("blocked").get()).val();

    if (isBlocked === true) {
      await event.data.ref.remove();
      return;
    }

    const lastTs = (await statusRef.child("lastTimestamp").get()).val();

    if (lastTs === ts) {
      await blockDevice(deviceId, "Duplicate timestamp");
      await event.data.ref.remove();
      return;
    }

    await statusRef.child("lastTimestamp").set(ts);

    const oneMinAgo = ts - 60;

    const logsSnap = await realtimeDB
      .ref(`IoT/logs/${deviceId}`)
      .orderByChild("timestamp")
      .startAt(oneMinAgo)
      .get();

    const count = logsSnap.numChildren();

    if (count > 15) {
      await blockDevice(deviceId, "Too many logs per minute");
      await event.data.ref.remove();
      return;
    }

    console.log(`OK ${deviceId} → last_min_logs=${count}`);
  }
);

/* -------------------------------------------------------------
   MANUAL UNBLOCK
------------------------------------------------------------- */
exports.unblockDevice = onCall(async (req) => {
  const deviceId = req.data.deviceId;

  await realtimeDB.ref(`IoT/status/${deviceId}`).update({
    blocked: false,
    blockedReason: null,
    lastTimestamp: null
  });

  return { success: true };
});