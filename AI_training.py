import pandas as pd
import glob
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

print("📦 12개 데이터 파일 병합 중...")

# CSV 파일들이 모여있는 폴더 경로 (본인 경로에 맞게 수정 필요)
file_list = glob.glob('D:\\서버 관련 로그\\access_*_*.csv') 

# 모든 CSV 파일을 읽어서 리스트에 담은 후 하나로 합침
df_list = [pd.read_csv(file) for file in file_list]
full_df = pd.concat(df_list, ignore_index=True)

print(f"Total 데이터 개수: {len(full_df)}행 병합 완료!")

full_df = full_df.dropna(subset=['query_path', 'status_code', 'is_attack'])

full_df = full_df[full_df['is_attack'].isin([0, 1, '0', '1'])]

y = full_df['is_attack'].astype(int)

# ==========================================
# 2. 특징(X)과 라벨(Y) 분리 및 텍스트 벡터화
# ==========================================
print("\n🔤 텍스트 데이터(URL)를 숫자 벡터로 변환 중 (TF-IDF)...")

X_text = full_df['query_path']
y = full_df['is_attack'].astype(int)

vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(3, 5), max_features=5000)
X_vectors = vectorizer.fit_transform(X_text)

# ==========================================
# 3. 학습 데이터와 검증 데이터 분리 (8:2)
# ==========================================
X_train, X_test, y_train, y_test = train_test_split(
    X_vectors, y, test_size=0.2, random_state=42, stratify=y
)

# ==========================================
# 4. 랜덤 포레스트 AI 모델 학습 시작
# ==========================================
print("\n🤖 랜덤 포레스트 모델 학습 시작... (데이터가 많아 시간이 조금 걸릴 수 있음)")

# n_estimators: 나무 개수 (100개가 적당), n_jobs=-1: 컴퓨터 CPU 코어 다 쓰기
model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

print("🎉 모델 학습 완료!")

# ==========================================
# 5. 모델 성능 검증 (정확도 평점 매기기)
# ==========================================
y_pred = model.predict(X_test)

print("\n📊 [학습 결과 리포트]")
print(f"정확도(Accuracy): {accuracy_score(y_test, y_pred):.4f}")
print("\n상세 분류 성능:")
print(classification_report(y_test, y_pred))

# ==========================================
# 6. 완성된 AI 모델 및 벡터라이저 파일로 저장
# ==========================================
print("\n💾 완성된 AI 모델 파일 저장 중...")
joblib.dump(model, 'idps_rf_model.pkl')
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
print("✨ idps_rf_model.pkl 및 tfidf_vectorizer.pkl 저장 완료")
print("\n✅ AI 모델 학습 및 저장 프로세스 완료!")