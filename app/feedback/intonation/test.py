from pitch import *

import json
import os
import matplotlib.pyplot as plt

PITCH_DATA_FILE_PATH = "/workspace/app/feedback/intonation/pitch_data.json"
AUDIO_FILE_PATH = "/workspace/app/feedback/intonation/audio/"
TMP_PLOT_FOLDER = "/workspace/app/feedback/intonation/tmp"

def plot_pitch(time_stamps, pitch_values, file_name):
    plt.clf()
    plt.figure(figsize=(10, 4))
    plt.plot(time_stamps, pitch_values, label='Pitch')
    plt.xlabel('Time (s)')
    plt.ylabel('Pitch (Hz)')
    plt.title('Pitch over Time')
    plt.legend()
    plt.grid(True)
    
    save_file_path = os.path.join(TMP_PLOT_FOLDER, f"{file_name}.png")
    plt.savefig(save_file_path)


if __name__ == "__main__":    
    with open(PITCH_DATA_FILE_PATH, "r") as f:
        pitch_data = json.load(f)

    # audio_file_path = os.path.join(AUDIO_FILE_PATH, f"{user_sentence_code}.wav")

    # with open(audio_file_path, "rb") as f:
    #     audio_data = BytesIO(f.read())
    
    # sound = bytesio_to_sound(audio_data)
    
    
    ref_sentence_code = "1_0"
    ref_pitch = pitch_data[ref_sentence_code]['pitch']
    ref_time = pitch_data[ref_sentence_code]['time']
    
    print(f"ref_sentence_code: {ref_sentence_code}")
    
    for sentence_code in SENTENCE_CODE_LIST:
        pitch = pitch_data[sentence_code]['pitch']
        time = pitch_data[sentence_code]['time']
    
        aligned_time, aligned_ref_pitch, aligned_user_pitch = align_pitch_contours(ref_time, ref_pitch, time, pitch)
        
        pitch_difference, ref_trend, user_trend = compare_pitch_contours(aligned_time, aligned_ref_pitch, aligned_user_pitch)
        
        sentence_type, sentence_number = sentence_code.split("_")
        if sentence_type == "0":
            print(f"의문문: {sentence_number}번")
        elif sentence_type == "1":
            print(f"평서문: {sentence_number}번")
        
        diff_rate = abs((ref_trend - user_trend) / ref_trend * 100)
        print(f"diff_rate: {diff_rate:.2f}%")
        print()
