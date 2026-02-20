let currentMode = 'none';
let cameraStream = null;
let currentBlob = null;
const els = {
    placeholder: document.getElementById('placeholder'),
    imgPreview: document.getElementById('imagePreview'),
    vidPreview: document.getElementById('videoPreview'),
    btnCamera: document.getElementById('btnCamera'),
    btnScan: document.getElementById('btnScan'),
    btnText: document.getElementById('btnText'),
    loader: document.getElementById('loader'),
    resultBox: document.getElementById('resultBox'),
    canvas: document.getElementById('canvas')
};

// 1. ฟังก์ชันเมื่อเลือกไฟล์ (File Upload)
async function handleFileSelect(input) {
    if (input.files && input.files[0]) {
        stopCamera();
        
        const file = input.files[0];
        currentBlob = await file.arrayBuffer();
        
        const reader = new FileReader();
        reader.onload = (e) => {
            els.imgPreview.src = e.target.result;
            showPreview('image');
        };
        reader.readAsDataURL(file);
        
        currentMode = 'file';
        els.btnText.innerText = "Scan Image";
    }
}

// 2. ฟังก์ชันเปิด/ปิดกล้อง (Camera Toggle)
async function toggleCamera() {
    if (currentMode === 'camera') {
        stopCamera();
        resetUI();
    } else {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            els.vidPreview.srcObject = cameraStream;
            showPreview('video');
            
            currentMode = 'camera';
            els.btnCamera.classList.add('active');
            els.btnText.innerText = "Capture & Scan";
        } catch (err) {
            alert("ไม่สามารถเปิดกล้องได้: " + err.message);
        }
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    els.btnCamera.classList.remove('active');
}

// 3. ฟังก์ชันจัดการ Preview (Helper)
function showPreview(type) {
    els.placeholder.style.display = 'none';
    els.resultBox.style.display = 'none';
    
    if (type === 'image') {
        els.imgPreview.style.display = 'block';
        els.vidPreview.style.display = 'none';
    } else if (type === 'video') {
        els.imgPreview.style.display = 'none';
        els.vidPreview.style.display = 'block';
    }
}

function resetUI() {
    currentMode = 'none';
    els.placeholder.style.display = 'block';
    els.imgPreview.style.display = 'none';
    els.vidPreview.style.display = 'none';
    els.btnText.innerText = "Scan Now";
}

// 4. ฟังก์ชันฉลาด: ปุ่ม Scan เดียวทำได้หมด (Smart Scan)
async function handleSmartScan() {
    if (currentMode === 'none' && !currentBlob) {
        return alert("กรุณาเลือกรูปหรือเปิดกล้องก่อนครับ");
    }

    setLoading(true);

    try {
        if (currentMode === 'camera') {
            // 1. จับภาพจาก video ลง canvas
            els.canvas.width = els.vidPreview.videoWidth;
            els.canvas.height = els.vidPreview.videoHeight;
            const ctx = els.canvas.getContext('2d');
            ctx.drawImage(els.vidPreview, 0, 0);

            // 2. แปลงเป็น Blob (Bytes)
            const blob = await new Promise(r => els.canvas.toBlob(r, 'image/jpeg', 0.9));
            currentBlob = await blob.arrayBuffer();

            // 3. **โชว์ภาพที่ถ่าย (ตามโจทย์)** หยุดวิดีโอแล้วโชว์รูปนิ่งแทน
            els.imgPreview.src = URL.createObjectURL(blob);
            stopCamera();
            showPreview('image');
        }

        await sendToGateway(currentBlob);

    } catch (err) {
        console.error(err);
        alert("เกิดข้อผิดพลาด: " + err.message);
    } finally {
        setLoading(false);
        els.btnText.innerText = "Scan Again";
    }
}

// 5. ส่งข้อมูลไป API Gateway
async function sendToGateway(bytes) {
    // แบบที่ 1: สำหรับทดสอบบนคอมพิวเตอร์เครื่องนี้เท่านั้น (Localhost)
    const API_URL = 'http://localhost:5000/scan';

    // แบบที่ 2: สำหรับทดสอบบนมือถือ (ต้องใช้ IP เครื่องคอมฯ)
    // const API_URL = 'http://10.62.122.50:5000/scan'; 

    try {
        console.log(`Sending data to: ${API_URL}`);

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/octet-stream',
                'X-File-Name': 'capture.jpg'
            },
            body: bytes
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.status === 'success') {
            document.getElementById('resSnake').innerText = data.prediction.class_name;
            document.getElementById('resThai').innerText = data.info.thai;
            document.getElementById('resConf').innerText = (data.prediction.confidence * 100).toFixed(1) + "%";
            document.getElementById('resDanger').innerText = data.info.danger;
            document.getElementById('resAid').innerText = data.info.aid;
            
            const dangerEl = document.getElementById('resDanger');
            if(data.info.danger === 'High') dangerEl.classList.add('danger-high');
            else dangerEl.classList.remove('danger-high');

            els.resultBox.style.display = 'block';
        } else {
            throw new Error("API Error: " + JSON.stringify(data));
        }
    } catch (error) {
        console.error(error);
        alert(`เชื่อมต่อไม่ได้ (${API_URL})\nError: ${error.message}\n\nคำแนะนำ: ตรวจสอบว่ามือถือและคอมฯ ใช้วง Wi-Fi เดียวกัน หรือ IP ถูกต้องหรือไม่`);
    }
}

function setLoading(isLoading) {
    els.btnScan.disabled = isLoading;
    els.loader.style.display = isLoading ? 'block' : 'none';
    els.btnText.style.display = isLoading ? 'none' : 'block';
}