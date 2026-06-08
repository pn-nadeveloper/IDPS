import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드
CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY")
EMAIL = os.getenv("CLOUDFLARE_EMAIL")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

def test_cloudflare_api():
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}"
    #url = f"https://api.cloudflare.com/client/v4/user"
    headers = {
        "X-Auth-Email"  : EMAIL,
        "X-Auth-Key"    : CLOUDFLARE_API_KEY,
    }
    try:
        response = requests.get(url, headers=headers, timeout=5.0)  # GET 요청으로 사용자 정보 조회 테스트
        if response.status_code == 200:
            print("✅ Cloudflare API 연결 성공!")
            data = response.json()
            print(json.dumps(data, indent=4))  # 응답 데이터 출력
        else:
            print(f"❌ Cloudflare API 연결 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Cloudflare API 호출 중 예외 발생: {e}")

if __name__ == "__main__":
    test_cloudflare_api()