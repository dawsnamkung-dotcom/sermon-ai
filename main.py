import os
import tempfile
import re
import time
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import uvicorn
import nest_asyncio
from google import genai

nest_asyncio.apply()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

client = genai.Client(api_key=api_key)

app = FastAPI()

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>설교 기록 & 요약 웹앱</title>
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
        
        /* 로딩 애니메이션 스타일 */
        .loading-container { display: none; background-color: #e8f4f8; border: 1px solid #bde0ec; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: center; }
        .spinner { display: inline-block; width: 40px; height: 40px; border: 4px solid rgba(41, 128, 185, 0.2); border-radius: 50%; border-top-color: #2980b9; animation: spin 1s ease-in-out infinite; margin-bottom: 15px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { color: #2c3e50; font-size: 16px; font-weight: bold; transition: all 0.5s ease; }
    </style>
</head>
<body>
    <h2>🎙️ AI 설교 기록 & 요약 (GenAI SDK)</h2>
    
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
    
    <!-- 동적 로딩 화면 UI -->
    <div id="loadingContainer" class="loading-container">
        <div class="spinner"></div>
        <div id="loadingText" class="loading-text">분석 준비 중...</div>
    </div>
    
    <div id="resultBox" class="output-box" style="display:none;"></div>

    <script>
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
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                await sendAudioData(audioBlob, 'recording.webm');
                audioChunks = [];
            };

            mediaRecorder.start();
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
            await sendAudioData(file, file.name);
        };

        async function sendAudioData(fileOrBlob, filename) {
            // UI 초기화
            loadingContainer.style.display = 'block';
            resultBox.style.display = 'none';
            
            // 진행 과정 텍스트 배열
            const steps = [
                "📡 오디오 파일을 안전하게 서버로 전송하고 있습니다...",
                "🔄 구글 AI 서버에서 음성 데이터를 활성화(처리)하는 중입니다...",
                "🧠 최신 모델이 목소리를 텍스트로 추출(STT)하고 있습니다...",
                "📝 전체 문맥을 파악하여 4단락 구조로 요약본을 작성 중입니다...",
                "✨ 거의 다 되었습니다! 최종 양식을 예쁘게 다듬는 중입니다..."
            ];
            
            let stepIndex = 0;
            loadingText.innerText = steps[stepIndex];
            
            // 4.5초마다 진행 상태 텍스트 변경
            const progressInterval = setInterval(() => {
                stepIndex++;
                if (stepIndex < steps.length) {
                    loadingText.innerText = steps[stepIndex];
                }
            }, 4500);

            const formData = new FormData();
            formData.append('audio_file', fileOrBlob, filename);
            formData.append('context', contextInput.value);

            try {
                const response = await fetch('/process_audio', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                // 완료 시 타이머 종료 및 UI 전환
                clearInterval(progressInterval);
                loadingContainer.style.display = 'none';
                resultBox.style.display = 'block';
                
                const modelInfoHtml = `<div class="model-info">💡 적용된 AI 모델: ${data.model_used}</div>`;
                resultBox.innerHTML = modelInfoHtml + data.result;
            } catch (error) {
                clearInterval(progressInterval);
                loadingContainer.style.display = 'none';
                alert("오류가 발생했습니다: " + error);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_CONTENT)

@app.post("/process_audio")
async def process_audio(audio_file: UploadFile = File(...), context: str = Form("")):
    ext = os.path.splitext(audio_file.filename)[1]
    if not ext:
        ext = ".webm"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_audio:
        temp_audio.write(await audio_file.read())
        temp_audio_path = temp_audio.name

    try:
        uploaded_file = client.files.upload(file=temp_audio_path)
        
        while True:
            file_info = client.files.get(name=uploaded_file.name)
            if file_info.state == "ACTIVE":
                break
            elif file_info.state == "FAILED":
                raise Exception("오디오 파일 처리에 실패했습니다.")
            time.sleep(2)
        
        prompt = f"""
        당신은 전문적인 설교 기록 및 요약 비서입니다.
        제공된 오디오 파일은 교회 설교 녹음입니다.
        다음의 사전 맥락(성경 본문, 고유명사)을 참고하여 내용을 정확히 파악하세요: [{context}]
        
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
        """
        
        model_name = "gemini-2.5-flash"
        response = client.models.generate_content(
            model=model_name,
            contents=[uploaded_file, prompt]
        )
        
        client.files.delete(name=uploaded_file.name)
        
        result_html = response.text
        result_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', result_html)
        result_html = re.sub(r'# (.*?)\n', r'<h3>\1</h3>\n', result_html)
        result_html = re.sub(r'## (.*?)\n', r'<h4>\1</h4>\n', result_html)
        result_html = result_html.replace("\n", "<br>")
        
        return {"result": result_html, "model_used": model_name}

    finally:
        os.remove(temp_audio_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
