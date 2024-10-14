import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from pickle import load
from CNN_regression import CNN_regression
import torch
import random
import string
import os

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

    # 현재 파일의 절대 경로를 기준으로 상대 경로를 처리
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scaler_X_path = os.path.join(current_dir, '../scaler/minmax_scaler_x.pkl')
    scaler_K_path = os.path.join(current_dir, '../scaler/minmax_scaler_K.pkl')
    scaler_N_path = os.path.join(current_dir, '../scaler/minmax_scaler_N.pkl')
    scaler_P_path = os.path.join(current_dir, '../scaler/minmax_scaler_P.pkl')

    # 스케일러를 로드하고 데이터 스케일링(X)
    scaler_X = load(open(scaler_X_path, 'rb'))
    input_data_scaled = scaler_X.transform(TestData.reshape(-1, NoOfFeature)).reshape(1, DataLength, NoOfFeature)
    
    # 스케일링된 데이터를 텐서로 변환
    input_tensor = torch.tensor(input_data_scaled, dtype=torch.float32)


    with torch.no_grad():
        output = model(input_tensor)
        print(output)
        output_numpy = output.numpy()
        # 예측된 K, N, P 각각에 대해 역변환 수행
        scaler_K = load(open(scaler_K_path, 'rb'))
        scaler_N = load(open(scaler_N_path, 'rb'))
        scaler_P = load(open(scaler_P_path, 'rb'))

        # 각각 K, N, P 값 추출
        K_pred = scaler_K.inverse_transform(output_numpy[:, 0].reshape(-1, 1))
        N_pred = scaler_N.inverse_transform(output_numpy[:, 1].reshape(-1, 1))
        P_pred = scaler_P.inverse_transform(output_numpy[:, 2].reshape(-1, 1))
        # 예측된 값들을 다시 결합
        output_rescaled = np.hstack([K_pred, N_pred, P_pred])

        print(f"Rescaled Output: {output_rescaled}")
    return output_rescaled

if __name__ == "__main__":
    # 현재 파일의 절대 경로를 기준으로 상대 경로를 처리
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, './model/cnn_regression_model.pth')  # 학습된 모델 경로
    scaler_path = os.path.join(current_dir, '../scaler/minmax_scaler_x.pkl')  # 스케일러 경로

    # 모델 클래스 정의 (여기서는 CNN_regression 사용)
    model = CNN_regression()
    
    # 학습된 모델 가중치 로드
    model.load_state_dict(torch.load(model_path))
    print(f"Model loaded from {model_path}")

    # 예측할 파일 경로 지정 (테스트 데이터 파일 이름)
    test_filename = os.path.join(current_dir, '../data/inference/dataset1.csv')  # 예시로 test_data.csv

    # 예측 수행
    predicted_output = predict_dt(model, test_filename)

    # 예측 결과 출력
    print(f"Final Predicted Output: {predicted_output}")