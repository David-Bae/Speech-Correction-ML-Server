import subprocess
import random
from tempfile import TemporaryDirectory
import os

def generate_intonation_feedback_image(audio_data, file_name):
    serial_number = ''.join(random.choices('0123456789', k=8))

    with TemporaryDirectory() as temp_corpus_dir:
        audio_file_path = os.path.join(temp_corpus_dir, f"{file_name}.wav")
        with open(audio_file_path, "wb") as audio_file:
            audio_file.write(audio_data.getvalue())

        from_text_file_path = f"/workspace/app/feedback/intonation_sentences/{file_name}.txt"
        to_text_file_path = f"/workspace/test/{file_name}.txt"
        
        with open(from_text_file_path, 'r') as from_file:
            with open(to_text_file_path, 'w') as to_file:
                to_file.write(from_file.read())

        

        

def align_mfa(corpus_directory, dictionary_path, acoustic_model_path, output_directory):
    command = [
        'mfa', 'align',
        corpus_directory,
        dictionary_path,
        acoustic_model_path,
        output_directory
    ]
    
    try:
        subprocess.run(command, check=True)
        print("Alignment completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")