import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Render 서버의 API 키를 안전하게 가져옴
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 최신 2.5 모델과 완벽하게 호환되는 구글 GenAI 공식 브라우저 라이브러리 탑재
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>설교 기록 & 요약 웹앱</title>
    <!-- 구글 최신 GenAI SDK 정식 로드 -->
    <script type="importmap">
      {
        "imports": {
          "@google/genai": "https://esm.run/@google/genai"
        }
      }
    </script>
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .section { background-color: #f4f6f7; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        textarea { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; border: 1px solid #bdc3c7; border-radius: 4px; }
        .btn { padding: 12px 24px; font-size: 16px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; border: none; border-radius: 5px; color: white; font-weight: bold; }
        #recordBtn { background-color: #e74c3c; }
        #stopBtn { background-color: #7f8c8d; }
        #uploadBtn { background-color: #27ae60; }
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
    <h2>🎙️ AI 설교 요약 (최신 Gemini 2.5 Flash & 대용량 무제한)</h2>
    
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

    <script type="module">
        import { GoogleGenAI } from "@google/genai";

        const API_KEY = "REPLACE_WITH_GEMINI_API_KEY";
        // 최신 규격에 맞는 API 클라이언트 선언
        const ai = new GoogleGenAI({ apiKey: API_KEY });

        const contextInput = document.getElementById('context');
        const loadingContainer = document.getElementById('loadingContainer');
        const loadingText = document.getElementById('loadingText');
        const resultBox = document.getElementById('resultBox');

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
                await processAudioWithSDK(audioBlob, 'recording.webm', 'audio/webm');
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
            await processAudioWithSDK(file, file.name, mimeType);
        };

        async function processAudioWithSDK(fileOrBlob, filename, mimeType) {
            loadingContainer.style.display = 'block';
            resultBox.style.display = 'none';
            
            const steps = [
                "📡 대용량 오디오 파일을 구글 AI 전용 스토리지로 업로드 중입니다...",
                "🔄 구글 클라우드가 대용량 음성 스트림을 고속으로 접수하고 있습니다...",
                "🧠 인공지능이 음성 트랙 전체의 유효 상태를 분석(ACTIVE)하고 있습니다...",
                "📝 최신 Gemini 2.5 Flash가 전체 흐름을 완벽하게 파악해 기록 중입니다...",
                "✨ 최종 정리가 끝났습니다! 서식 양식 마무리를 짓는 중입니다..."
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
                // 1. 대용량용 무제한 창구(files API)로 직접 전송
                const uploadResult = await ai.files.upload({
                    file: fileOrBlob,
                    mimeType: mimeType,
                    config: { displayName: filename }
                });

                // 2. 구글 내부 가상 인코딩 처리 대기
                let fileInfo = uploadResult;
                while (fileInfo.state === "PROCESSING") {
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    fileInfo = await ai.files.get({ name: uploadResult.name });
                }

                if (fileInfo.state === "FAILED") {
                    throw new Error("구글 서버 내 오디오 데이터 처리 도중 실패했습니다.");
                }

                // 3. 정교하게 고도화된 프롬프트 전달
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

                // 4. [변경 완료] 최초 원했던 고성능 최신 모델 'gemini-2.5-flash'로 호출
                const response = await ai.models.generateContent({
                    model: 'gemini-2.5-flash',
                    contents: [fileInfo, prompt],
                });

                let resultHtml = response.text;
                resultHtml = resultHtml.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
                resultHtml = resultHtml.replace(/# (.*?)\\n/g, '<h3>$1</h3>\\n');
                resultHtml = resultHtml.replace(/## (.*?)\\n/g, '<h4>$1</h4>\\n');
                resultHtml = resultHtml.replace(/\\n/g, '<br>');

                clearInterval(progressInterval);
                loadingContainer.style.display = 'none';
                resultBox.style.display = 'block';

                const modelInfoHtml = `<div class="model-info">💡 적용된 AI 모델: Gemini 2.5 Flash (Official SDK v1beta)</div>`;
                resultBox.innerHTML = modelInfoHtml + resultHtml;

                // 5. 사용 후 즉각 삭제
                await ai.files.delete({ name: fileInfo.name });

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

@app.get("/", response_class=HTMLResponse)
async def get_index():
    safe_html = HTML_TEMPLATE.replace("REPLACE_WITH_GEMINI_API_KEY", API_KEY)
    return HTMLResponse(content=safe_html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
