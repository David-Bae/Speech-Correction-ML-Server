import parselmouth
import numpy as np
from scipy.interpolate import interp1d
from io import BytesIO
from pydub import AudioSegment
from scipy.interpolate import make_interp_spline


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#! BytesIO to Sound (1)
def bytesio_to_sound(audio_data: BytesIO):
    """
    BytesIO 객체를 parselmouth의 Sound 객체로 변환하는 함수
    """
    audio_segment = AudioSegment.from_file(audio_data)
    raw_data = audio_segment.raw_data
    samples = np.frombuffer(raw_data, dtype=np.int16)
    sound = parselmouth.Sound(samples, audio_segment.frame_rate)
    return sound


#! Pitch 추출 (2)
#* 음성 데이터에서 time_stamps와 pitch_values를 추출하는 함수.
def extract_pitch(audio_data, time_step=0.01, pitch_floor=75, pitch_ceiling=600):
    sound = parselmouth.Sound(audio_data)
    pitch = sound.to_pitch(time_step=time_step, pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    pitch_values = pitch.selected_array['frequency']
    time_stamps = pitch.xs()
    #! 무음(0) 처리
    pitch_values[pitch_values == 0] = np.nan
    return time_stamps, pitch_values


#! Pitch Interpolation (3)
#* pitch_values에서 결측값(NaN)을 선형 보간법을 사용하여 채우는 함수
def interpolate_pitch(pitch_values):
    nans, x = np.isnan(pitch_values), lambda z: z.nonzero()[0]
    pitch_values[nans] = np.interp(x(nans), x(~nans), pitch_values[~nans])
    return pitch_values


#! Pitch Normalization (4)
#* pitch_values를 평균(0)과 표준편차(1)로 정규화하는 함수
def normalize_pitch(pitch_values):
    mean = np.mean(pitch_values)
    std = np.std(pitch_values)
    normalized_pitch = (pitch_values - mean) / std
    return normalized_pitch


#! Pitch Resampling (5)
#* 시간과 음정 데이터를 원하는 개수의 샘플로 재샘플링(선형보간)하는 함수
def resample_pitch(time_stamps, pitch_values, num_samples=100):
    f = interp1d(time_stamps, pitch_values, kind='linear')
    new_time = np.linspace(time_stamps[0], time_stamps[-1], num_samples)
    new_pitch = f(new_time)
    return new_time, new_pitch

#! Pitch Smoothing (6) - 그래프를 부드럽게 만들기 위해 사용
#* B-spline interpolation)을 사용하여 time_stamps과
#* pitch_values의 그래프를 부드럽게 만드는 함수
def smooth_pitch(time_stamps, pitch_values, num_samples=500):
    x_new = np.linspace(time_stamps.min(), time_stamps.max(), num_samples)  # 더 많은 점 생성
    spl = make_interp_spline(time_stamps, pitch_values, k=3)  # B-spline
    pitch_smooth = spl(x_new)

    return x_new, pitch_smooth


#! <가장 중요한 함수>
def get_time_and_pitch(audio_data: BytesIO, num_samples=500):
    sound = bytesio_to_sound(audio_data)
    time, pitch = extract_pitch(sound)
    pitch = interpolate_pitch(pitch)
    pitch_norm = normalize_pitch(pitch)
    time_resampled, pitch_resampled = resample_pitch(time, pitch_norm)
    time_resampled, pitch_resampled = smooth_pitch(time_resampled, pitch_resampled, num_samples)

    return (time_resampled, pitch_resampled)






"""
Feedback 생성 함수
"""
from fastdtw import fastdtw

def align_pitch_contours(ref_time, ref_pitch, user_time, user_pitch):
    #* 1. 동일한 샘플 수로 보간 (Interpolation)
    num_samples = 100  # 재샘플링할 샘플 수 설정
    ref_interp = interp1d(ref_time, ref_pitch, kind='linear')
    user_interp = interp1d(user_time, user_pitch, kind='linear')
    common_time = np.linspace(0, 1, num_samples)
    ref_pitch_resampled = ref_interp(np.linspace(ref_time[0], ref_time[-1], num_samples))
    user_pitch_resampled = user_interp(np.linspace(user_time[0], user_time[-1], num_samples))

    #* 2. fastdtw를 이용한 정렬
    # distance는 무시
    distance, path = fastdtw(ref_pitch_resampled, user_pitch_resampled, dist=lambda x, y: abs(x - y))

    #* fastdtw 경로를 따라 정렬된 피치 값 추출
    ref_indices, user_indices = zip(*path)
    
    aligned_ref_pitch = ref_pitch_resampled[list(ref_indices)]
    aligned_user_pitch = user_pitch_resampled[list(user_indices)]

    #* 정렬된 시간 축 생성
    aligned_time = common_time[list(ref_indices)]  # 또는 list(user_indices) 사용 가능

    return aligned_time, aligned_ref_pitch, aligned_user_pitch


def compare_pitch_contours(aligned_time, aligned_ref_pitch, aligned_user_pitch):
    # 피치 차이 계산
    pitch_difference = aligned_user_pitch - aligned_ref_pitch

    # 끝부분에서의 피치 변화 추세 계산
    end_section = int(len(aligned_time) * 0.7)
    ref_trend = np.mean(np.diff(aligned_ref_pitch[end_section:]))
    user_trend = np.mean(np.diff(aligned_user_pitch[end_section:]))

    return pitch_difference, ref_trend, user_trend

def generate_feedback(pitch_difference, ref_trend, user_trend):
    feedback = ""
    threshold = 0.5  # 허용 가능한 편차의 임계값

    # 전체 피치 편차 확인
    if np.max(np.abs(pitch_difference)) > threshold:
        feedback += "전체적인 피치 곡선이 레퍼런스와 상당히 다릅니다.\n"

    # 발화 끝부분의 억양 확인
    if ref_trend > 0 and user_trend <= 0:
        feedback += "의문문의 억양을 위해 발화 끝부분에서 피치를 올려야 합니다.\n"
    elif ref_trend < 0 and user_trend >= 0:
        feedback += "평서문의 억양을 위해 발화 끝부분에서 피치를 내려야 합니다.\n"
    else:
        feedback += "억양이 레퍼런스와 잘 일치합니다.\n"

    return feedback


import json
import os

PITCH_DATA_FILE_PATH = "/workspace/app/feedback/intonation/pitch_data.json"
AUDIO_FILE_PATH = "/workspace/app/feedback/intonation/audio/"

def save_pitch_data_to_json(sentence_key, time_resampled, pitch_resampled):
    # JSON 파일 읽기
    try:
        with open(PITCH_DATA_FILE_PATH, 'r') as file:
            data = json.load(file)
    except Exception as e:
        # 파일이 없으면 새로 생성
        data = {}
    
    # 새로운 문장 데이터 추가
    data[sentence_key] = {
        "time": time_resampled.tolist(),
        "pitch": pitch_resampled.tolist()
    }
    
    # 수정된 데이터를 파일에 저장
    with open(PITCH_DATA_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Added data for '{sentence_key}' to {PITCH_DATA_FILE_PATH}")


def load_pitch_data_from_file(sentence_key):
    try:
        with open(PITCH_DATA_FILE_PATH, "r") as file:
            data = json.load(file)
    except Exception as e:
        return None
    
    time = np.array(data[sentence_key]["time"])
    pitch = np.array(data[sentence_key]["pitch"])
    
    return (time, pitch)

SENTENCE_CODE_LIST = ["0_0", "0_1", "0_2", "1_0", "1_1", "1_2"]


if __name__ == "__main__":
    for sentence_code in SENTENCE_CODE_LIST:

        audio_file_path = os.path.join(AUDIO_FILE_PATH, f"{sentence_code}.wav")

        with open(audio_file_path, "rb") as f:
            audio_file = BytesIO(f.read())
        
        #! Pitch 데이터 추출
        time_user, pitch_user = get_time_and_pitch(audio_file)
        
        save_pitch_data_to_json(sentence_code, time_user, pitch_user)
    
    
    
    # time_ref, pitch_ref = load_pitch_data_from_file(ref_sentence_code)
    
    # #! 피치 곡선 정렬
    # aligned_time, aligned_ref_pitch, aligned_user_pitch = align_pitch_contours(time_ref, pitch_ref, time_user, pitch_user)
    
    # #! 피치 곡선 비교
    # pitch_difference, ref_trend, user_trend = compare_pitch_contours(
    #     aligned_time, aligned_ref_pitch, aligned_user_pitch
    # )

    # #! 피드백 생성
    # feedback = generate_feedback(pitch_difference, ref_trend, user_trend)

    # print(feedback)


        
    
