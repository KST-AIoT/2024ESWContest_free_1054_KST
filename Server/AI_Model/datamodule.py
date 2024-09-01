import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

class Dataset:
    def __init__(self):
        # 데이터 로드 및 전처리
        train_data, test_data = self._load_data()

        self.X_train, self.y_train = self._data_preprocessing(train_data)
        self.X_test, self.y_test = self._data_preprocessing(test_data)
        self.X_inference = self.X_test 

    def _load_data(self):
        # 데이터 로드
        data = pd.read_csv('data/dataset1.csv')
        print(data.head())
        print(data.describe())
        print(data.isnull().sum())

        # 데이터 변환: 4개의 행이 하나의 라벨에 해당하도록 변환
        X, y = self._transform_data(data)

        # 데이터셋 분할 (80% 훈련, 20% 테스트)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        return (X_train, y_train), (X_test, y_test)

    def _transform_data(self, data):
        X = []
        y = []

        for i in range(0, len(data), 4):  # 4개의 행마다 그룹화(예시)
            sample_features = data.iloc[i:i+4][['frequency', 'phase', 'magnitude', 'temperature']].values.flatten()
            X.append(sample_features)

            # 첫 번째 행의 라벨을 사용 (모든 행의 라벨이 동일하다고 가정)
            label = data.iloc[i]['K_percent'], data.iloc[i]['N_percent'], data.iloc[i]['P_percent']
            y.append(label)

        return np.array(X), np.array(y)
    
    def _data_preprocessing(self, data):
        X, y = data

        # 입력 데이터 스케일링
        scaler_X = MinMaxScaler()
        X_scaled = scaler_X.fit_transform(X)

        # 출력 라벨 스케일링
        scaler_y = MinMaxScaler()
        y_scaled = scaler_y.fit_transform(y)

        return X_scaled, y_scaled

# 사용 예시
if __name__ == "__main__":
    dataset = Dataset()
    print("X_train shape:", dataset.X_train.shape)
    print("y_train shape:", dataset.y_train.shape)
    print("X_test shape:", dataset.X_test.shape)
    print("y_test shape:", dataset.y_test.shape)
