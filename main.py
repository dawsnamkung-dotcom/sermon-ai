import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
import uvicorn

app = FastAPI()

API_KEY = os.environ.get("GEMINI_API_KEY", "")

MANIFEST_JSON = """{
  "short_name": "설교요약AI",
  "name": "AI 설교 기록 & 요약 비서",
  "icons": [
    {
      "src": "https://img.icons8.com/fluency/192/microphone.png",
      "type": "image/png",
      "sizes": "192x192"
    },
    {
      "src": "https://img.icons8.com/fluency/512/microphone.png",
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

SERVICE_WORKER_JS = """
self.addEventListener('install', (e) => {
  self.skipWaiting();
});
self.addEventListener('fetch', (e) => {
  e.respondWith(fetch(e.request));
});
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>설교 기록 & 요약 웹앱</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#2c3e50">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" href="https://img.icons8.com/fluency/192/microphone.png">

    <style>
        body { font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h2 { margin: 0; font-size: 20px; }
        
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
            transition: background-color 0.2s;
        }
        #installBtn:hover { background-color: #1f618d; }

        .section { background-color: #f4f6f7; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        textarea { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; border: 1px solid #bdc3c7; border-radius: 4px; }
        .btn { padding: 12px 24px; font-size: 16px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; border: none; border-radius: 5px; color: white; font-weight: bold; }
        #recordBtn { background-color: #e74c3c; }
        #stopBtn { background-color: #7f8c8d; }
        #toggleScriptBtn { background-color: #34495e; display: none; }
        #uploadBtn { background-color: #27ae60; }
        input[type="file"] { margin-bottom: 15px; font-size: 16px; }
        
        .live-script-box { 
            display: none; 
            background-color: #ffffff; 
            border: 2px dashed #3498db; 
            border-radius: 8px; 
            padding: 15px; 
            margin-top: 15px; 
            max-height: 180px; 
            overflow-y: auto; 
            font-size: 14px; 
            line-height: 1.6; 
            color: #2c3e50; 
        }
        .live-script-header { font-weight: bold; color: #2980b9; margin-bottom: 8px; font-size: 13px; }
        .interim-text { color: #95a5a6; }

        /* 결과 박스 및 복사 버튼 스타일 */
        .result-container { margin-top: 20px; display: none; }
        .result-header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .copy-btn { 
            background-color: #8e44ad; 
            color: white; 
            padding: 8px 16px; 
            font-size: 14px; 
            font-weight: bold; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
            transition: all 0.2s; 
        }
        .copy-btn:hover { background-color: #732d91; }
        .copy-btn.copied { background-color: #27ae60; }

        .output-box { background-color: #fff; padding: 20px; border-radius: 8px; white-space: pre-wrap; line-height: 1.6; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .model-info { color: #7f8c8d; font-size: 13px; text-align: right; margin-bottom: 10px; border-bottom: 1px dashed #bdc3c7; padding-bottom: 5px; }
        hr { border: 0; height: 1px; background: #dcdde1; margin: 20px 0; }
        
        .loading-container { display: none; background-color: #e8f4f8; border: 1px solid #bde0ec; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: center; }
        .spinner { display: inline-block; width: 40px; height: 40px; border: 4px solid rgba(41, 128, 185, 0.2); border-radius: 50%; border-top-color: #2980b9; animation: spin 1s ease-in-out infinite; margin-bottom: 15px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { color: #2c3e50; font-size: 16px; font-weight: bold; transition: all 0.5s ease; }
        .timer-badge { display: inline-block; margin-top: 8px; font-size: 13px; color: #7f8c8d; }
        .status-badge { font-size: 12px; color: #27ae60; margin-left: 5px; font-weight: normal; }
    </style>
</head>
<body>
    <div class="header-container">
        <h2>🎙️ AI 설교 요약 (백그라운드 & 100MB+ 지원)</h2>
        <button id="installBtn">📱 앱 다운로드</button>
    </div>
    
    <div class="section">
        <label><b>1. 사전 맥락 입력 (성경 본문, 고유명사 등):</b></label>
        <textarea id="context" rows="3" placeholder="예: 오늘 본문은 로마서 8장 1~2절, 바울, 에베소 교회..."></textarea>
    </div>
    
    <div class="section">
        <label><b>2-A. 실시간 녹음하기:</b></label><br>
        <button id="recordBtn" class="btn">🔴 녹음 시작</button>
        <button id="stopBtn" class="btn" disabled>⏹️ 녹음 종료 및 요약하기</button>
        <button id="toggleScriptBtn" class="btn">📜 실시간 스크립트 보기</button>
        
        <div id="liveScriptBox" class="live-script-box">
            <div class="live-script-header">🔴 실시간 음성 인식 중 <span class="status-badge">(화면 자동 꺼짐 방지 활성)</span>:</div>
            <div id="liveScriptContent">말씀하시는 내용이 여기에 실시간으로 표시됩니다...</div>
        </div>

        <hr>
        
        <label><b>2-B. 기존 녹음 파일 업로드 (100MB 이상 가능):</b></label><br>
        <input type="file" id="audioUpload" accept="audio/*"><br>
        <button id="uploadBtn" class="btn">📁 파일 업로드 및 요약하기</button>
    </div>
    
    <div id="loadingContainer" class="loading-container">
        <div class="spinner"></div>
        <div id="loadingText" class="loading-text">분석 준비 중...</div>
        <div id="timerText" class="timer-badge"></div>
    </div>
    
    <!-- 요약 결과 및 복사 버튼 영역 -->
    <div id="resultContainer" class="result-container">
        <div class="result-header-bar">
            <span style="font-weight: bold; color: #2c3e50; font-size: 16px;">📖 설교 요약 결과</span>
            <button id="copyBtn" class="copy-btn" onclick="copyResultText()">📋 요약본 복사하기</button>
        </div>
        <div id="resultBox" class="output-box"></div>
    </div>

    <script>
        const API_KEY = "REPLACE_WITH_GEMINI_API_KEY";
        const contextInput = document.getElementById('context');
        const loadingContainer = document.getElementById('loadingContainer');
        const loadingText = document.getElementById('loadingText');
        const timerText = document.getElementById('timerText');
        const resultContainer = document.getElementById('resultContainer');
        const resultBox = document.getElementById('resultBox');
        const copyBtn = document.getElementById('copyBtn');

        let lastSummaryRawText = ''; // 클립보드 복사용 원본 텍스트

        // 복사하기 기능 함수
        async function copyResultText() {
            if (!lastSummaryRawText) return;
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(lastSummaryRawText);
                } else {
                    // 클립보드 API 미지원 환경 fallback
                    const tempTextarea = document.createElement('textarea');
                    tempTextarea.value = lastSummaryRawText;
                    document.body.appendChild(tempTextarea);
                    tempTextarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(tempTextarea);
                }
                copyBtn.innerText = '✅ 복사 완료!';
                copyBtn.classList.add('copied');
                setTimeout(() => {
                    copyBtn.innerText = '📋 요약본 복사하기';
                    copyBtn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                alert('복사에 실패했습니다: ' + err);
            }
        }

        let deferredPrompt;
        const installBtn = document.getElementById('installBtn');

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            installBtn.style.display = 'block';
        });

        installBtn.onclick = async () => {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                console.log('User accepted PWA install');
            }
            deferredPrompt = null;
            installBtn.style.display = 'none';
        };

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(() => console.log('Service Worker Active'));
        }

        let mediaRecorder;
        let audioChunks = [];
        let wakeLock = null;
        let audioContext = null;
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');
        const toggleScriptBtn = document.getElementById('toggleScriptBtn');
        const liveScriptBox = document.getElementById('liveScriptBox');
        const liveScriptContent = document.getElementById('liveScriptContent');

        let speechRecognizer = null;
        let finalTranscript = '';
        let isRecording = false;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            speechRecognizer = new SpeechRecognition();
            speechRecognizer.continuous = true;
            speechRecognizer.interimResults = true;
            speechRecognizer.lang = 'ko-KR';

            speechRecognizer.onresult = (event) => {
                let interimTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript + ' ';
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }
                liveScriptContent.innerHTML = finalTranscript + '<span class="interim-text">' + interimTranscript + '</span>';
                liveScriptBox.scrollTop = liveScriptBox.scrollHeight;
            };

            speechRecognizer.onend = () => {
                if (isRecording) {
                    try { speechRecognizer.start(); } catch (e) {}
                }
            };
        }

        let isScriptVisible = false;
        toggleScriptBtn.onclick = () => {
            isScriptVisible = !isScriptVisible;
            if (isScriptVisible) {
                liveScriptBox.style.display = 'block';
                toggleScriptBtn.innerText = '📜 스크립트 숨기기';
            } else {
                liveScriptBox.style.display = 'none';
                toggleScriptBtn.innerText = '📜 실시간 스크립트 보기';
            }
        };

        async function requestWakeLock() {
            try {
                if ('wakeLock' in navigator) {
                    wakeLock = await navigator.wakeLock.request('screen');
                    wakeLock.addEventListener('release', () => {
                        console.log('Wake Lock released');
                    });
                }
            } catch (err) {
                console.log('WakeLock error:', err);
            }
        }

        recordBtn.onclick = async () => {
            await requestWakeLock();

            try {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (AudioCtx) {
                    audioContext = new AudioCtx();
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    gainNode.gain.value = 0.0001;
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    oscillator.start();
                }
            } catch (e) {
                console.log('AudioContext keep-alive init failed:', e);
            }

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
            isRecording = true;
            finalTranscript = '';
            liveScriptContent.innerText = '말씀하시는 내용이 여기에 실시간으로 표시됩니다...';

            if (speechRecognizer) {
                try { speechRecognizer.start(); } catch (e) {}
            }

            recordBtn.disabled = true;
            recordBtn.style.backgroundColor = '#c0392b';
            recordBtn.innerText = '🔴 녹음 중...';
            stopBtn.disabled = false;
            stopBtn.style.backgroundColor = '#34495e';
            toggleScriptBtn.style.display = 'inline-block';
        };

        stopBtn.onclick = () => {
            isRecording = false;

            if (wakeLock !== null) {
                wakeLock.release();
                wakeLock = null;
            }
            if (audioContext && audioContext.state !== 'closed') {
                audioContext.close();
            }

            if (speechRecognizer) {
                try { speechRecognizer.stop(); } catch (e) {}
            }
            mediaRecorder.stop();
            recordBtn.disabled = false;
            recordBtn.style.backgroundColor = '#e74c3c';
            recordBtn.innerText = '🔴 녹음 시작';
            stopBtn.disabled = true;
            stopBtn.style.backgroundColor = '#7f8c8d';
            toggleScriptBtn.style.display = 'none';
            liveScriptBox.style.display = 'none';
            isScriptVisible = false;
            toggleScriptBtn.innerText = '📜 실시간 스크립트 보기';
        };

        document.addEventListener('visibilitychange', async () => {
            if (wakeLock !== null && document.visibilityState === 'visible' && isRecording) {
                await requestWakeLock();
            }
        });

        const audioUpload = document.getElementById('audioUpload');
        const uploadBtn = document.getElementById('uploadBtn');

        function getMimeType(file) {
            if (file.type && file.type.startsWith('audio/')) {
                return file.type;
            }
            const ext = file.name.split('.').pop().toLowerCase();
            const map = {
                'mp3': 'audio/mp3',
                'm4a': 'audio/mp4',
                'aac': 'audio/aac',
                'wav': 'audio/wav',
                'ogg': 'audio/ogg',
                'flac': 'audio/flac',
                'webm': 'audio/webm'
            };
            return map[ext] || 'audio/mp3';
        }

        uploadBtn.onclick = async () => {
            if (audioUpload.files.length === 0) {
                alert("업로드할 오디오 파일을 선택해주세요.");
                return;
            }
            const file = audioUpload.files[0];
            const mimeType = getMimeType(file);
            await processAudioWithFilesAPI(file, file.name, mimeType);
        };

        async function processAudioWithFilesAPI(fileOrBlob, filename, mimeType) {
            loadingContainer.style.display = 'block';
            resultContainer.style.display = 'none';
            timerText.innerText = '';
            
            let elapsedSec = 0;
            const timerInterval = setInterval(() => {
                elapsedSec++;
                const min = Math.floor(elapsedSec / 60);
                const sec = elapsedSec % 60;
                timerText.innerText = `⏱️ 경과 시간: ${min > 0 ? min + '분 ' : ''}${sec}초 (대용량 파일은 1~3분 소요됩니다)`;
            }, 1000);

            try {
                loadingText.innerText = `📡 ${Math.round(fileOrBlob.size / (1024 * 1024))}MB 대용량 전송 세션을 생성하는 중입니다...`;

                const startResponse = await fetch(`https://generativelanguage.googleapis.com/upload/v1beta/files?key=${API_KEY}`, {
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

                if (!startResponse.ok) {
                    const errText = await startResponse.text();
                    throw new Error("업로드 세션 시작 실패: " + errText);
                }

                const uploadUrl = startResponse.headers.get('X-Goog-Upload-URL');

                loadingText.innerText = "🔄 구글 클라우드로 대용량 오디오를 고속 전송 중입니다...";
                const uploadResponse = await fetch(uploadUrl, {
                    method: 'POST',
                    headers: {
                        'X-Goog-Upload-Offset': '0',
                        'X-Goog-Upload-Command': 'upload, finalize'
                    },
                    body: fileOrBlob
                });

                if (!uploadResponse.ok) {
                    const errText = await uploadResponse.text();
                    throw new Error("파일 데이터 전송 실패: " + errText);
                }

                const fileInfo = await uploadResponse.json();
                const fileUri = fileInfo.file.uri;
                const fileName = fileInfo.file.name;

                let isReady = false;
                loadingText.innerText = "🧠 구글 AI가 대용량 음성 데이터를 인덱싱하고 있습니다 (잠시만 기다려주세요)...";
                
                for (let i = 0; i < 120; i++) {
                    const checkResponse = await fetch(`https://generativelanguage.googleapis.com/v1beta/${fileName}?key=${API_KEY}`);
                    const checkJson = await checkResponse.json();
                    
                    if (checkJson.state === "ACTIVE") {
                        isReady = true;
                        break;
                    } else if (checkJson.state === "FAILED") {
                        throw new Error("구글 서버 내 파일 처리 실패 (오디오 손상 또는 미지원 형식)");
                    }
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }

                if (!isReady) throw new Error("파일 분석 대기 시간 초과 (4분 초과)");

                loadingText.innerText = "📝 전체 설교 내용을 분석하여 구조화 요약본을 작성 중입니다...";

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

                const generateResponse = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${API_KEY}`, {
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
                lastSummaryRawText = rawText; // 복사용 원본 저장

                let resultHtml = rawText;
                resultHtml = resultHtml.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
                resultHtml = resultHtml.replace(/# (.*?)\\n/g, '<h3>$1</h3>\\n');
                resultHtml = resultHtml.replace(/## (.*?)\\n/g, '<h4>$1</h4>\\n');
                resultHtml = resultHtml.replace(/\\n/g, '<br>');

                clearInterval(timerInterval);
                loadingContainer.style.display = 'none';
                resultContainer.style.display = 'block';

                const modelInfoHtml = `<div class="model-info">💡 적용된 AI 모델: Gemini 2.5 Flash (초대용량 Files API)</div>`;
                resultBox.innerHTML = modelInfoHtml + resultHtml;

                fetch(`https://generativelanguage.googleapis.com/v1beta/${fileName}?key=${API_KEY}`, {
                    method: 'DELETE'
                }).catch(e => console.log("임시 파일 삭제 완료 혹은 생략됨."));

            } catch (error) {
                clearInterval(timerInterval);
                loadingContainer.style.display = 'none';
                alert("🚨 대용량 처리 실패: " + error.message);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    safe_html = HTML_TEMPLATE.replace("REPLACE_WITH_GEMINI_API_KEY", API_KEY)
    return HTMLResponse(content=safe_html)

@app.get("/manifest.json")
async def get_manifest():
    return Response(content=MANIFEST_JSON, media_type="application/json")

@app.get("/sw.js")
async def get_sw():
    return Response(content=SERVICE_WORKER_JS, media_type="application/javascript")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
