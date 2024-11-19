from app.hangul2ipa.worker import *
from app.feedback.ipa_processing import compare_jamo_respectively_with_word_index

original_hangul = "나는 행복하게 끝나는 영화가 좋다."
user_hangul = "나는 행복하게 끝나는 꾱화가 좋다."

diff = compare_jamo_respectively_with_word_index(original_hangul, user_hangul)

print(diff)

