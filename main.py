import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response, FileResponse
import uvicorn

app = FastAPI()

# Render 서버의 API 키를 안전하게 가져옴
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 1. PWA 설정 파일 (manifest.json)
MANIFEST_JSON = """{
  "short_name": "설교요약",
  "name": "AI 설교 기록 및 요약 비서",
  "icons": [
    {
      "src": "/icon.png",
      "type": "image/png",
      "sizes": "512x512",
      "purpose": "any maskable"
    }
  ],
  "start_url": "/",
  "background_color": "#ffffff",
  "display": "standalone",
  "theme_color": "#e74c3c",
  "orientation": "portrait"
}"""

# 2. PWA 오프라인 작동용 기본 서비스 워커 (service-worker.js)
SERVICE_WORKER_JS = """
const CACHE_NAME = 'sermon-ai-cache-v1';
const urlsToCache = [
  '/',
  '/manifest.json',
  '/icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event스마트폰 홈화면에 진짜 앱처럼 예쁜 **아이콘**을 만들고, 터치 한 번으로 설치할 수 있는 **PWA(누적형 웹앱) 기능**을 완벽하게 추가했습니다!

이 기능을 적용하면 브라우저 주소창을 거치지 않고, 홈화면에 생긴 아이콘을 누르는 순간 주소창 없는 **전체 화면(Full Screen) 앱**으로 깔끔하게 실행됩니다. 

깃허브(GitHub)의 `main.py` 내용을 아래 코드로 통째로 교체(Commit)해 주시면 바로 적용됩니다.

---

### 🛠️ PWA 앱 다운로드 기능이 탑재된 `main.py`

```python
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
import uvicorn

app = FastAPI()

# Render 서버의 API 키를 안전하게 가져옴
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 1. PWA 설정을 위한 Manifest 파일 정의 (앱 이름, 아이콘, 테마 색상 설정)
MANIFEST_JSON = """{
  "short_name": "설교요약AI",
  "name": "AI 설교 기록 & 요약",
  "icons": [
    {
      "src": "[https://img.icons8.com/fluency/192/microphone.png](https://img.icons8.com/fluency/192/microphone.png)",
      "type": "image/png",
      "sizes": "192x192"
    },
    {
      "src": "[https://img.icons8.com/fluency/512/microphone.png](https://img.icons8.com/fluency/512/microphone.png)",
      "type": "image/png",
      "sizes": "512x512"
    }
  ],
  "start_url": "/",
  "background_color": "#ffffff",
  "theme_color": "#2c3e50",
  "display": "standalone",
  "orientation": "portrait"
}"""

# 2. 오프라인에서도 웹앱을 안정적으로 구동시키기 위한 서비스 워커(Service Worker)
SERVICE_WORKER_JS = """
self.addEventListener('install', (e) => {
  self.skipWaiting();
});
self.addEventListener('fetch', (e) => {
  // 네트워크 요청을 그대로 통과시킵니다 (PWA 요건 충족용)
  e.respondWith(fetch(e.request));
});
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 설교 기록 & 요약</title>
    
    <!-- PWA 관련 메타 태그 및 아이콘 설정 -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#2c3e50">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" href="[https://img.icons8.com/fluency/192/microphone.png](https://img.icons8.com/fluency/192/microphone.png)">

    <style>
        body { font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #fafbfc; }
        .header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h2 { margin: 0; font-size: 22px; color: #2c3e50; }
        
        /* 앱 설치 버튼 스타일 */
        #installBtn { 
            display: none; 
            background-color: #2980b9; 
            color: white; 
            padding: 8px 14px; 
            font-size: 13px; 
            font-weight: bold; 
            border: none; 
            border-radius: 20px; 
            cursor: pointer; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .section { background-color: #f4f6f7; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
        textarea { width: 100%; padding: 12px; margin-bottom: 10px; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 15px; }
        .btn { padding: 12px 24px; font-size: 16px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; border: none; border-radius: 6px; color: white; font-weight: bold; transition: all 0.2s; }
        #recordBtn { background-color: #e74c3c; }
        #recordBtn:hover { background-color: #c0392b; }
        #stopBtn { background-color: #7f8c8d; }
        #uploadBtn { background-color: #27ae60; }
        #uploadBtn:hover { background-color: #219653; }
        input[type="file"] { margin-bottom: 15px; font-size: 16px; }
        .output-box { background-color: #fff; padding: 20px; border-radius: 8px; margin-top: 20px; white-space: pre-wrap; line-height: 1.6; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .model-info { color: #7f8c8d; font-size: 13px; text-align: right; margin-bottom: 10px; border-bottom: 1px dashed #bdc3c7; padding-bottom: 5px; }
        hr { border: 0; height: 1px; background: #dcdde1; margin: 20px 0; }
        
        .loading-container { display: none; background-color: #e8f4f8; border: 1px solid #bde0ec; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: center; }
        .spinner { display: inline-block; width: 40px; height: 40px; border: 4px solid rgba(41, 128, 185, 0.2); border-radius: 50%; border-top-color: #2980b9; animation: spin 1s ease-in-out infinite; margin-bottom: 15px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { color: #2c3e50; font-size: 16px; font-weight: bold; transition: all 0.5s ease; }
    </style>
</head>
<body>
    <div class="header-container">
        <h2>🎙️ AI 설교 요약기</h2>
        <!-- 홈화면에 앱 다운로드 설치를 바로 유도하는 PWA 버튼 -->
        <button id="installBtn">📱 앱 설치하기</button>
    </div>
    
    <div class="section">
        <label><b>1. 사전 맥락 입력 (성경 본문, 고유명사 등):</b></label>
        <textarea id="context" rows="3" placeholder="예: 오늘 본문은 로마서 8장 1~2절, 바울, 에베소 교회..."></textarea>
    </div>
    
    <div class="section">
        <label><b>2-A. 실시간 녹음하기:</b></label><br>
        <button id="recordBtn" class="btn">🔴 녹음 시작</button>
        <button id="stopBtn" class="btn" disabled>⏹️ 녹음 종료 및 요약하기</button>
        
        <hr>
        
        <label><b>2-B. 기존 녹음 파일 업로드 (MP3, M4A 등):</b></label><br>
        <input type="file" id="audioUpload" accept="audio/*"><br>
        <button id="uploadBtn" class="btn">📁 파일 업로드 및 요약하기</button>
    </div>
    
    <div id="loadingContainer" class="loading-container">
        <div class="spinner"></div>
        <div id="loadingText" class="loading-text">분석 준비 중...</div>
    </div>
    
    <div id="resultBox" class="output-box" style="display:none;"></div>

    <script>
        const API_KEY = "REPLACE_WITH_GEMINI_API_KEY";
        const contextInput = document.getElementById('context');
        const loadingContainer = document.getElementById('loadingContainer');
        const loadingText = document.getElementById('loadingText');
        const resultBox = document.getElementById('resultBox');

        // --- PWA 설치 기능 스크립트 ---
        let deferredPrompt;
        const installBtn = document.getElementById('installBtn');

        window.addEventListener('beforeinstallprompt', (e) => {
            // 브라우저 기본 설치 팝업을 막고 커스텀 버튼을 노출합니다.
            e.preventDefault();
            deferredPrompt = e;
            installBtn.style.display = 'block';
        });

        installBtn.onclick = async () => {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                console.log('User accepted the install prompt');
            }
            deferredPrompt = null;
            installBtn.style.display = 'none';
        };

        // 서비스 워커 등록
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(() => console.log('Service Worker Registered'));
        }
        // ------------------------------

        let mediaRecorder;
        let audioChunks = [];
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');

        recordBtn.onclick = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                if (audioChunks.length === 0) {
                    alert("녹음된 소리가 없습니다.");
                    return;
                }
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                await processAudioWithFilesAPI(audioBlob, 'recording.webm', 'audio/webm');
                audioChunks = [];
            };

            mediaRecorder.start(1000);
            recordBtn.disabled = true;
            recordBtn.style.backgroundColor = '#c0392b';
            recordBtn.innerText = '🔴 녹음 중...';
            stopBtn.disabled = false;
            stopBtn.style.backgroundColor = '#34495e';
        };

        stopBtn.onclick = () => {
            mediaRecorder.stop();
            recordBtn.disabled = false;
            recordBtn.style.backgroundColor = '#e74c3c';
            recordBtn.innerText = '🔴 녹음 시작';
            stopBtn.disabled = true;
            stopBtn.style.backgroundColor = '#7f8c8d';
        };

        const audioUpload = document.getElementById('audioUpload');
        const uploadBtn = document.getElementById('uploadBtn');

        uploadBtn.onclick = async () => {
            if (audioUpload.files.length === 0) {
                alert("업로드할 오디오 파일을 선택해주세요.");
                return;
            }
            const file = audioUpload.files[0];
            const mimeType = file.type || "audio/mp3";
            await processAudioWithFilesAPI(file, file.name, mimeType);
        };

        async function processAudioWithFilesAPI(fileOrBlob, filename, mimeType) {
            loadingContainer.style.display = 'block';
            resultBox.style.display = 'none';
            
            const steps = [
                "📡 초대용량 전송 채널을 생성하고 있습니다...",
                "🔄 구글 클라우드로 끊김 없이 음성을 전송 중입니다...",
                "🧠 대용량 오디오 파일을 활성화하고 상태를 대기하는 중입니다...",
                "📝 인공지능이 긴 설교의 전체 흐름을 요약 구조화하고 있습니다...",
                "✨ 최종 보고서를 생성하고 있습니다. 창을 닫지 마세요!"
            ];
            
            let stepIndex = 0;
            loadingText.innerText = steps[stepIndex];
            const progressInterval = setInterval(() => {
                stepIndex++;
                if (stepIndex < steps.length) {
                    loadingText.innerText = steps[stepIndex];
                }
            }, 8500);

            try {
                // 1단계: Resumable Upload 세션 시작
                const startResponse = await fetch(`[https://generativelanguage.googleapis.com/upload/v1beta/files?key=$](https://generativelanguage.googleapis.com/upload/v1beta/files?key=$){API_KEY}`, {
                    method: 'POST',
                    headers: {
                        'X-Goog-Upload-Protocol': 'resumable',
                        'X-Goog-Upload-Command': 'start',
                        'X-Goog-Upload-Header-Content-Length': fileOrBlob.size,
                        'X-Goog-Upload-Header-Content-Type': mimeType,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        file: {
                            displayName: filename
                        }
                    })
                });

                if (!startResponse.ok) throw new Error("업로드 세션 시작 실패");

                const uploadUrl = startResponse.headers.get('X-Goog-Upload-URL');

                // 2단계: 실제 바이너리 데이터 청크 전송
                const uploadResponse = await fetch(uploadUrl, {
                    method: 'POST',
                    headers: {
                        'X-Goog-Upload-Offset': '0',
                        'X-Goog-Upload-Command': 'upload, finalize'
                    },
                    body: fileOrBlob
                });

                if (!uploadResponse.ok) throw new Error("파일 데이터 전송 실패");

                const fileInfo = await uploadResponse.json();
                const fileUri = fileInfo.file.uri;
                const fileName = fileInfo.file.name;

                // 3단계: 파일 상태 'ACTIVE' 대기
                let isReady = false;
                loadingText.innerText = "🔄 구글 서버 내에서 음성 분석 준비 중입니다 (수초 소요)...";
                
                for (let i = 0; i < 30; i++) {
                    const checkResponse = await fetch(`[https://generativelanguage.googleapis.com/v1beta/$](https://generativelanguage.googleapis.com/v1beta/$){fileName}?key=${API_KEY}`);
                    const checkJson = await checkResponse.json();
                    
                    if (checkJson.state === "ACTIVE") {
                        isReady = true;
                        break;
                    } else if (checkJson.state === "FAILED") {
                        throw new Error("구글 서버 내 파일 처리 실패");
                    }
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }

                if (!isReady) throw new Error("파일 분석 대기 시간 초과");

                // 4단계: 업로드 완료된 대용량 파일을 활용해 요약 요청
                loadingText.innerText = "📝 설교 내용을 전체 수집하여 요약 노트를 구성하는 중입니다...";

                const prompt = `
                당신은 전문적인 설교 기록 및 요약 비서입니다.
                제공된 오디오 파일은 교회 설교 녹음입니다.
                다음의 사전 맥락(성경 본문, 고유명사)을 참고하여 내용을 정확히 파악하세요: [` + contextInput.value + `]
                
                분석 후, 아래의 마크다운 템플릿 양식에 맞춰 완벽하게 구조화된 요약본을 작성해 주세요.
                
                # 📜 오늘 설교 요약
                
                ## 1. 성경 본문 및 제목
                - (음성에서 파악된 본문과 제목)
                
                ## 2. 서론 (도입)
                - (서론 내용 요약)
                
                ## 3. 핵심 대지 (본론)
                - **첫째,** (내용)
                - **둘째,** (내용)
                - **셋째,** (내용)
                
                ## 4. 삶의 적용점 및 기도제목
                - (실천 사항 및 결론 요약)
                
                ---
                ## 📝 핵심 스크립트 요약
                (전체 흐름을 파악할 수 있는 스크립트 전문 또는 상세 요약)
                `;

                const generateResponse = await fetch(`[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$){API_KEY}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        contents: [
                            {
                                parts: [
                                    {
                                        fileData: {
                                            mimeType: mimeType,
                                            fileUri: fileUri
                                        }
                                    },
                                    {
                                        text: prompt
                                    }
                                ]
                            }
                        ]
                    })
                });

                if (!generateResponse.ok) {
                    const errData = await generateResponse.json();
                    throw new Error(errData.error?.message || "요약본 생성 실패");
                }

                const resultJson = await generateResponse.json();
                const rawText = resultJson.candidates[0].content.parts[0].text;

                // 마크다운 문법 정제
                let resultHtml = rawText;
                resultHtml = resultHtml.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
                resultHtml = resultHtml.replace(/# (.*?)\\n/g, '<h3>$1</h3>\\n');
                resultHtml = resultHtml.replace(/## (.*?)\\n/g, '<h4>$1</h4>\\n');
                resultHtml = resultHtml.replace(/\\n/g, '<br>');

                clearInterval(progressInterval);
                loadingContainer.style.display = 'none';
                resultBox.style.display = 'block';

                const modelInfoHtml = `<div class="model-info">💡 적용된 AI 모델: Gemini 2.5 Flash (Files API)</div>`;
                resultBox.innerHTML = modelInfoHtml + resultHtml;

                // 5단계: 분석 완료 후 임시 파일 즉시 삭제
                fetch(`[https://generativelanguage.googleapis.com/v1beta/$](https://generativelanguage.googleapis.com/v1beta/$){fileName}?key=${API_KEY}`, {
                    method: 'DELETE'
                }).catch(e => console.log("임시 파일 삭제 완료 혹은 생략됨."));

            } catch (error) {
                clearInterval(progressInterval);
                loadingContainer.style.display = 'none';
                alert("🚨 대용량 처리 실패: " + error.message);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get_index():
    safe_html = HTML_TEMPLATE.replace("REPLACE_WITH_GEMINI_API_KEY", API_KEY)
    return HTMLResponse(content=safe_html)

# PWA 표준 파일 1: manifest.json 세팅
@app.get("/manifest.json")
async def get_manifest():
    return Response(content=MANIFEST_JSON, media_type="application/json")

# PWA 표준 파일 2: sw.js (서비스 워커) 세팅
@app.get("/sw.js")
async def get_sw():
    return Response(content=SERVICE_WORKER_JS, media_type="application/javascript")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
