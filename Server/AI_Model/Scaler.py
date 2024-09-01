import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

class Scaler:
    def __init__(self):
        # 데이터 로드 및 전처리
        self.X, self.y = self._load_data()
        self.scaler_X = self._scaler_x()  # 입력 데이터 스케일러 생성
        self.scaler_y = self._scaler_y()  # 출력 데이터 스케일러 생성

    def _load_data(self):
        # 데이터 로드
        data = pd.read_csv('AI_Model/data/dataset1.csv')
        # 데이터 변환: 4개의 행이 하나의 라벨에 해당하도록 변환
        X, y = self._transform_data(data)
        return X, y

    def _transform_data(self, data):
        X = []
        y = []

        for i in range(0, len(data), 4):  # 4개의 행마다 그룹화
            sample_features = data.iloc[i:i+4][['frequency', 'phase', 'magnitude', 'temperature']].values.flatten()
            X.append(sample_features)

            # 첫 번째 행의 라벨을 사용 (모든 행의 라벨이 동일하다고 가정)
            label = data.iloc[i]['K_percent'], data.iloc[i]['N_percent'], data.iloc[i]['P_percent']
            y.append(label)

        return np.array(X), np.array(y)

    def _scaler_x(self):
        # 입력 데이터 스케일링
        scaler_X = MinMaxScaler()
        scaler_X.fit(self.X)
        return scaler_X

    def _scaler_y(self):
        # 출력 라벨 스케일링
        scaler_y = MinMaxScaler()
        scaler_y.fit(self.y)
        return scaler_y

    def transform_input(self, input_data):
        # 입력 데이터를 스케일링
        input_df = pd.DataFrame([input_data.flatten()], columns=[f'feature_{i+1}' for i in range(input_data.size)])
        return self.scaler_X.transform(input_df)

    def inverse_transform_output(self, output_data):
        # 출력 데이터를 원래 값으로 변환
        return self.scaler_y.inverse_transform(output_data)
