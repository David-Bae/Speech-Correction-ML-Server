import openai
import pandas as pd

client = openai.OpenAI()


INSTRUCTIONS = pd.read_csv("app/feedback/feedback_text/mo_legacy.csv")

def get_role_and_prompt_for_feedback_generation(user, standard, model):    
    user_instruction = INSTRUCTIONS[INSTRUCTIONS['Mo'] == user]['Instruction'].values[0]
    standard_instruction = INSTRUCTIONS[INSTRUCTIONS['Mo'] == standard]['Instruction'].values[0]
    
    if model == "gpt-4o":
        role = (
            "당신은 청각장애인을 대상으로 하는 한국어 발음 교정 전문가입니다. "
            "항상 친절하고, 상대방이 이해하기 쉽게 명확하고 간결하게(짧게) 설명해 주세요."
        )

        prompt = (
            f"사용자가 '{standard}'를 '{user}'라고 발음한 경우에 대한 피드백 문장을 이해하기 쉽고 간결하게 만들어주세요.\n"
            "반드시 다음 사항을 준수해주세요.\n"
            f"1. {standard}와 {user}의 발음 방법을 비교해서 차이점을 기반으로 피드백 문장을 만들어주세요. "
            f"만약 두 모음의 발음 방법을 비교할 수 없다면, {standard}의 발음 방법을 기반으로 피드백 문장을 만들어주세요.\n"
            "2. 피드백 문장은 짧고 간결하게 만들어주세요.\n"
            f"3. 사용자는 전연령입니다. 어린아이일 수도 있고, 노인일 수도 있습니다. 따라서 피드백 문장은 모든 연령대에 이해하기 쉽고 친근하게 만들어주세요.\n"
            "모음 발음 방법:\n"
            f"'{user}' 발음 방법: {user_instruction}\n"
            f"'{standard}' 발음 방법: {standard_instruction}\n"
        )
    else:
        role = None
        prompt = (
            "당신은 청각장애인을 대상으로 하는 한국어 발음 교정 전문가입니다. "
            "항상 친절하고, 상대방이 이해하기 쉽게 명확하고 간결하게(짧게) 설명해 주세요.\n"
            f"사용자가 '{standard}'를 '{user}'라고 발음한 경우에 대한 피드백 문장을 이해하기 쉽고 간결하게 만들어주세요.\n"
            "반드시 다음 사항을 준수해주세요.\n"
            f"1. {standard}와 {user}의 발음 방법을 비교해서 차이점을 기반으로 피드백 문장을 만들어주세요. "
            f"만약 두 모음의 발음 방법을 비교할 수 없다면, {standard}의 발음 방법을 기반으로 피드백 문장을 만들어주세요.\n"
            "2. 피드백 문장은 짧고 간결하게 만들어주세요.\n"
            f"3. 사용자는 전연령입니다. 어린아이일 수도 있고, 노인일 수도 있습니다. 따라서 피드백 문장은 모든 연령대에 이해하기 쉽고 친근하게 만들어주세요.\n"
            "모음 발음 방법:\n"
            f"'{user}' 발음 방법: {user_instruction}\n"
            f"'{standard}' 발음 방법: {standard_instruction}\n"
            "피드백 문장 예시: 지금보다 입을 조금 더 벌리고 혀를 약간 낮춰 다시 발음해 보세요!"
        )
    
    return role, prompt

def get_feedback_gpt_4o(user, standard):
    role, prompt = get_role_and_prompt_for_feedback_generation(user=user, standard=standard)
    
    completion = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[
            {"role": "system", "content": role},
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content

def get_feedback_gpt_o1_mini(user, standard):
    _, prompt = get_role_and_prompt_for_feedback_generation(user=user, standard=standard, model="o1-mini")
    
    completion = client.chat.completions.create(
        model="o1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content





FEEDBACK_TEXT_FILE_PATH = "app/feedback/feedback_text/mo_new.csv"

vowels = [
    "ㅣ", "ㅔ", "ㅐ", "ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅑ", "ㅕ", "ㅛ", "ㅠ", "ㅒ", "ㅖ", "ㅘ", "ㅝ", "ㅙ", "ㅞ", "ㅚ", "ㅟ", "ㅢ"
]

if __name__ == "__main__":
    import csv
    
    count = 1

    with open(FEEDBACK_TEXT_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["combination", "feedback_text"])
        
        for user in vowels:
            for standard in vowels:
                if user != standard:
                    combination = f"{user}_{standard}"
                    feedback_text = get_feedback_gpt_o1_mini(user=user, standard=standard)
                    writer.writerow([combination, feedback_text])
                    
                    print(f"{count}/{len(vowels) * (len(vowels)-1)}: {combination} done!")
                    count += 1
                
                
                