import pandas as pd

file_path = "app/feedback/feedback_text/mo_new.csv"

df = pd.read_csv(file_path)

# 첫 번째 열의 이름을 가져옵니다.
first_column_name = df.columns[0]

vowels = {
    "ㅣ": 0, "ㅔ": 0, "ㅐ": 0, "ㅏ": 0,
    "ㅓ": 0, "ㅗ": 0, "ㅜ": 0, "ㅡ": 0,
    "ㅑ": 0, "ㅕ": 0, "ㅛ": 0, "ㅠ": 0,
    "ㅒ": 0, "ㅖ": 0, "ㅘ": 0, "ㅝ": 0,
    "ㅙ": 0, "ㅞ": 0, "ㅚ": 0, "ㅟ": 0,
    "ㅢ": 0
}

# 첫 번째 열의 모든 값을 순회하며 출력합니다.
for value in df[first_column_name]:
    user, standard = value.split("_")
    vowels[user] += 1
    
print(vowels)

