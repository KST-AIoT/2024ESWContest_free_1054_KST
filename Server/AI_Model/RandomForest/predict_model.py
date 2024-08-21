import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import joblib

def predict_rf(frequency, phase, magnitude, temperature):
    # 입력 데이터 수집
    #frequency = float(input("Enter frequency: "))
    #phase = float(input("Enter phase: "))
    #magnitude = float(input("Enter magnitude: "))
    #temperature = float(input("Enter temperature: "))

    # 입력 데이터를 배열로 변환
    input_data = np.array([[frequency, phase, magnitude, temperature]])

    # 모델 로드
    model = joblib.load('AI_Model/RandomForest/rf_model.joblib')

    # 데이터 전처리 - 학습 시 사용한 스케일러로 스케일링
    data = pd.read_csv('../data/dataset.csv')  # 실제 데이터셋 파일 경로 사용
    X = data[['frequency', 'phase', 'magnitude', 'temperature']]
    y = data[['K_percent', 'N_percent', 'P_percent']]

    scaler_X = MinMaxScaler()
    scaler_X.fit(X)
    input_data_scaled = scaler_X.transform(input_data)

    # 예측
    y_pred_scaled = model.predict(input_data_scaled)

    # 출력 데이터를 원래 스케일로 변환
    scaler_y = MinMaxScaler()
    scaler_y.fit(y)
    y_pred = scaler_y.inverse_transform(y_pred_scaled)

    # 예측 결과 출력
    #print(f'Predicted K_percent: {y_pred[0][0]:.2f}%')
    #print(f'Predicted N_percent: {y_pred[0][1]:.2f}%')
    #print(f'Predicted P_percent: {y_pred[0][2]:.2f}%')
    return {
        'K_percent': y_pred[0][0],
        'N_percent': y_pred[0][1],
        'P_percent': y_pred[0][2]
    }
if __name__ == "__main__":
    predict_rf()
