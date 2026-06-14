import os
import json
import joblib
import requests
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from urllib.parse import unquote
import time

load_dotenv()  # .env 파일에서 환경 변수 로드
app = FastAPI(title="Hybrid AI-Powered Intrusion Detection System") # FastAPI 앱 생성
WHITELIST_SET = set() # 화이트 리스트를 글로벌 변수로 선언
WHITELIST_FILE = "whitelist.txt" # 화이트 리스트 파일 경로

model = None
vectorizer = None

def model_load():
    global model, vectorizer
    try:
        model = joblib.load('idps_rf_model.pkl')
        vectorizer = joblib.load('tfidf_vectorizer.pkl')
        print("✅ AI 모델 로드 성공!")
    except Exception as e:
        print(f"❌ AI 모델 로드 실패: {e}")

API_KEYS = [ ## 여러 API 키 추가
    os.getenv("OPENROUTER_API_KEY"),
    os.getenv("OPENROUTER_API_KEY_2"),
    os.getenv("OPENROUTER_API_KEY_3"),
    os.getenv("OPENROUTER_API_KEY_4"),
]

API_KEYS = [k for k in API_KEYS if k] # 여러 API 키 중 정상적인 키만 넣어주기

current_key_index = 0 # 현재 사용하는 API 키 인덱스

def load_whitelist():
    global WHITELIST_SET

    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            # 파일에서 줄바꿈을 제거하고, 빈줄이나 주석(#) 제외하고 메모리에 로드
            lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
            WHITELIST_SET = set(lines)
        print(f"✅ 화이트 리스트 로드 완료: {len(WHITELIST_SET)}개 로드됨")
    else:
        with open(WHITELIST_FILE, "w" , encoding="utf-8") as f:
            f.write("# 화이트 리스트에 추가할 URL 경로를 여기에 입력하세요.\n")
            f.write("# 예시:\n")
            f.write("/index.html\n")
            f.write("/js/script.js\n")
        WHITELIST_SET = {"/index.html", "/js/script.js"} # 기본적으로 몇 개의 정상 URL을 화이트 리스트에 추가
        print(f"⚠️ 화이트 리스트 파일이 존재하지 않아 새로 생성했습니다: {WHITELIST_FILE}")

def call_second_ai(query_path: str):

    global current_key_index # 현재 사용하는 API 키 인덱스

    if not API_KEYS:
        print("❌ 설정된 API 키가 없습니다. 설정파일을 확인해주세요.")
        exit(1)
    ## 모델 설정 (원하는 모델로 바꿔서)
    ##model_name = "gemma-4-31b-it:free"
    #model_name = "google/gemma-4-31b-it:free"
    model_name = "openrouter/free"
    url = f"https://openrouter.ai/api/v1/chat/completions"

    Max_total_attempts = len(API_KEYS) * 2

    for key in range(Max_total_attempts):
        active_key = API_KEYS[current_key_index]
        headers = {
            "Authorization": f"Bearer {active_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "당신은 엄격한 웹 보안 전문가 입니다. 입력된 URL 경로가 해킹시도인지(ATTACK) 정상적인(NORMAL) 판정하세요."
            "사족이나 대화는 절대 하지 말고 무조건 아래 JSON 형식으로만 답변하세요.\n"
            "⚠️ 중요: 'reason'의 내용은 반드시 '한국어(Korean)'로만 구체적으로 작성해야 합니다.\n\n"
            "{\"verdict\": \"ATTACK\", \"reason\": \"이유\"} 또는 {\"verdict\": \"NORMAL\", \"reason\": \"이유\"}"
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

            if response.status_code == 429 or "error" in res_json:
                err_msg = res_json.get("error", {}).get("message", "Unknown Rate Limit")
                print(f"❌ OpenRouter 자체 에러 발생: {err_msg}")
                current_key_index = (current_key_index + 1) % len(API_KEYS)
                time.sleep(0.5)
                continue

            ai_text = res_json['choices'][0]['message']['content'].strip()

            result = json.loads(ai_text)
            return result.get("verdict", "NORMAL"), result.get("reason", "reason")
        except Exception as e:
            print(f"❌ [키 {current_key_index+1}번] 에러발생 (원인: {e})")
            print(f"서버를 멈추지 않고, 다음키로 인덱스 하여 다시 시도합니다.")

            current_key_index = (current_key_index + 1) % len(API_KEYS)
            time.sleep(0.5)
            continue
        
    print(f"❌ OpenRouter API 호출 실패: 제한된 시도 횟수 도달")
    return {"success": False,"reason": "OpenRouter API 호출 실패"}
@app.on_event("startup")
def startup_event():
    load_whitelist()
    model_load()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/whitelist/reload")
async def reload_whitelist_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(load_whitelist)
    return {"status": "success", "message": "화이트 리스트 재로드 작업이 백그라운드에서 시작되었습니다."}

@app.get("/model/reload")
async def reload_model_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(model_load)
    return {"status": "success", "message": "AI 모델 재로드 작업이 백그라운드에서 시작되었습니다."}



@app.get("/check")
async def check_log(path: str = None, ip: str = None, id: str = None):
    global model, vectorizer, WHITELIST_SET
    if not path:
        return {"status": "error", "message": "URL 경로를 입력해주세요."}
    if not ip:
        return {"status": "error", "message": "IP 주소를 입력해주세요."}
    temp_path = unquote(path)  # URL 디코딩
    if temp_path in WHITELIST_SET:
        return {
            "success": True,
            "status": "ALLOW",
            "source": "WHITELIST",
            "reason": "화이트 리스트에 등록된 URL",
            "ip": ip,
            "id": id
        }
    for white_path in WHITELIST_SET:
        if temp_path.startswith(white_path):
            return {
                "success": True,
                "status": "ALLOW",
                "source": "WHITELIST",
                "reason": "화이트 리스트에 등록된 URL",
                "ip": ip,
                "id": id
            }
    try:

        vector = vectorizer.transform([path])

        attack_prob = model.predict_proba(vector)[0][1]

        if attack_prob >= 0.8:

            return {
                "success": True,
                "status": "BLOCK",
                "source" : "1st_AI",
                "proba" : f"{attack_prob*100:.1f}%",
                "reason" : "명확한 패턴 감지",
                "ip": ip,
                "id": id
            }
        elif attack_prob <= 0.2:

            return {
                "success": True,
                "status": "ALLOW",
                "source": "1st_AI",
                "proba": f"{attack_prob*100:.1f}%",
                "ip": ip,
                "id": id
            }
        else:

            verdict, reason = call_second_ai(path)

            with open("llm_train_dataset.jsonl", "a", encoding="utf-8") as f:
                log_data = {"url": path, "verdict": verdict, "reason": reason}
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

            if verdict == "ATTACK":
                return {
                    "success": True,
                    "status": "BLOCK",
                    "source": "2nd_AI",
                    "reason": reason,
                    "ip": ip,
                    "id": id
                }
            else:
                return {
                    "success": True,
                    "status": "ALLOW",
                    "source": "2nd_AI",
                    "reason": reason,
                    "ip": ip,
                    "id": id
                }
    except Exception as e:
        return{"success": False, "status": "ALLOW", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)