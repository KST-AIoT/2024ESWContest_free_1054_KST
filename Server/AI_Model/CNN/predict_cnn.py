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

label_conditions = {
    0: {"N": 400, "K": 200, "P": 50},
    1: {"N": 400, "K": 200, "P": 100},
    2: {"N": 800, "K": 200, "P": 50},
    3: {"N": 800, "K": 200, "P": 100},
    4: {"N": 400, "K": 400, "P": 50},
    5: {"N": 400, "K": 400, "P": 100},
    6: {"N": 800, "K": 400, "P": 50},
    7: {"N": 800, "K": 400, "P": 100}
}

# 라벨에 따라 조건을 반환하는 함수
def label_to_conditions(label):
    '''
    주어진 라벨을 기반으로 label_conditions에 해당하는 조건을 반환하는 함수.

    :param label: 딥러닝 모델이 출력한 정수형 라벨 (0~7)
    :return: 해당 라벨에 대응하는 K, N, P 조건이 담긴 딕셔너리
    '''
    if label in label_conditions:
        return label_conditions[label]
    else:
        raise ValueError(f"Invalid label: {label}. Expected a label between 0 and 7.")

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
        predicted_label_index = torch.argmax(output, 1).item()
        predicted_label = label_to_conditions(predicted_label_index)
    print(f'Predicted Label: {predicted_label}')
    return predicted_label

if __name__ == "__main__":
    predict_dt()
