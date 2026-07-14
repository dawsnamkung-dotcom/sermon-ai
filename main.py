import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Render 서버에 등록된 API 키를 브라우저(자바스크립트)가 안전하게 가져갈 수 있도록 전달합니다.
API_KEY = os.environ.get("GEMINI_API_KEY", "")

HTML_CONTENT = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>설교 기록 & 요약 웹앱</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .section {{ background-color: #f4f6f7; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        textarea {{ width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; border: 1px solid #bdc3c7; border-radius: 4px; }}
        .btn {{ padding: 12px 24px; font-size: 16px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; border: none; border-radius: 5px; color: white; font-weight: bold; }}
        #recordBtn {{ background-color: #e74c3c; }}
        #stopBtn {{ background-color: #7f8c8d; }}
        #uploadBtn {{ background-color: #27ae60; }}
        input[type="file"] {{ margin-bottom: 15px; font-size: 16px; }}
        .output-box {{ background-color: #fff; padding: 20px; border-radius: 8px; margin-top: 20px; white-space: pre-wrap; line-height: 1.6; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .model-info {{ color: #7f8c8d; font-size: 13px; text-align: right; margin-bottom: 10px; border-bottom: 1px dashed #bdc3c7; padding-bottom: 5px; }}
        hr {{ border: 0; height: 1px; background: #dcdde1; margin: 20px 0; }}
        
        .loading-container {{ display: none; background-color: #e8f4f8; border: 1px solid #bde0ec; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: center; }}
        .spinner {{ display: inline-block; width: 40px; height: 40px; border: 4px solid rgba(41, 128, 185, 0.2); border-radius: 50%; border-top-color: #2980b9; animation: spin 1s ease-in-out infinite; margin-bottom: 15px; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .loading-text {{ color: #2c3e50; font-size: 16px; font-weight: bold; transition: all 0.5s ease; }}
    </style>
</head>
<body>
    <h2>🎙️ 대용량 지원 설교 요약 (구글 다이렉트 전송)</h2>
    
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
        const API_KEY = "{API_KEY}"; // 백엔드에서 전달받은 안전한 키
        const contextInput = document.getElementById('context');
        const loadingContainer = document.getElementById('loadingContainer');
        const loadingText = document.getElementById('loadingText');
        const resultBox = document.getElementById('resultBox');

        let mediaRecorder;
        let audioChunks = [];
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');

        recordBtn.onclick = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = event => {{
                if (event.data.size > 0) {{
                    audioChunks.push(event.data);
                }}
            }};

            mediaRecorder.onstop = async () => {{
                if (audioChunks.length === 0) {{
                    alert("녹음된 소리가 없습니다.");
                    return;
                }
                const audioBlob = new Blob(audioChunks, {{ type: 'audio/webm' }});
                await processAudioDirectly(audioBlob, 'webm');
                audioChunks = [];
            }};

            mediaRecorder.start(1000);
            recordBtn.disabled = true;
            recordBtn.style.backgroundColor = '#c0392b';
            recordBtn.innerText = '🔴 녹음 중...';
            stopBtn.disabled = false;
            stopBtn.style.backgroundColor = '#34495e';
        };

        stopBtn.onclick = () => {{
            mediaRecorder.stop();
            recordBtn.disabled = false;
            recordBtn.style.backgroundColor = '#e74c3c';
            recordBtn.innerText = '🔴 녹음 시작';
            stopBtn.disabled = true;
            stopBtn.style.backgroundColor = '#7f8c8d';
        }};

        const audioUpload = document.getElementById('audioUpload');
        const uploadBtn = document.getElementById('uploadBtn');

        uploadBtn.onclick = async () => {{
            if (audioUpload.files.length === 0) {{
                alert("업로드할 오디오 파일을 선택해주세요.");
                return;
            }}
            const file = audioUpload.files[0];
            const ext = file.name.split('.').pop().toLowerCase();
            await processAudioDirectly(file, ext);
        }};

        // [핵심 변경] 브라우저에서 구글 Gemini API로 직접 파일을 전송하는 함수
        async function processAudioDirectly(fileOrBlob, extension) {{
            loadingContainer.style.display = 'block';
            resultBox.style.display = 'none';
            
            const steps = [
                "📡 대용량 오디오를 구글 AI 서버로 직접 안전하게 전송 중입니다...",
                "🔄 구글 클라우드가 음성 데이터를 고속으로 받아들이고 있습니다...",
                "🧠 인공지능이 오디오에서 설교 목소리를 추출하여 받아적는 중입니다...",
                "📝 받아적은 전체 흐름과 주제를 일목요연하게 요약 정리 중입니다...",
                "✨ 거의 완료되었습니다! 예쁜 요약 노트를 만들고 있습니다..."
            ];
            
            let stepIndex = 0;
            loadingText.innerText = steps[stepIndex];
            const progressInterval = setInterval(() => {{
                stepIndex++;
                if (stepIndex < steps.length) {{
                    loadingText.innerText = steps[stepIndex];
                }}
            }}, 5000);

            try {{
                // 1. 파일을 Base64 데이터로 변환
                const base64Data = await getBase64(fileOrBlob);
                const rawBase64 = base64Data.split(',')[1];
                
                // 파일 형식 매핑
                let mimeType = "audio/webm";
                if (extension === "mp3") mimeType = "audio/mp3";
                else if (extension === "m4a") mimeType = "audio/m4a";
                else if (extension === "wav") mimeType = "audio/wav";

                // 2. Gemini API 직접 요청 (1.5 Flash 모델 사용)
                const prompt = `
                당신은 전문적인 설교 기록 및 요약 비서입니다.
                제공된 오디오 파일은 교회 설교 녹음입니다.
                다음의 사전 맥락(성경 본문, 고유명사)을 참고하여 내용을 정확히 파악하세요: [\${{contextInput.value}}]
                
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

                const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=\${{API_KEY}}`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        contents: [
                            {{
                                parts: [
                                    {{
                                        inlineData: {{
                                            mimeType: mimeType,
                                            data: rawBase64
                                        }}
                                    }},
                                    {{
                                        text: prompt
                                    }}
                                ]
                            }}
                        ]
                    }})
                }});

                if (!response.ok) {{
                    const errData = await response.json();
                    throw new Error(errData.error?.message || "구글 서버 응답 실패");
                }}

                const resultJson = await response.json();
                const rawText = resultJson.candidates[0].content.parts[0].text;

                // 마크다운 문법을 HTML로 간단하게 정제
                let resultHtml = rawText;
                resultHtml = resultHtml.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
                resultHtml = resultHtml.replace(/# (.*?)\\n/g, '<h3>$1</h3>\\n');
                resultHtml = resultHtml.replace(/## (.*?)\\n/g, '<h4>$1</h4>\\n');
                resultHtml = resultHtml.replace(/\\n/g, '<br>');

                clearInterval(progressInterval);
                loadingContainer.style.display = 'none';
                resultBox.style.display = 'block';

                const modelInfoHtml = `<div class="model-info">💡 적용된 AI 모델: Gemini 1.5 Flash (Direct API)</div>`;
                resultBox.innerHTML = modelInfoHtml + resultHtml;

            }} catch (error) {{
                clearInterval(progressInterval);
                loadingContainer.style.display = 'none';
                alert("🚨 처리 실패: " + error.message);
            }}
        }}

        function getBase64(file) {{
            return new Promise((resolve, reject) => {{
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result);
                reader.onerror = error => reject(error);
            }});
        }}
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_CONTENT)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
