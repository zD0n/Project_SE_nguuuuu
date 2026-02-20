from flask import Flask, request, jsonify, render_template
import base64
import io
import os
from PIL import Image

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()

    if "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    # Decode base64 image
    header, encoded = data["image"].split(",", 1)
    image_bytes = base64.b64decode(encoded)

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    os.makedirs("uploads", exist_ok=True)
    save_path = "uploads/photo.jpg"
    image.save(save_path, "JPEG")

    return jsonify({
        "status": "success",
        "saved_to": save_path
    })

