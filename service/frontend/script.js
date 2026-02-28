let currentMode = 'none';
let cameraStream = null;
let currentBlob = null;
let currentMongoId = null;
let debounceTimer = null;
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

// Debounce function (300ms delay)
function debounce(func, delay) {
    return function(...args) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => func.apply(this, args), delay);
    };
}

// Initialize search suggestions
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-snake');
    if (searchInput) {
        // Input event for suggestions (debounced)
        searchInput.addEventListener('input', debounce(handleSearchInput, 300));
        // Handle selection (when user picks from datalist)
        searchInput.addEventListener('change', handleSearchSelect);
    }
    
    // Save card button
    const saveBtn = document.getElementById('btnSaveCard');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveCardAsImage);
    }
});

async function handleSearchInput(e) {
    const query = e.target.value.trim();
    const datalist = document.getElementById('snake-suggestions');
    
    // Clear and hide if query is too short
    if (query.length < 2) {
        if (datalist) datalist.innerHTML = '';
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/search-suggestions?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        
        // Populate datalist with options
        if (datalist) {
            datalist.innerHTML = '';
            if (data.suggestions && data.suggestions.length > 0) {
                data.suggestions.forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    datalist.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Search error:', error);
        if (datalist) datalist.innerHTML = '';
    }
}

async function handleSearchSelect(e) {
    let selectedName;
    if (typeof e === 'string') {
        selectedName = e;
    } else {
        selectedName = e.target.value;
        if (!selectedName) return;
        e.target.value = selectedName;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/wiki-info?name=${encodeURIComponent(selectedName)}`);
        
        if (response.status === 404) {
            alert('ไม่พบข้อมูลประวัติงู โปรดเลือกจากรายชื่อที่แนะนำ');
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const wikiData = await response.json();
        
        document.getElementById('resSnake').innerText = selectedName;
        document.getElementById('resConf').innerText = "ค้นหาด้วยชื่อ";
        document.getElementById('resThai').innerText = wikiData.thai || selectedName;
        document.getElementById('resDanger').innerText = wikiData.danger || "Unknown";
        document.getElementById('resAid').innerText = wikiData.aid || "-";
        document.getElementById('resMorphology').innerText = wikiData.morphology || "-";
        document.getElementById('resWarning').style.display = 'none';
        document.getElementById('feedbackSection').style.display = 'none';
        document.getElementById('resSnakeImg').style.display = 'none';
        document.getElementById('btnSaveCard').style.display = 'none';
        
        // Clear datalist
        const datalist = document.getElementById('snake-suggestions');
        if (datalist) datalist.innerHTML = '';
        
        const dangerEl = document.getElementById('resDanger');
        const dangerText = wikiData.danger || "";
        
        if (dangerText.includes('ไม่มีพิษ')) {
            dangerEl.style.color = '#28a745';
            dangerEl.style.fontWeight = 'bold';
        } else if (dangerText.includes('พิษ')) {
            dangerEl.style.color = '#dc3545';
            dangerEl.style.fontWeight = 'bold';
        } else {
            dangerEl.style.color = 'inherit';
            dangerEl.style.fontWeight = 'normal';
        }
        
        els.resultBox.style.display = 'block';
        document.getElementById('resTimestamp').innerText = `ค้นหาเมื่อ: ${new Date().toLocaleString('th-TH')}`;
        currentMongoId = null;
    } catch (error) {
        console.error('Search select error:', error);
        alert('ไม่พบข้อมูลประวัติงู โปรดเลือกจากรายชื่อที่แนะนำ');
    }
}

async function handleSearchSelectDirect(selectedName) {
    await handleSearchSelect(selectedName);
}

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
        console.log("ข้อมูลจาก Backend:", data);
        
        if (data.status === 'success') {
            const snakeName = data.prediction?.class_name || "Unknown";
            const confidenceVal = data.confidence ?? ((data.prediction?.confidence || 0) * 100);
            const mongoId = data.mongo_id || null;
            const snakeIdentifier = data.snake_identifier || snakeName;
            
            document.getElementById('resSnake').innerText = snakeName;
            document.getElementById('resConf').innerText = confidenceVal.toFixed(1) + "%";
            
            const snakeImg = document.getElementById('resSnakeImg');
            snakeImg.src = els.imgPreview.src;
            snakeImg.style.display = 'block';
            
            document.getElementById('resThai').innerText = "กำลังโหลด...";
            document.getElementById('resDanger').innerText = "กำลังโหลด...";
            document.getElementById('resAid').innerText = "กำลังโหลด...";
            document.getElementById('resMorphology').innerText = "กำลังโหลด...";
            
            document.getElementById('resDanger').classList.remove('danger-high');

            const warningEl = document.getElementById('resWarning');
            if (confidenceVal < 50) {
                warningEl.innerText = "AI ไม่แน่ใจในผลลัพธ์ โปรดระมัดระวัง";
                warningEl.style.display = 'block';
            } else {
                warningEl.style.display = 'none';
            }

            currentMongoId = mongoId;
            document.getElementById('feedbackSection').style.display = 'block';
            document.getElementById('feedbackText').value = '';
            document.getElementById('btnSaveCard').style.display = 'block';
            document.getElementById('resTimestamp').innerText = `สแกนเมื่อ: ${new Date().toLocaleString('th-TH')}`;

            els.resultBox.style.display = 'block';
            
            loadWikiInfo(snakeIdentifier);
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

async function submitFeedback() {
    const feedbackText = document.getElementById('feedbackText').value.trim();
    
    if (!feedbackText) {
        return alert("กรุณากรอกข้อเสนอแนะก่อนครับ");
    }
    
    if (!currentMongoId) {
        return alert("ไม่พบ mongo_id กรุณาสแกนใหม่อีกครั้ง");
    }
    
    const API_URL = 'http://localhost:5000/feedback';
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id_mongo: currentMongoId,
                feedback: feedbackText
            })
        });
        
        if (response.ok) {
            alert("ขอบคุณสำหรับข้อเสนอแนะ!");
            document.getElementById('feedbackSection').style.display = 'none';
        } else {
            throw new Error("Failed to submit feedback");
        }
    } catch (error) {
        console.error(error);
        alert("เกิดข้อผิดพลาดในการส่งข้อเสนอแนะ: " + error.message);
    }
}

async function loadWikiInfo(snakeIdentifier) {
    const GATEWAY_URL = 'http://localhost:5000';
    
    try {
        const wikiResponse = await fetch(`${GATEWAY_URL}/wiki-info/${encodeURIComponent(snakeIdentifier)}`);
        
        if (!wikiResponse.ok) {
            throw new Error("Wiki fetch failed");
        }
        
        const wikiData = await wikiResponse.json();
        
        document.getElementById('resThai').innerText = wikiData.thai || "ไม่ทราบชื่อ";
        document.getElementById('resDanger').innerText = wikiData.danger || "Unknown";
        document.getElementById('resAid').innerText = wikiData.aid || "-";
        document.getElementById('resMorphology').innerText = wikiData.morphology || "-";
        
        const dangerEl = document.getElementById('resDanger');
        const dangerText = wikiData.danger || "";
        
        if (dangerText.includes('ไม่มีพิษ')) {
            dangerEl.style.color = '#28a745';
            dangerEl.style.fontWeight = 'bold';
        } else if (dangerText.includes('พิษ')) {
            dangerEl.style.color = '#dc3545';
            dangerEl.style.fontWeight = 'bold';
        } else {
            dangerEl.style.color = 'inherit';
            dangerEl.style.fontWeight = 'normal';
        }
        
    } catch (error) {
        console.error("Wiki load error:", error);
        document.getElementById('resThai').innerText = "ไม่สามารถโหลดข้อมูลได้";
        document.getElementById('resDanger').innerText = "-";
        document.getElementById('resAid').innerText = "-";
        document.getElementById('resMorphology').innerText = "-";
    }
}

async function saveCardAsImage() {
    const resultBox = document.getElementById('resultBox');
    const saveBtn = document.getElementById('btnSaveCard');
    const feedbackSection = document.getElementById('feedbackSection');
    const snakeName = document.getElementById('resSnake').innerText;
    
    if (!resultBox || !snakeName) {
        return alert("ไม่พบผลการสแกน");
    }
    
    try {
        saveBtn.style.display = 'none';
        feedbackSection.style.display = 'none';
        
        const canvas = await html2canvas(resultBox, {
            scale: 2,
            useCORS: true
        });
        
        const dataUrl = canvas.toDataURL('image/png');
        
        const link = document.createElement('a');
        link.download = `SnakeGuard_${snakeName}.png`;
        link.href = dataUrl;
        link.click();
        
    } catch (error) {
        console.error('Save image error:', error);
        alert("เกิดข้อผิดพลาดในการบันทึกรูปภาพ: " + error.message);
    } finally {
        saveBtn.style.display = 'block';
        if (currentMongoId) {
            feedbackSection.style.display = 'block';
        }
    }
}
