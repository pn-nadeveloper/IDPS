import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

data = {
    'url_length':      [15,  120, 25,  180, 30,  150, 18,  200],
    'special_chars':   [ 1,   12,  2,   15,  1,   18,  0,   22],
    'has_sql_keyword': [ 0,    1,  0,    1,  0,    1,  0,    1],
    'is_attack':       [ 0,    1,  0,    1,  0,    1,  0,    1]  # 정답 (0: 정상, 1: 공격)
}

df = pd.DataFrame(data)

x = df[['url_length', 'special_chars', 'has_sql_keyword']]
y = df['is_attack']

model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(x, y)

joblib.dump(model, 'local_cop_model.pkl')
print("모델이 성공적으로 저장되었습니다.")