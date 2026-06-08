import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
list_id = os.getenv("CLOUDFLARE_LIST_ID")

def test_cloudflare_api():
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists/{list_id}/items" #Cloudflare List 항목 업데이트 테스트 API 엔드포인트
    #url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists" #Cloudflare API 엔드포인트 URL (리스트 항목 조회)
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    body = [ {
        "ip": "10.0.0.1",
        "comment": "Test IP for IDPS system"
    } ]
    try:
        response = requests.post(url, headers=headers, json=body, timeout=5.0)  # POST 요청으로 리스트 항목 추가 테스트
        if response.status_code == 200:
            print("✅ Cloudflare API 연결 성공!")
            data = response.json()
            print(json.dumps(data, indent=4))  # 응답 데이터 출력
        else:
            print(f"❌ Cloudflare API 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare API 호출 중 예외 발생: {e}")

def test1_cloudflare_api():
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists/{list_id}/items" #Cloudflare List 항목 업데이트 테스트 API 엔드포인트
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
    }
    try:
        response = requests.get(url, headers=headers, timeout=5.0)  # POST 요청으로 리스트 항목 추가 테스트
        if response.status_code == 200:
            print("✅ Cloudflare API 연결 성공!")
            data = response.json()
            print(json.dumps(data, indent=4))  # 응답 데이터 출력
        else:
            print(f"❌ Cloudflare API 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare API 호출 중 예외 발생: {e}")

def test2_cloudflare_api():
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists/{list_id}/items" #Cloudflare List 항목 업데이트 테스트 API 엔드포인트
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
    }
    body = {
        "items": [{
            "id" : "6b684593679d430381274ef159495dd3"
        }]
    }
    try:
        response = requests.delete(url, headers=headers, json=body, timeout=5.0)  # DELETE 요청으로 리스트 항목 삭제 테스트
        if response.status_code == 200:
            print("✅ Cloudflare API 연결 성공!")
            data = response.json()
            print(json.dumps(data, indent=4))  # 응답 데이터 출력
        else:
            print(f"❌ Cloudflare API 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare API 호출 중 예외 발생: {e}")


if __name__ == "__main__":
    #test_cloudflare_api()
    test1_cloudflare_api()
    #test2_cloudflare_api()