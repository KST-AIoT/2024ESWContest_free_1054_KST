import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

class Dataset:
    def __init__(self):
        #데이터 로드 및 전처리
        train_data, test_data = self._load_data()

        self.X_train, self.y_train = self._data_preprocessing(train_data)
        self.X_test, self.y_test = self._data_preprocessing(test_data)
        self.X_inference = self.X_test 
    def _load_data(self):
        #데이터 로드
        data = pd.read_csv('data/dataset.csv')
        
        # 입력 데이터 (X)와 출력 라벨 (y)로 분리
        X = data[['frequency', 'phase', 'magnitude', 'temperature']]
        y = data[['K_percent', 'N_percent', 'P_percent']]
        # 데이터셋 분할 (80% 훈련, 20% 테스트)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        return (X_train, y_train), (X_test, y_test)
    
    def _data_preprocessing(self, data):
        # 스케일링
        X, y = data
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        y_scaled = scaler.fit_transform(y)  # 필요에 따라 라벨도 스케일링

        return X_scaled, y_scaled

        
