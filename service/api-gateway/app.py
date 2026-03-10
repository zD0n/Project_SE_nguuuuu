import os
import requests
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, TimeoutError

app = Flask(__name__)
CORS(app)

# URLs ของแต่ละ Service ตามโครงสร้างโปรเจกต์
S2_URL = os.environ.get('S2_URL', 'http://image-storage:5002/upload')
S3_URL = os.environ.get('S3_URL', 'http://ai-service:5001/predict')
S4_URL = os.environ.get('S4_URL', 'http://encyclopedia:8000')
S4_INFO_URL = os.environ.get('S4_INFO_URL', 'http://encyclopedia:8000/info')
S5_URL = os.environ.get('S5_URL', 'http://log-storage:3350/log')
S5_FEEDBACK_URL = os.environ.get('S5_FEEDBACK_URL', 'http://log-storage:3350/feedback')

# Timeout settings
SERVICE_TIMEOUT = 5
AI_TIMEOUT = 10

# Map AI common names to Wiki database identifiers
COMMON_TO_SCIENTIFIC = {
    "Vine Snake": "Ahaetulla nasuta",
    "Whip Snake": "Ahaetulla pulverulenta",
    "Krait": "Bungarus fasciatus",
    "Golden Tree": "Chrysopelea ornata",
    "Russell Viper": "Daboia russelii",
    "Painted Bronzeback": "Dendrelaphis pictus",
    "Red-tailed Racer": "Gonyosoma albicarcen",
    "Sea Krait": "Laticauda colubrina",
    "Wolf Snake": "Lycodon aulicus",
    "Monocled Cobra": "Naja kaouthia",
    "King Cobra": "Ophiophagus hannah",
    "Protobothrops": "Protobothrops kelom",
    "Mock Viper": "Psammodynastes pulverulentus",
    "Python": "Python bivittatus",
    "Red-necked": "Rhabdophis subminiatus",
    "Bamboo Viper": "Trimeresurus albus",
    "Checkered Keelback": "Xenochrophis flavipunctatus"
}

def transform_wiki_response(wiki_data):
    """Transform Wiki response to match Frontend expectations"""
    if not wiki_data or isinstance(wiki_data, dict) and "error" in wiki_data:
        return {"thai": "ไม่ทราบชื่อ", "danger": "Unknown", "aid": "-", "morphology": "-"}
    
    return {
        "thai": wiki_data.get("name_th", "ไม่ทราบชื่อ"),
        "danger": wiki_data.get("venomous", wiki_data.get("group", "Unknown")),
        "aid": wiki_data.get("first_aid_th", "-"),
        "morphology": wiki_data.get("morphology", "-")
    }

def get_snake_identifier(common_name):
    """Get database identifier from AI prediction"""
    return COMMON_TO_SCIENTIFIC.get(common_name, common_name)

def send_log_background(data):
    """ส่ง Log ไปที่ S5 แบบเบื้องหลัง เพื่อเพิ่มความเร็วในการตอบสนอง"""
    try:
        requests.post(S5_URL, json=data, timeout=SERVICE_TIMEOUT)
    except Exception as e:
        print(f"Failed to send log: {e}")

def fetch_wiki_background(snake_name, mongo_id):
    """ดึงข้อมูล Wiki แบบ background และส่ง log"""
    try:
        db_identifier = get_snake_identifier(snake_name)
        wiki_res = requests.get(f"{S4_INFO_URL}/{db_identifier}", timeout=SERVICE_TIMEOUT)
        wiki_data = wiki_res.json() if wiki_res.status_code == 200 else {}
    except Exception as e:
        print(f"Wiki fetch error: {e}")
        wiki_data = {}

def call_service(url, files=None, method='POST', timeout=10, params=None):
    """ฟังก์ชันกลางสำหรับติดต่อ Microservices อื่นๆ"""
    try:
        if method == 'POST':
            resp = requests.post(url, files=files, params=params, timeout=timeout)
        else:
            resp = requests.get(url, params=params, timeout=timeout)
        return resp.json()
    except Exception as e:
        print(f"Service Error at {url}: {e}")
        return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/scan', methods=['POST'])
def scan():
    img_bytes = request.data 
    
    if not img_bytes:
        return jsonify({"error": "No data received"}), 400

    filename = request.headers.get('X-File-Name', 'uploaded_snake.jpg')
    content_type = 'image/jpeg'

    payload = {'file': (filename, img_bytes, content_type)}

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_s2 = executor.submit(call_service, S2_URL, files=payload, timeout=SERVICE_TIMEOUT)
        future_s3 = executor.submit(call_service, S3_URL, files=payload, timeout=AI_TIMEOUT)

        try:
            storage_res = future_s2.result(timeout=SERVICE_TIMEOUT) or {"url": "", "mongo_id": ""}
        except TimeoutError:
            storage_res = {"url": "", "mongo_id": ""}
        
        try:
            ai_res = future_s3.result(timeout=AI_TIMEOUT) or {"class_name": "Unknown", "confidence": 0.0}
        except TimeoutError:
            ai_res = {"class_name": "Unknown", "confidence": 0.0}

    snake_name = ai_res.get('class_name', 'Unknown')
    confidence = ai_res.get('confidence', 0)
    mongo_id = storage_res.get("mongo_id") or storage_res.get("id", "")
    
    log_payload = {
        "id_mongo": mongo_id,
        "id_snake": snake_name,
        "confi": round(confidence * 100, 2)
    }
    threading.Thread(target=send_log_background, args=(log_payload,)).start()
    
    threading.Thread(target=fetch_wiki_background, args=(snake_name, mongo_id)).start()

    return jsonify({
        "status": "success",
        "image_url": storage_res.get("url", ""),
        "mongo_id": mongo_id,
        "prediction": ai_res,
        "confidence": round(confidence * 100, 2),
        "snake_identifier": get_snake_identifier(snake_name)
    })

@app.route('/wiki-info', methods=['GET'])
@app.route('/wiki-info/<path:snake_name>', methods=['GET'])
def wiki_info(snake_name=None):
    if snake_name:
        input_name = snake_name.strip()
    else:
        input_name = request.args.get('name', '').strip()
    
    if not input_name:
        return jsonify({"error": "name is required"}), 400
    
    try:
        db_identifier = get_snake_identifier(input_name)
        print(f"[wiki-info] Input: {input_name} -> DB Identifier: {db_identifier}", flush=True)
        wiki_res = requests.get(f"{S4_INFO_URL}/{db_identifier}", timeout=SERVICE_TIMEOUT)
        print(f"[wiki-info] Encyclopedia response: {wiki_res.status_code}", flush=True)
        
        if wiki_res.status_code != 200:
            return jsonify({"thai": "ไม่ทราบชื่อ", "danger": "Unknown"}), 404
            
        return jsonify(transform_wiki_response(wiki_res.json()))
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/search-suggestions', methods=['GET'])
def search_suggestions():
    q = request.args.get("q", "").strip()
    
    if not q or len(q) < 2:
        return jsonify({"suggestions": []}), 200
    
    try:
        print(f"[search-suggestions] Calling Encyclopedia: {S4_URL}/suggest?q={q}", flush=True)
        wiki_res = requests.get("http://encyclopedia:8000/suggest", params={"q": q, "limit": 5}, timeout=5)
        print(f"[search-suggestions] Encyclopedia response status: {wiki_res.status_code}", flush=True)
        
        if wiki_res.status_code == 200:
            return jsonify(wiki_res.json()), 200
        else:
            print(f"[search-suggestions] Encyclopedia returned {wiki_res.status_code}: {wiki_res.text}", flush=True)
            return jsonify({"suggestions": []}), 200
    except Exception as e:
        print(f"[search-suggestions] Error connecting to Encyclopedia: {e}", flush=True)
        return jsonify({"suggestions": []}), 200

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    
    if not data or not data.get('id_mongo') or not data.get('feedback'):
        return jsonify({"error": "id_mongo and feedback are required"}), 400
    
    try:
        resp = requests.post(S5_FEEDBACK_URL, json=data, timeout=SERVICE_TIMEOUT)
        if resp.status_code == 200:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"error": "Failed to save feedback"}), resp.status_code
    except Exception as e:
        print(f"Feedback Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
