import os
import json
import joblib
import requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드

app = FastAPI(title="Hybrid AI-Powered Intrusion Detection System")

try:
    model = joblib.load('idps_rf_model.pkl')
    vectorizer = joblib.load('tfidf_vectorizer.pkl')
    print("✅ AI 모델 로드 성공!")
except Exception as e:
    print(f"❌ AI 모델 로드 실패: {e}")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_second_ai(query_path: str):
    ## 모델 설정 (원하는 모델로 바꿔서)
    ##model_name = "gemma-4-31b-it:free"
    ##model_name = "google/gemma-4-31b-it:free"
    model_name = "openrouter/free"
    url = f"https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "당신은 엄격한 웹 보안 전문가 입니다. 입력된 URL 경로가 해킹시도인지(ATTACK) 정상적인(NORMAL) 판정하세요."
        "사족이나 대화는 절대 하지 말고 무조건 아래 JSON 형식으로만 답변하세요.\n"
        "{\"verdict\": \"ATTACK\"} 또는 {\"verdict\": \"NORMAL\", \"reason\": \"이유\"}"
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"URL: {query_path}"}
        ],
        "temperature": 0.1
    }

    try:

        response = requests.post(url, headers=headers, json=payload, timeout=5.0)
        res_json = response.json()

        if "error" in res_json:
                    print(f"❌ OpenRouter 자체 에러 발생: {res_json['error']}")
                    return "ATTACK", "API 내부 에러로 인한 안전 차단"

        ai_text = res_json['choices'][0]['message']['content'].strip()

        result = json.loads(ai_text)
        return result.get("verdict", "NORMAL"), result.get("reason", "분석 완료")
    except Exception as e:
        print(f"❌ OpenRouter API 호출 실패: {e}")
        return "NORMAL", "OpenRouter API 호출 실패"
    
@app.get("/check")
async def check_log(path: str):
    if not path:
        return {"status": "error", "message": "URL 경로를 입력해주세요."}
    try:

        vector = vectorizer.transform([path])

        attack_prob = model.predict_proba(vector)[0][1]

        if attack_prob >= 0.8:

            return {
                "status": "BLOCK",
                "source" : "1st_AI",
                "proba" : f"{attack_prob*100:.1f}%",
                "reason" : "명확한 패턴 감지"
            }
        elif attack_prob >= 0.2:

            return {
                "status": "ALLOW",
                "source": "1st_AI",
                "proba": f"{attack_prob*100:.1f}%",
            }
        else:

            verdict, reason = call_second_ai(path)

            with open("llm_train_dataset.jsonl", "a", encoding="utf-8") as f:
                log_data = {"url": path, "verdict": verdict, "reason": reason}
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

            if verdict == "ATTACK":
                return {
                    "status": "BLOCK",
                    "source": "2nd_AI",
                    "reason": reason
                }
            else:
                return {
                    "status": "ALLOW",
                    "source": "2nd_AI",
                    "reason": reason
                }
    except Exception as e:
        return{"status": "ALLOW", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)