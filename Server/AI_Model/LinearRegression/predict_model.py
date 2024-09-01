import numpy as np
import joblib
from AI_Model.Scaler import Scaler

def predict_lr(frequency, phase, magnitude, temperature):
    # Scaler 클래스 인스턴스 생성 (데이터 로드 및 스케일러 준비)
    scaler = Scaler()

    # 입력 데이터를 배열로 변환
    input_data = np.array([[frequency, phase, magnitude, temperature]])

    # 모델 로드
    model = joblib.load('AI_Model/LinearRegression/LR_model.joblib')

    # 입력 데이터 스케일링
    print("suc1")
    input_data_scaled = scaler.transform_input(input_data)

    # 예측
    print("suc2")
    y_pred_scaled = model.predict(input_data_scaled)

    # 출력 데이터를 원래 값으로 변환
    print("suc3")
    y_pred = scaler.inverse_transform_output(y_pred_scaled)

    # 예측 결과 반환
    return {
        'K_percent': y_pred[0][0],
        'N_percent': y_pred[0][1],
        'P_percent': y_pred[0][2]
    }

if __name__ == "__main__":
    prediction = predict_lr([100, 200, 300, 400], [30, 40, 50, 60], [1.2, 1.3, 1.4, 1.5], [25, 26, 27, 28])
    print(prediction)
