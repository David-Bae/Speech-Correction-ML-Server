import matplotlib.pyplot as plt
from matplotlib import rc

INTONATION_GRAPH_IMAGES_DIRECTORY = "/workspace/app/feedback/intonation/intonation_graph_images"


plot_config = {
    'color': 'orange', #* Pitch 곡선 색상
}

def plot_intonation_graph(time_resampled, pitch_resampled, sentence_number):
    plt.clf()
    
    # # 축 눈금 제거
    plt.xticks([])
    plt.yticks([])
    
    plt.plot(time_resampled, pitch_resampled, linewidth=5, color=plot_config['color'])    
    
    save_file_path = f"{INTONATION_GRAPH_IMAGES_DIRECTORY}/{sentence_number}.png"
    plt.savefig(save_file_path, bbox_inches='tight', pad_inches=0)