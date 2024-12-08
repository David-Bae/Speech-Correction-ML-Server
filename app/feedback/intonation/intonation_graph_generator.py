import matplotlib.pyplot as plt
from io import BytesIO

INTONATION_GRAPH_IMAGES_DIRECTORY = "/workspace/app/feedback/intonation/intonation_graph_images"

plot_config = {
    'color': 'green', #* Pitch 곡선 색상
}

def plot_intonation_graph(time_resampled, pitch_resampled):
    plt.clf()
    
    # # 축 눈금 제거
    plt.xticks([])
    plt.yticks([])
    
    plt.plot(time_resampled, pitch_resampled, linewidth=5, color=plot_config['color'])    
    
    #* 이미지를 메모리에 저장
    buffer = BytesIO()
    plt.savefig(buffer, format='jpg', bbox_inches='tight', pad_inches=0)
    buffer.seek(0)

    return buffer

def save_intonation_graph(time_resampled, pitch_resampled, save_path="/workspace/graph_test/graph.jpg"):
    plt.clf()
    
    # 축 눈금 제거
    plt.xticks([])
    plt.yticks([])
    
    # 그래프 플롯
    plt.plot(time_resampled, pitch_resampled, linewidth=5, color=plot_config['color'])
    
    # 그래프를 이미지로 저장
    plt.savefig(save_path, format='jpg', bbox_inches='tight', pad_inches=0)
    
    print(f"Graph saved to {save_path}")
    return save_path