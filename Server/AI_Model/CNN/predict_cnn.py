import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from pickle import load
import torch
import random
import string
import CNN

DataLength = 27                                 # 각 데이터의 길이(총 27개의 주파수 데이터 측정)
NoOfFeature = 2                                 # 각 데이터의 특징(magnitude, phase)

'''
주어진 파일 데이터를 이용해 예측 수행
'''
def predict_dt(model, filename):
    # 테스트 데이터를 저장할 배열 초기화
    TestData = np.zeros([1, DataLength, NoOfFeature]) 
    input_data = pd.read_csv(filename)

    TestData[0, :, 0] = input_data['magnitude'][:DataLength]
    TestData[0, :, 1] = input_data["phase"][:DataLength]


    # 스케일러를 로드하고 데이터 스케일링
    scaler_X = load(open('../scaler/minmax_scaler_x.pkl', 'rb'))
    input_data_scaled = scaler_X.transform(TestData.reshape(-1, NoOfFeature)).reshape(1, DataLength, NoOfFeature)

    # 스케일링된 데이터를 텐서로 변환
    input_tensor = torch.tensor(input_data_scaled, dtype=torch.float32)


    with torch.no_grad():
        output = model(input_tensor)
        predicted_label = torch.argmax(output, 1).item()

    print(f'Predicted Label: {predicted_label}')
    return predicted_label

if __name__ == "__main__":
    predict_dt()
