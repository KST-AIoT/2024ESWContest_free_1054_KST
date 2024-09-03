import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from pickle import load
import torch

DataLength = 27
NoOfFeature = 2

def load_model(path, config):
    model = CNN(config)
    state_dict = torch.load(path, map_location=torch.device('cpu'), weights_only=True)  # GPU에서 학습한 모델을 CPU에서 로드
    model.load_state_dict(state_dict)
    model.eval()  
    return model

def predict_dt(filename):
    TestData = np.zeros([1, DataLength, NoOfFeature]) 
    input_data = pd.read_csv(fiilename)

    TestData[0, :, 0] = input_data['magnitude'][:DataLength]
    TestData[0, :, 1] = input_data["phase"][:DataLength]

    config = {
        'learning_rate': 0.0008,
        'epochs': 1000,
    }

    loaded_model = load_model('./cnn_model.pth', config)

    scaler_X = load(open('../minmax_scaler_x.pkl', 'rb'))
    input_data_scaled = scaler_X.transform(TestData.reshape(-1, NoOfFeature)).reshape(1, DataLength, NoOfFeature)

    input_tensor = torch.tensor(input_data_scaled, dtype=torch.float32)

    with torch.no_grad():
        output = loaded_model(input_tensor)
        predicted_label = torch.argmax(output, 1).item()  # 라벨은 1부터 8까지

    print(f'Predicted Label: {predicted_label}')
    return predicted_label

if __name__ == "__main__":
    predict_dt()