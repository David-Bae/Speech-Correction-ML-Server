# the engine that does the hard lifting.
# convert() is the entry point for converting Korean orthography into transcription

import regex as re
from base64 import b64decode
from typing import Union
from jamo import j2h

from app.hangul2ipa.classes import ConversionTable, Word
import app.hangul2ipa.rules as rules


def transcription_convention(convention: str):
    # supported transcription conventions: ipa, yale, park
    convention = convention.lower()
    if convention not in ['ipa', 'yale', 'park']:
        raise ValueError(f"Your input {convention} is not supported.")
    return ConversionTable(convention)


def sanitize(word: str) -> str:
    """
    converts all hanja 漢字 letters to hangul
    and also remove any space in the middle of the word
    """
    if len(word) < 1:  # if empty input, no sanitize
        return word

    word = word.replace(' ', '')

    hanja_idx = [match.start() for match in re.finditer(r'\p{Han}', word)]
    if len(hanja_idx) == 0:  # if no hanja, no sanitize
        return word


def convert(hangul: str,
            rules_to_apply: str = 'pastcnhovr',
            convention: str = 'ipa',
            sep: str = '') -> str:
    # the main function for IPA conversion

    if len(hangul) < 1:  # if no content, then return no content
        return ""

    # prepare
    rules_to_apply = rules_to_apply.lower()
    CT_convention = transcription_convention(convention)
    #! hangul = sanitize(hangul) # 현재 프로젝트에서는 필요없음.
    word = Word(hangul=hangul)

    # resolve word-final consonant clusters right off the bat
    rules.simplify_coda(word)

    # apply rules
    word = rules.apply_rules(word, rules_to_apply)

    # high mid/back vowel merger after bilabial (only for the Yale convention)
    if CT_convention.name == 'yale' and 'u' in rules_to_apply:
        bilabials = list("ㅂㅃㅍㅁ")
        applied = list(word.jamo)
        for i, jamo in enumerate(word.jamo[:-1]):
            if jamo in bilabials and word.jamo[i+1] == "ㅜ":
                applied[i+1] = "ㅡ"
        word.jamo = ''.join(applied)

    # convert to IPA or Yale
    transcribed = rules.transcribe(word.jamo, CT_convention)

    # apply phonetic rules
    if CT_convention.name == 'ipa':
        transcribed = rules.apply_phonetics(transcribed, rules_to_apply)

    return sep.join(transcribed)


def convert_many(long_content: str,
                 rules_to_apply: str = 'pastcnhovr',
                 convention: str = 'ipa',
                 sep: str = '') -> Union[int, str]:
    # decode uploaded file and create a wordlist to pass to convert()
    decoded = b64decode(long_content).decode('utf-8')
    decoded = decoded.replace('\r\n', '\n').replace('\r', '\n')  # normalize line endings
    decoded = decoded.replace('\n\n', '')  # remove empty line at the file end

    input_internal_sep = '\t' if '\t' in decoded else ','

    if '\n' in decoded:
        # a vertical wordlist uploaded
        input_lines = decoded.split('\n')
        wordlist = [l.split(input_internal_sep)[1].strip() for l in input_lines if len(l) > 0]
    else:
        # a horizontal wordlist uploaded
        wordlist = decoded.split(input_internal_sep)

    # iterate over wordlist and populate res
    res = ['Orthography\tIPA']
    for word in wordlist:
        converted_r = convert(hangul=word,
                              rules_to_apply=rules_to_apply,
                              convention=convention,
                              sep=sep)
        res.append(f'{word.strip()}\t{converted_r.strip()}')

    return '\n'.join(res)

def convert_sentence(sentence: str) -> str:
    words = sentence.split()
    words_ipa = map(convert, words)
    
    sentence_ipa = " ".join(words_ipa)
    
    return sentence_ipa

import logging
logger = logging.getLogger(__name__)

def hangul2ipa(hangul: str) -> str:
    ipa = convert_sentence(hangul)
    return ipa


def apply_to_sentence(func):
    def wrapper(hangul: str, *args, **kwargs):
        # 문장을 단어로 분리
        words = hangul.split()
        
        # 각 단어에 함수 적용
        result = []
        for word in words:
            word_result = func(word, *args, **kwargs)
            result.append(word_result)
            
        return result
    return wrapper

@apply_to_sentence
def hangul2jamo_with_pronunciation_rules(hangul: str,
            rules_to_apply: str = 'pastcnhovr') -> str:
    #* 한글 단어를 자모 리스트로 변환 하는 함수.
    
    if len(hangul) == 0:  # if no content, then return no content
        return ""

    # prepare 
    rules_to_apply = rules_to_apply.lower()
    word = Word(hangul=hangul)

    # resolve word-final consonant clusters right off the bat
    rules.simplify_coda(word)

    # apply rules
    word = rules.apply_rules(word, rules_to_apply)

    jamo_list = list(word.jamo)

    return jamo_list


def jamo_to_syllables(jamo_list):
    # 자음 리스트
    ja = [
        'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
    ]
    # 모음 리스트
    mo = [
        'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
    ]

    # 음절 변환 타입
    class SyllableType:
        JAMO = 0
        JAMOJA = 1


    syllables = ""
    i = 0
    next_to_process = 0

    while i < len(jamo_list):
        #! 자음인 경우 다음 요소로 넘어감
        if jamo_list[i] in ja:            
            i += 1
            continue

        syllable_type = None
        initial_sound = None

         #! 모음 앞에 자음이 없는 경우
        if next_to_process == i:
            initial_sound = 'ㅇ'
        #! 모음 앞에 자음이 있는 경우
        else:
            initial_sound = jamo_list[i-1]

        #! {X 모 X}
        if i + 1 == len(jamo_list):
            syllable_type = SyllableType.JAMO
        else:
            #! {X 모 모}
            if jamo_list[i+1] in mo:
                syllable_type = SyllableType.JAMO
            else:
                #! {X 모 자 X}
                if i + 2 == len(jamo_list):
                    syllable_type = SyllableType.JAMOJA
                #! {X 모 자 자}
                elif jamo_list[i+2] in ja:
                    syllable_type = SyllableType.JAMOJA
                else:
                    #! {X 모 ㅇ 모}
                    if jamo_list[i+1] == 'ㅇ':
                        syllable_type = SyllableType.JAMOJA
                    #! {X 모 자 모}
                    else:
                        syllable_type = SyllableType.JAMO
        
        if syllable_type == SyllableType.JAMO:
            syllables += j2h(initial_sound, jamo_list[i])
            i += 1
            next_to_process = i
        else:
            syllables += j2h(initial_sound, jamo_list[i], jamo_list[i+1])
            i += 2
            next_to_process = i

    return syllables



def apply_pronunciation_rules(standard_hangul: str) -> str:
    """
    한글 문장에 발음법칙을 적용하여 실제 발음되는 형태로 변환하는 함수
    """
    # 한글 문장을 발음 규칙에 맞는 자모 리스트로 변환
    jamo_list = hangul2jamo_with_pronunciation_rules(standard_hangul)

    # 자모 리스트를 음절로 변환
    syllables_list = list(map(jamo_to_syllables, jamo_list))

    # 음절로 리스트를 한글 문장으로 변환
    hangul_with_pronunciation_rules = ' '.join(syllables_list)

    return hangul_with_pronunciation_rules


