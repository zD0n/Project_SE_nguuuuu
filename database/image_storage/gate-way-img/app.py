import os
import base64
from datetime import datetime, timezone

from flask import Flask, Blueprint, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId

# ---------- Config ----------
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)


api = Blueprint("api", __name__, url_prefix="/api")


def bytes_to_base64(data: bytes) -> str:
    # base64.b64encode: bytes -> base64 bytes -> str  :contentReference[oaicite:5]{index=5}
    return base64.b64encode(data).decode("utf-8")


def base64_to_bytes(b64: str) -> bytes:
    # base64.b64decode: base64 str -> bytes :contentReference[oaicite:6]{index=6}
    return base64.b64decode(b64.encode("utf-8"))


def allowed_file(filename: str | None) -> bool:
    if not filename:
        return False
    name = filename.lower()
    return any(name.endswith(ext) for ext in ALLOWED_EXT)


# ----------------Health Check-----------------------------
@app.get("/health")
def health():
    try:
        mongo.db.command("ping")
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}, 500


# ---------- 2) Upload image -> base64 -> MongoDB ----------
@app.post("/upload")
@api.post("/upload")
def upload_image():
    # ใช้ request.files สำหรับรับไฟล์ :contentReference[oaicite:7]{index=7}
    if "file" not in request.files:
        return jsonify({"error": "missing file field"}), 400

    f = request.files["file"]
    if not f or f.filename == "":
        return jsonify({"error": "empty filename"}), 400

    if not allowed_file(f.filename):
        return jsonify({"error": f"only allow {sorted(ALLOWED_EXT)}"}), 415

    raw = f.read()
    if not raw:
        return jsonify({"error": "empty file content"}), 400
    
    if len(raw) > MAX_FILE_SIZE:
        return jsonify({"error": f"file too large. max {MAX_FILE_SIZE // (1024*1024)}MB"}), 413

    b64 = bytes_to_base64(raw)

    doc = {
        "filename": f.filename,
        "content_type": f.mimetype,
        "base64": b64,
        "created_at": datetime.now(timezone.utc),
    }

    res = mongo.db.images.insert_one(doc)
    mongo_id = str(res.inserted_id)
    return jsonify(
        {
            "id": mongo_id,
            "mongo_id": mongo_id,
            "filename": doc["filename"],
            "content_type": doc["content_type"],
            "get_url": f"/api/images/{res.inserted_id}",
            "url": f"/api/images/{res.inserted_id}",
        }
    ), 201


# ---------- 3) Get base64 back ----------
@api.get("/images/<id>")
def get_image_base64(id: str):
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400

    # find_one :contentReference[oaicite:10]{index=10}
    doc = mongo.db.images.find_one({"_id": oid})
    if not doc:
        return jsonify({"error": "not found"}), 404

    return jsonify(
        {
            "id": str(doc["_id"]),
            "filename": doc.get("filename"),
            "content_type": doc.get("content_type"),
            "base64": doc.get("base64"),
            "created_at": doc.get("created_at").isoformat()
            if doc.get("created_at")
            else None,
        }
    )


app.register_blueprint(api)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5002"))
    app.run(host="0.0.0.0", port=port, debug=False)
