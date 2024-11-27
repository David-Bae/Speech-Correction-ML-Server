import parselmouth
import numpy as np
from scipy.interpolate import interp1d
from io import BytesIO
from pydub import AudioSegment
from scipy.interpolate import make_interp_spline


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! Pitch 추출
def extract_pitch(audio_data, time_step=0.01, pitch_floor=75, pitch_ceiling=600):
    sound = parselmouth.Sound(audio_data)
    pitch = sound.to_pitch(time_step=time_step, pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    pitch_values = pitch.selected_array['frequency']
    time_stamps = pitch.xs()
    pitch_values[pitch_values == 0] = np.nan
    return time_stamps, pitch_values

#! Pitch Interpolation
def interpolate_pitch(pitch_values):
    nans, x = np.isnan(pitch_values), lambda z: z.nonzero()[0]
    pitch_values[nans] = np.interp(x(nans), x(~nans), pitch_values[~nans])
    return pitch_values

#! Pitch Normalization
def normalize_pitch(pitch_values):
    mean = np.mean(pitch_values)
    std = np.std(pitch_values)
    normalized_pitch = (pitch_values - mean) / std
    return normalized_pitch

#! Pitch Resampling
def resample_pitch(time_stamps, pitch_values, num_samples=100):
    f = interp1d(time_stamps, pitch_values, kind='linear')
    new_time = np.linspace(time_stamps[0], time_stamps[-1], num_samples)
    new_pitch = f(new_time)
    return new_time, new_pitch

#! Feedback Generation
def generate_feedback(distance, threshold=30):
    if distance < threshold:
        return "The intonation is correct!"
    else:
        return "Improve the intonation in some sections."

#! BytesIO to Sound
def bytesio_to_sound(audio_data: BytesIO):
    """
    BytesIO 객체를 parselmouth의 Sound 객체로 변환하는 함수
    """
    audio_segment = AudioSegment.from_file(audio_data)
    raw_data = audio_segment.raw_data
    samples = np.frombuffer(raw_data, dtype=np.int16)
    sound = parselmouth.Sound(samples, audio_segment.frame_rate)
    return sound


#! Pitch Smoothing
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