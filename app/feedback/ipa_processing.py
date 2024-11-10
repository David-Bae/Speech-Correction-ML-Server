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
                # word_index로 몇 번째 단어에서 차이가 발생했는지 표시
                # logger.info(orig_word)
                # logger.info(user_word)
                
                diff_with_word_index.append((word_index, orig_word[i1:i2][0], user_word[j1:j2][0]))
    
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
            if tag != 'equal':                
                diff_with_word_index.append((word_index, tag, orig_word[i1:i2], user_word[j1:j2]))
    
    return diff_with_word_index