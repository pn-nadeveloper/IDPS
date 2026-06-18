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

app = FastAPI(title="Hybrid AI-Powered Intrusion Detection System") # FastAPI 앱 생성
WHITELIST_SET = set() # 화이트 리스트를 글로벌 변수로 선언
WHITELIST_FILE = "whitelist.txt" # 화이트 리스트 파일 경로
Gemini_API_KEY = "" # Gemini API 키 초기값
OPENROUTER_API_KEY = "" #OPENROUTER API 키 초기값
CLOUDFLARE_API_TOKEN = "" # Cloudflare API 토큰 초기값
CLOUDFLARE_API_KEY = "" # Cloudflare API 키 초기값
ACCOUNT_ID = "" # Cloudflare 계정 ID 초기값
EMAIL = "" # Cloudflare 이메일 초기값
model = None
vectorizer = None
list_id = "" # Cloudflare 리스트 ID 초기값
AI_ENGINE = "" # AI 엔진 선택 초기값

def model_load():
    global model, vectorizer
    try:
        model = joblib.load('idps_rf_model.pkl')
        vectorizer = joblib.load('tfidf_vectorizer.pkl')
        print("✅ AI 모델 로드 성공!")
    except Exception as e:
        print(f"❌ AI 모델 로드 실패: {e}")

API_KEYS = [ ] ## API KEY 리스트 초기값

current_key_index = 0 # 현재 사용하는 API 키 인덱스

def reload_setting():
    global Gemini_API_KEY, OPENROUTER_API_KEY, AI_ENGINE, API_KEYS, current_key_index, CLOUDFLARE_API_TOKEN, ACCOUNT_ID, CLOUDFLARE_API_KEY, EMAIL, list_id
    load_dotenv(override=True)  # .env 파일에서 환경 변수 로드
    Gemini_API_KEY = os.getenv("GEMINI_API_KEY") # Gemini API 키
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") #기존 코드
    AI_ENGINE = os.getenv("ACTIVE_AI_ENGINE") # AI 엔진 선택
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN") # Cloudflare API 토큰
    ACCOUNT_ID = os.getenv("ACCOUNT_ID") # Cloudflare 계정 ID
    CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY") # Cloudflare API 키
    EMAIL = os.getenv("CLOUDFLARE_EMAIL") # Cloudflare 이메일
    list_id = os.getenv("CLOUDFLARE_LIST_ID") # Cloudflare 리스트 ID
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

def call_ai_engine(query_path: str):
    global AI_ENGINE
    """
    .env의 ACTIVE_AI_ENGINE 값에 따라
    알맞은 AI 함수를 동적으로 연결해주는 마스터 스위치"""
    if AI_ENGINE == "OPENROUTER_Rotation":
        return call_second_ai_Rotation(query_path)
    elif AI_ENGINE == "OPENROUTER":
        return call_second_ai_OpenRouter(query_path)
    elif AI_ENGINE == "GEMINI":
        return call_second_ai_Gemini(query_path)
    #elif AI_ENGINE == "OTHER": # 추가 AI 엔진 추가 필요
        #return call_second_ai(query_path) # 추가 AI 엔진 함수 추가
    else:
        return {"success": False,"reason": "AI 엔진 선택 오류"}

def call_second_ai_Rotation(query_path: str):

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

def call_second_ai_Gemini(query_path: str):
    global Gemini_API_KEY
    ## 모델 설정 (원하는 모델로 바꿔서)
    model_name = "gemma-4-31b-it:free"
    #model_name = "google/gemma-4-31b-it:free"
    ##model_name = "openrouter/free"
    url = f"https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {Gemini_API_KEY}",
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

        if "error" in res_json:
            print(f"❌ OpenRouter 자체 에러 발생: {res_json['error']}")
            return {"success": False,"reason": "OpenRouter API 호출 실패"}
        ai_text = res_json['choices'][0]['message']['content'].strip()

        result = json.loads(ai_text)
        return result.get("verdict", "NORMAL"), result.get("reason", "reason")
    except Exception as e:
        print(f"❌ OpenRouter API 호출 실패: 제한된 시도 횟수 도달")
        return {"success": False,"reason": "OpenRouter API 호출 실패"}

def call_second_ai_OpenRouter(query_path: str):
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
                    return {"success": False,"reason": "API 내부 에러로 인한 안전 차단"}

        ai_text = res_json['choices'][0]['message']['content'].strip()

        result = json.loads(ai_text)
        return result.get("verdict", "NORMAL"), result.get("reason", "분석 완료")
    except Exception as e:
        print(f"❌ OpenRouter API 호출 실패: {e}")
        return {"success": False,"reason": "OpenRouter API 호출 실패"}

def cloudflare_list_setup():
    global CLOUDFLARE_API_TOKEN, ACCOUNT_ID
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists" #Cloudflare API 엔드포인트 URL (리스트 조회)
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5.0)  # GET 요청으로 리스트 조회
        if response.status_code == 200:
            data = response.json()
            if(data['result'][0]['id'] == list_id):
                print("✅ Cloudflare API 리스트 연결에 성공하였습니다.")
                print(f"✅ Cloudflare API 리스트 이름: {data['result'][0]['name']}")
            else:
                print("❌ Cloudflare API 리스트 연결에 실패하였습니다.")
                print(f"Cloudflare API 리스트 ID: {data['result'][0]['id']}")
                print(f"현재 리스트 ID: {list_id}")
                print("리스트 ID를 확인해주세요.")
        else:
            print(f"❌ Cloudflare API 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare API 호출 중 예외 발생: {e}")

def cloudflare_setup():
    global CLOUDFLARE_API_TOKEN, ACCOUNT_ID
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/tokens" #Cloudflare API 엔드포인트 URL (토큰 조회)
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5.0)  # GET 요청으로 토큰 정보 조회
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cloudflare API 토큰 이름: {data['result'][0]['name']}")
        else:
            print(f"❌ Cloudflare SETUP 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare SETUP 호출 중 예외 발생: {e}")

def cloudflare_info():
    global CLOUDFLARE_API_KEY, EMAIL, ACCOUNT_ID
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}" #Cloudflare API 엔드포인트 URL (토큰 조회)
    headers = {
        "X-Auth-Email"  : EMAIL,
        "X-Auth-Key"    : CLOUDFLARE_API_KEY,
    }
    try:
        response = requests.get(url, headers=headers, timeout=5.0)  # GET 요청으로 사용자 정보 조회
        if response.status_code == 200:
            data = response.json()
            print(f"🍷 {data['result']['name']}님 IDPS에 연결성공 하였습니다. 🔫")
        else:
            print(f"❌ Cloudflare INFO 조회 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare INFO 호출 중 예외 발생: {e}")

@app.on_event("startup")
def startup_event():
        load_whitelist()
        model_load()
        reload_setting()
        cloudflare_setup()
        cloudflare_info()
        cloudflare_list_setup()

@app.get("/reset")
async def reset_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(startup_event)
    return {"status": "success", "message": "전체 재설정 작업이 백그라운드에서 시작되었습니다."}

@app.get("/cloudflare/list/reload")
async def reload_cloudflare_list_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(reload_setting)
    background_tasks.add_task(cloudflare_list_setup)
    return {"status": "success", "message": "Cloudflare API 리스트 설정 재로드 작업이 백그라운드에서 시작되었습니다."}

@app.get("/cloudflare/reload")
async def reload_cloudflare_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(reload_setting)
    background_tasks.add_task(cloudflare_setup)
    return {"status": "success", "message": "Cloudflare API 설정 재로드 작업이 백그라운드에서 시작되었습니다."}

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

@app.get("/setting/reload")
async def reload_setting_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(reload_setting)
    print("-" * 80)
    print("현재 설정: ")
    print(f"Gemini API 키: {Gemini_API_KEY}")
    print(f"OpenRouter API 키: {OPENROUTER_API_KEY}")
    print(f"OpenRouter 키 리스트: {API_KEYS}")
    print(f"AI 엔진: {AI_ENGINE}")
    print("-" * 80)
    return {"status": "success", "message": "설정 재로드 작업이 백그라운드에서 시작되었습니다."}

@app.post("/blocked")
async def blocked_ip(ip : str = None, reason : str = None):
    if not ip:
        return {"status": "error", "message": "IP 주소를 입력해주세요."}
    if not reason:
        return {"status": "error", "message": "사유를 입력해주세요."}
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists/{list_id}/items" #Cloudflare API 엔드포인트 URL (리스트 등록)
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    body = [ {
        "ip": ip,
        "comment": reason
    } ]
    try:
        response = requests.post(url, headers=headers, json=body, timeout=5.0)  # POST 요청으로 리스트 항목 추가 테스트
        if response.status_code == 200:
            result = response.json()
            return {"status": "success", "message": result['result']['operation_id']}
        else:
            print(f"❌ Cloudflare 차단 API 연결 실패: {response.status_code} - {response.text}")
            return {"status": "error", "message": "차단 실패"}
    except Exception as e:
        print(f"❌ Cloudflare 차단 API 호출 중 예외 발생: {e}")
        return {"status": "error", "message": "차단 실패"}

@app.get("/unblocked")
async def unblocked_ip(id : str = None):
    if not id:
        return {"status": "error", "message": "ID 를 입력해주세요."}
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists/{list_id}/items" #Cloudflare API 엔드포인트 URL (리스트 등록)
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "items": [{
            "id" : id
        }]
    }
    try:
        response = requests.delete(url, headers=headers, json=body, timeout=5.0)  # DELETE 요청으로 리스트 항목 삭제 테스트
        if response.status_code == 200:
            data = response.json()
            if data['success'] == True:
                print("✅ Cloudflare 차단 해제 성공!")
                return {"status": "success", "message": "차단 해제 성공"}
            else:
                print(f"❌ Cloudflare 차단 해제 실패: {response.status_code} - {response.text}")
                return {"status": "error", "message": "차단 해제 실패"}
        else:
            print(f"❌ Cloudflare 차단 API 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare 차단 API 호출 중 예외 발생: {e}")

@app.get("/check")
async def check_log(path: str = None, ip: str = None, id: str = None):
    global model, vectorizer, WHITELIST_SET
    if not path:
        return {"status": "error", "message": "URL 경로를 입력해주세요."}
    if not ip:
        return {"status": "error", "message": "IP 주소를 입력해주세요."}
    if not id:
        return {"status": "error", "message": "ID 를 입력해주세요."}
    temp_path = unquote(path)  # URL 디코딩
    if temp_path in WHITELIST_SET:
        return {
            "success": True,
            "status": "ALLOW",
            "proba" : 0,
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
                "proba" : 0,
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
                "proba" : f"{attack_prob*100:.1f}",
                "reason" : "명확한 패턴 감지",
                "ip": ip,
                "id": id
            }
        elif attack_prob <= 0.2:

            return {
                "success": True,
                "status": "ALLOW",
                "source": "1st_AI",
                "proba": f"{attack_prob*100:.1f}",
                "reason": "명확한 패턴 감지 안됨",
                "ip": ip,
                "id": id
            }
        else:

            verdict, reason = call_ai_engine(path)

            with open("llm_train_dataset.jsonl", "a", encoding="utf-8") as f:
                log_data = {"url": path, "verdict": verdict, "reason": reason}
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

            if verdict == "ATTACK":
                return {
                    "success": True,
                    "status": "BLOCK",
                    "source": "2nd_AI",
                    "proba" : f"{attack_prob*100:.1f}",
                    "reason": reason,
                    "ip": ip,
                    "id": id
                }
            else:
                return {
                    "success": True,
                    "status": "ALLOW",
                    "source": "2nd_AI",
                    "proba" : 0,
                    "reason": reason,
                    "ip": ip,
                    "id": id
                }
    except Exception as e:
        return{"success": False, "status": "ALLOW", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)