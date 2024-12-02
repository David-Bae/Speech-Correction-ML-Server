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

sentence_type = {
    0: "의문문",
    1: "평서문",
    2: "감탄문",
    3: "청유문"
}

if __name__ == "__main__":    
    with open(PITCH_DATA_FILE_PATH, "r") as f:
        pitch_data = json.load(f)    
    
    
    for ref_type in range(4):
        for ref_number in range(10):
            ref_sentence_code = f"{ref_type}_{ref_number}"
            ref_pitch = pitch_data[ref_sentence_code]['pitch']
            ref_time = pitch_data[ref_sentence_code]['time']
            
            scores = [0.0] * 4
            count = [9 if i == ref_type else 10 for i in range(4)]
    
            for user_type in range(4):
                for user_number in range(10):
                    user_sentence_code = f"{user_type}_{user_number}"
                    if ref_sentence_code == user_sentence_code:
                        continue
                    
                    user_pitch = pitch_data[user_sentence_code]['pitch']
                    user_time = pitch_data[user_sentence_code]['time']
    
                    aligned_time, aligned_ref_pitch, aligned_user_pitch = align_pitch_contours(ref_time, ref_pitch, user_time, user_pitch)
                    pitch_difference, ref_trend, user_trend = compare_pitch_contours(aligned_time, aligned_ref_pitch, aligned_user_pitch)
                    diff_rate = abs((ref_trend - user_trend) / (ref_trend + 1e-6) * 100)
                    scores[user_type] += diff_rate

            scores = [score / count[i] for i, score in enumerate(scores)]
            predicted_type = np.argmin(scores)
            print(f"{ref_sentence_code} - {sentence_type[predicted_type]}")