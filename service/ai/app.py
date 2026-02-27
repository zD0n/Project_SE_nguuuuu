import io
import torch
import os
from flask import Flask, request, jsonify
from PIL import Image
import gdown
from rfdetr import RFDETRMedium

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

CLASS_ID_MAP = {
    25: "Vine Snake", 26: "Whip Snake", 99: "Krait", 135: "Golden Tree", 
    203: "Russell Viper", 215: "Painted Bronzeback", 302: "Red-tailed Racer", 
    368: "Sea Krait", 396: "Wolf Snake", 462: "Monocled Cobra", 497: "King Cobra", 
    560: "Protobothrops", 562: "Mock Viper", 603: "Python", 616: "Red-necked", 
    725: "Bamboo Viper", 758: "Checkered Keelback"
}

SORTED_IDS = sorted(CLASS_ID_MAP.keys())
CLASS_NAMES_LIST = [CLASS_ID_MAP[k] for k in SORTED_IDS]

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "checkpoint_best_ema.pth")

device = 'cpu'
model = RFDETRMedium(pretrain_weights=MODEL_PATH, num_classes=len(CLASS_NAMES_LIST), device=device)

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    try:
        file = request.files['file']
        image = Image.open(io.BytesIO(file.read())).convert("RGB")
        detections = model.predict(image, threshold=0.15)

        res = {"class_name": "Unknown", "confidence": 0.0, "bbox": []}
        
        if len(detections.confidence) > 0:
            idx = detections.confidence.argmax()
            class_idx = int(detections.class_id[idx])
            
            if class_idx < len(CLASS_NAMES_LIST):
                name = CLASS_NAMES_LIST[class_idx]
            else:
                name = f"Unknown ID:{class_idx}"

            res = {
                "class_name": name,
                "confidence": round(float(detections.confidence[idx]), 4),
                "bbox": [int(b) for b in detections.xyxy[idx].tolist()]
            }
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)