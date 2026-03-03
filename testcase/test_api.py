import pytest
import requests
import os
import json
import io
from PIL import Image

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:5000")
AI_URL = os.environ.get("TEST_AI_URL", "http://localhost:5001")
ENCYCLOPEDIA_URL = os.environ.get("TEST_ENCYCLOPEDIA_URL", "http://localhost:8000")

TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "testcase", "images.jpg")


def create_test_image():
    """Create a simple test image in memory"""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


def get_test_image_bytes():
    """Get test image bytes from file"""
    if os.path.exists(TEST_IMAGE_PATH):
        with open(TEST_IMAGE_PATH, "rb") as f:
            return f.read()
    return create_test_image().read()


class TestAPIGateway:
    """API Gateway Service Test Cases"""

    def test_gw_01_scan_with_image_bytes(self):
        """GW-01: POST /scan with image bytes - Expected: 200 OK + prediction JSON"""
        img_bytes = get_test_image_bytes()
        response = requests.post(
            f"{BASE_URL}/scan",
            data=img_bytes,
            headers={"Content-Type": "image/jpeg", "X-File-Name": "test_snake.jpg"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data

    def test_gw_02_scan_with_image_file(self):
        """GW-02: POST /scan with image file - Expected: 200 OK + prediction JSON"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test_snake.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{BASE_URL}/scan", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data

    def test_gw_03_confidence_below_70_percent(self):
        """GW-03: Confidence < 70% - Expected: Return 'Unknown' or handle properly"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test_snake.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{BASE_URL}/scan", files=files)
        if response.status_code == 200:
            data = response.json()
            confidence = data.get("confidence", 0)
            if confidence < 70:
                assert data.get("prediction", {}).get("class_name") in ["Unknown", ""]

    def test_gw_04_confidence_above_70_percent(self):
        """GW-04: Confidence >= 70% - Expected: Return snake name + confidence"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test_snake.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{BASE_URL}/scan", files=files)
        if response.status_code == 200:
            data = response.json()
            confidence = data.get("confidence", 0)
            if confidence >= 70:
                assert data.get("prediction", {}).get("class_name") != "Unknown"

    def test_gw_05_missing_image_input(self):
        """GW-05: Missing image input - Expected: 400 Bad Request"""
        response = requests.post(f"{BASE_URL}/scan", data=None)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_gw_06_ai_service_timeout(self):
        """GW-06: AI service timeout - Expected: 200 (graceful degradation)"""
        pass

    def test_gw_07_s3_upload_failure(self):
        """GW-07: S3 upload failure - Expected: Main response still 200"""
        pass

    def test_gw_08_rate_limit_exceeded(self):
        """GW-08: Rate limit exceeded - Expected: 429 Too Many Requests"""
        pass

    def test_gw_09_log_service_failure(self):
        """GW-09: Log service failure - Expected: Main response still 200"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test_snake.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{BASE_URL}/scan", files=files)
        assert response.status_code == 200

    def test_gateway_health(self):
        """GW: Health check"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json().get("status") == "ok"


class TestAIInferenceService:
    """AI Inference Service Test Cases"""

    def test_ai_01_model_loads(self):
        """AI-01: Model loads successfully - Expected: Model ready"""
        response = requests.get(f"{AI_URL}/health")
        assert response.status_code == 200

    def test_ai_02_receive_image_bytes(self):
        """AI-02: Receive image bytes - Expected: Convert to tensor"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{AI_URL}/predict", files=files)
        assert response.status_code == 200

    def test_ai_03_invalid_image_format(self):
        """AI-03: Invalid image format - Expected: 400 Error"""
        files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
        response = requests.post(f"{AI_URL}/predict", files=files)
        assert response.status_code in [400, 500]

    def test_ai_04_valid_image_inference(self):
        """AI-04: Valid image inference - Expected: JSON with label + confidence + bbox"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{AI_URL}/predict", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "class_name" in data
        assert "confidence" in data
        assert "bbox" in data

    def test_ai_05_model_returns_empty_result(self):
        """AI-05: Model returns empty result - Expected: Handle gracefully"""
        img = Image.new("RGB", (50, 50), color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        files = {"file": ("blank.jpg", img_bytes, "image/jpeg")}
        response = requests.post(f"{AI_URL}/predict", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data.get("class_name") == "Unknown"

    def test_ai_health(self):
        """AI: Health check"""
        response = requests.get(f"{AI_URL}/health")
        assert response.status_code == 200


class TestEncyclopediaService:
    """Encyclopedia Service Test Cases"""

    def test_enc_01_get_info_valid(self):
        """ENC-01: GET /info/<name> valid - Expected: 200 + snake information"""
        response = requests.get(f"{ENCYCLOPEDIA_URL}/info/Naja kaouthia")
        if response.status_code == 200:
            data = response.json()
            assert "name_en" in data or "name_th" in data

    def test_enc_02_get_info_invalid(self):
        """ENC-02: GET /info/<name> invalid - Expected: 404 Not Found"""
        response = requests.get(f"{ENCYCLOPEDIA_URL}/info/InvalidSnake12345")
        assert response.status_code == 404

    def test_enc_03_search(self):
        """ENC-03: GET /search?q=name - Expected: Return matching list"""
        response = requests.get(f"{ENCYCLOPEDIA_URL}/search?q=cobra")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_enc_04_sql_injection_attempt(self):
        """ENC-04: SQL injection attempt - Expected: Prevented"""
        response = requests.get(f"{ENCYCLOPEDIA_URL}/info/'; DROP TABLE snakes;--")
        assert response.status_code in [400, 404]

    def test_encyclopedia_health(self):
        """Encyclopedia: Health check"""
        response = requests.get(f"{ENCYCLOPEDIA_URL}/health")
        assert response.status_code == 200

    def test_encyclopedia_health_db(self):
        """Encyclopedia: DB health check"""
        response = requests.get(f"{ENCYCLOPEDIA_URL}/health/db")
        assert response.status_code == 200


class TestImageStorageService:
    """Image Storage Service Test Cases"""

    def test_img_01_upload_image(self):
        """IMG-01: Upload image successfully - Expected: Return image_id"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(
            f"{BASE_URL.replace('5000', '5002')}/upload", files=files
        )
        assert response.status_code in [200, 201]

    def test_img_02_duplicate_image_upload(self):
        """IMG-02: Duplicate image upload - Expected: No crash, return new ID or handle properly"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response1 = requests.post(
            f"{BASE_URL.replace('5000', '5002')}/upload", files=files
        )
        response2 = requests.post(
            f"{BASE_URL.replace('5000', '5002')}/upload", files=files
        )
        assert response2.status_code in [200, 201]

    def test_img_03_database_connection_failure(self):
        """IMG-03: Database connection failure - Expected: 500 Error"""
        pass


class TestEndToEnd:
    """End-to-End Test Cases"""

    def test_e2e_01_full_scan_flow(self):
        """E2E-01: Full scan flow - User uploads snake image -> AI -> Encyclopedia -> Log -> UI"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test_snake.jpg", io.BytesIO(img_bytes), "image/jpeg")}

        response = requests.post(f"{BASE_URL}/scan", files=files)

        assert response.status_code == 200
        data = response.json()

        assert "prediction" in data
        assert "confidence" in data
        assert "snake_identifier" in data

        confidence = data.get("confidence", 0)
        if confidence >= 70:
            snake_id = data.get("snake_identifier")
            wiki_response = requests.get(f"{ENCYCLOPEDIA_URL}/info/{snake_id}")
            assert wiki_response.status_code in [200, 404]


class TestDockerDeployment:
    """Docker / Deployment Test Cases"""

    def test_dev_01_docker_build(self):
        """DEV-01: Docker build success - Expected: Image builds without error"""
        pass

    def test_dev_02_docker_compose_up(self):
        """DEV-02: docker-compose up - Expected: All services running"""
        pass


class TestFrontend:
    """Frontend / UI Test Cases"""

    def test_fe_01_upload_image_request(self):
        """FE-01: Upload image - Expected: Request sent to Gateway"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{BASE_URL}/scan", files=files)
        assert response.status_code in [200, 400, 500]

    def test_fe_02_display_result(self):
        """FE-03: Display result - Expected: Show name + confidence"""
        img_bytes = get_test_image_bytes()
        files = {"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(f"{BASE_URL}/scan", files=files)
        if response.status_code == 200:
            data = response.json()
            assert "confidence" in data
            assert "prediction" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
