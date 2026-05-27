import joblib
import pandas as pd

model = joblib.load('local_cop_model.pkl')

new_log = {
    'url_length': [90],
    'special_chars': [1],
    'has_sql_keyword': [1]
}
new_df = pd.DataFrame(new_log)

probabilities = model.predict_proba(new_df)[0]
attack_prob = probabilities[1]

print(f"공격일 확률: {attack_prob:.2f}")

if attack_prob >= 0.8:
    print("잠재적 공격으로 감지되었습니다.")
elif attack_prob >= 0.4:
    print("의심스러운 활동으로 감지되었습니다.")
else:
    print("정상적인 활동으로 감지되었습니다.")