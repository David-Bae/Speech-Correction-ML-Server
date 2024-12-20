from difflib import SequenceMatcher
import pandas as pd

import logging
logger = logging.getLogger(__name__)


def parse_ipa(ipa_input):
    ipas = pd.read_csv("/workspace/app/feedback/table/ipa2ko.csv")["IPA"].values

    ipas = sorted(ipas, key=lambda c: len(c), reverse=True)

    parsed_ipa = []
    i = 0

    while i < len(ipa_input):
        skip = True
        for ipa in ipas:
            if ipa == ipa_input[i:i+len(ipa)]:
                skip = False
                parsed_ipa.append(ipa)
                i += len(ipa)
                break
        if skip == True:
            i += 1

    return parsed_ipa


def parse_ipa_with_words(ipa_sentence):
    words = ipa_sentence.split(" ")
    
    parsed_words = list(map(parse_ipa, words))
    
    return parsed_words


def compare_ipa_with_word_index(original_ipa, user_ipa):
    parsed_original = parse_ipa_with_words(original_ipa)
    parsed_user = parse_ipa_with_words(user_ipa)
    
    diff_with_word_index = []
    
    # 두 개의 단어 리스트를 단어 단위로 비교
    for word_index, (orig_word, user_word) in enumerate(zip(parsed_original, parsed_user)):
        # SequenceMatcher로 단어 단위의 음소 비교
        matcher = SequenceMatcher(None, orig_word, user_word)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':                
                diff_with_word_index.append((word_index, tag, orig_word[i1:i2], user_word[j1:j2]))
    
    return diff_with_word_index


from app.hangul2ipa.worker import *

def compare_jamo_with_word_index(original_hangul, user_hangul):
    parsed_original = hangul2jamo_with_pronunciation_rules(original_hangul)
    parsed_user = hangul2jamo_with_pronunciation_rules(user_hangul)
    
    diff_with_word_index = []
    
    # 두 개의 단어 리스트를 단어 단위로 비교
    for word_index, (orig_word, user_word) in enumerate(zip(parsed_original, parsed_user)):
        # SequenceMatcher로 단어 단위의 음소 비교
        matcher = SequenceMatcher(None, orig_word, user_word)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            #! 자주 틀리는 부분: Debug 필요!
            # print(tag, i1, i2, j1, j2)
            
            if tag != 'equal':
                diff_with_word_index.append((word_index, tag, orig_word[i1:i2], user_word[j1:j2]))

    return (parsed_original, parsed_user, diff_with_word_index)



def compare_jamo_respectively_with_word_index(original_hangul, user_hangul):
    parsed_original = hangul2jamo_with_pronunciation_rules(original_hangul)
    parsed_user = hangul2jamo_with_pronunciation_rules(user_hangul)
    
    diff_with_word_index = []
    
    mo = [
        'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 
        'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
    ]

    def is_mo(jamo):
        """주어진 자모가 모음인지 확인하는 함수"""
        return jamo in mo
    
    
    def split_jamo(jamo_list):
        ja = []
        mo = []
        for jamo in jamo_list:
            if is_mo(jamo):  # 자음인지 확인하는 함수
                mo.append(jamo)
            else:
                ja.append(jamo)
        return ja, mo
    
    for word_index, (orig_word, user_word) in enumerate(zip(parsed_original, parsed_user)):
        orig_ja, orig_mo = split_jamo(orig_word)
        user_ja, user_mo = split_jamo(user_word)
        
        # 자음 비교
        matcher = SequenceMatcher(None, orig_ja, user_ja)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                diff_with_word_index.append((word_index, 'ja', tag, orig_ja[i1:i2], user_ja[j1:j2]))
        
        # 모음 비교
        matcher = SequenceMatcher(None, orig_mo, user_mo)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                diff_with_word_index.append((word_index, 'mo', tag, orig_mo[i1:i2], user_mo[j1:j2]))

    return (parsed_original, parsed_user, diff_with_word_index)